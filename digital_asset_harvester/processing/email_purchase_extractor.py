"""Logic for identifying and extracting crypto purchase information from emails."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from digital_asset_harvester.config import HarvesterSettings, get_settings
from digital_asset_harvester.confidence import calculate_confidence
from digital_asset_harvester.llm import get_llm_client
from digital_asset_harvester.llm.ollama_client import LLMError
from digital_asset_harvester.llm.provider import LLMProvider
from digital_asset_harvester.prompts import DEFAULT_PROMPTS, PromptManager
from digital_asset_harvester.processing.extractors import registry
from digital_asset_harvester.processing.constants import (
    CRYPTO_EXCHANGES,
    CRYPTOCURRENCY_TERMS,
    NON_PURCHASE_PATTERNS,
    PURCHASE_KEYWORDS,
)
from digital_asset_harvester.validation import PurchaseRecord, PurchaseValidator
from digital_asset_harvester.telemetry import (
    StructuredLoggerAdapter,
    StructuredLoggerFactory,
    log_event,
)

logger = logging.getLogger(__name__)


@dataclass
class PurchaseInfo:
    total_spent: float
    currency: str
    amount: float
    item_name: str
    vendor: str
    purchase_date: str


@dataclass
class EmailPurchaseExtractor:
    settings: HarvesterSettings = field(default_factory=get_settings)
    llm_client: LLMProvider = field(default_factory=get_llm_client)
    logger_factory: StructuredLoggerFactory = field(
        default_factory=StructuredLoggerFactory
    )
    validator: PurchaseValidator = field(init=False)
    event_logger: StructuredLoggerAdapter = field(init=False)
    prompts: PromptManager = field(default_factory=lambda: DEFAULT_PROMPTS)
    _metadata_cache: Dict[str, Dict[str, str]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.validator = PurchaseValidator(
            allow_unknown_crypto=self.settings.allow_unknown_cryptos
        )
        self.event_logger = self.logger_factory.build(
            __name__,
            default_fields={
                "component": "email_purchase_extractor",
                "strict_validation": self.settings.strict_validation,
            },
        )

    def _contains_keywords(self, text: str, keywords: Set[str]) -> bool:
        """Check if text contains any of the specified keywords (case-insensitive)."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def _extract_email_metadata(self, email_content: str) -> Dict[str, str]:
        """Extract subject, sender, and body from email content with caching."""
        if email_content in self._metadata_cache:
            return self._metadata_cache[email_content]

        metadata = {"subject": "", "sender": "", "body": ""}
        lines = email_content.split("\n")

        body_started = False
        body_lines = []

        for i, line in enumerate(lines):
            if body_started:
                body_lines.append(line)
                continue

            line_strip = line.strip()
            line_lower = line_strip.lower()

            if line_lower.startswith("subject: "):
                metadata["subject"] = line_strip[9:].strip()
            elif line_lower.startswith("from: "):
                metadata["sender"] = line_strip[6:].strip()
            elif line_lower.startswith("body: "):
                # Support the "Body: " marker from our application's formatting
                body_started = True
                body_lines.append(line_strip[6:].strip())
            elif not line_strip:
                # Blank line separation (RFC 5322).
                # We skip blank lines if more headers seem to follow (supporting non-standard formats).
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if ":" in next_line and next_line.split(":")[0].replace(
                        "-", ""
                    ).isalnum():
                        continue

                # Otherwise, a blank line signals the start of the body if we have some metadata.
                if metadata["subject"] or metadata["sender"]:
                    body_started = True
            elif ":" not in line_strip:
                # Non-header line signals start of body
                if metadata["subject"] or metadata["sender"]:
                    body_started = True
                    body_lines.append(line)

        metadata["body"] = "\n".join(body_lines).strip()
        self._metadata_cache[email_content] = metadata
        return metadata

    def _is_likely_crypto_related(self, email_content: str) -> bool:
        """Quick keyword-based check to see if email might be crypto-related."""
        metadata = self._extract_email_metadata(email_content)
        full_text = f"{metadata['subject']} {metadata['sender']} {metadata['body']}"

        # Check for crypto exchanges in sender or content
        has_crypto_exchange = self._contains_keywords(
            metadata["sender"], CRYPTO_EXCHANGES
        )
        has_crypto_terms = self._contains_keywords(full_text, CRYPTOCURRENCY_TERMS)

        return has_crypto_exchange or has_crypto_terms

    def _is_likely_purchase_related(self, email_content: str) -> bool:
        """Check if email contains purchase-related keywords."""
        metadata = self._extract_email_metadata(email_content)
        full_text = f"{metadata['subject']} {metadata['body']}"

        has_purchase_keywords = self._contains_keywords(full_text, PURCHASE_KEYWORDS)
        has_non_purchase_patterns = self._contains_keywords(
            full_text, NON_PURCHASE_PATTERNS
        )

        return has_purchase_keywords and not has_non_purchase_patterns

    def _should_skip_llm_analysis(self, email_content: str) -> bool:
        """Determine if email can be quickly filtered out without LLM analysis."""
        metadata = self._extract_email_metadata(email_content)
        full_text = f"{metadata['subject']} {metadata['sender']} {metadata['body']}"

        # Skip if contains clear non-purchase patterns
        if self._contains_keywords(full_text, NON_PURCHASE_PATTERNS):
            return True

        # Skip if doesn't contain any crypto-related terms
        if not self._is_likely_crypto_related(email_content):
            return True

        return False

    def is_crypto_purchase_email(
        self, email_content: str, max_retries: Optional[int] = None
    ) -> bool:
        retries = (
            max_retries if max_retries is not None else self.settings.llm_max_retries
        )

        if self.settings.enable_preprocessing:
            if self._should_skip_llm_analysis(email_content):
                logger.debug(
                    "Skipping LLM analysis - email filtered out by preprocessing"
                )
                return False

            if not (
                self._is_likely_crypto_related(email_content)
                and self._is_likely_purchase_related(email_content)
            ):
                logger.debug("Email doesn't meet basic crypto + purchase criteria")
                return False

        prompt = self.prompts.render("classification", email_content=email_content)

        try:
            logger.info(
                "Submitting email for classification (up to %d attempts)", retries
            )
            result = self.llm_client.generate_json(prompt, retries=retries)
        except LLMError as exc:
            logger.error(
                "Failed to categorize email after %d attempts: %s", retries, exc
            )
            return False

        payload = result.data
        is_purchase = payload.get("is_crypto_purchase", False)
        confidence = payload.get("confidence", 0.5)
        reasoning = payload.get("reasoning", "No reasoning provided")

        logger.info(
            "Classification result: %s (confidence: %.2f) - %s",
            is_purchase,
            confidence,
            reasoning,
        )

        log_event(
            self.event_logger,
            "classification_completed",
            decision=bool(is_purchase),
            confidence=confidence,
        )

        if not is_purchase:
            return False

        if confidence < self.settings.min_confidence_threshold:
            logger.info(
                "Classification below confidence threshold (%.2f < %.2f)",
                confidence,
                self.settings.min_confidence_threshold,
            )
            return False

        return is_purchase

    def extract_purchase_info(
        self,
        email_content: str,
        max_retries: Optional[int] = None,
        default_timezone: str = "UTC",
    ) -> List[Dict[str, Any]]:
        # 1. Try specialized regex extractors first if enabled
        if self.settings.enable_regex_extractors:
            metadata = self._extract_email_metadata(email_content)
            regex_results = registry.extract(
                metadata["subject"], metadata["sender"], metadata["body"]
            )
            if regex_results:
                logger.info("Successfully extracted purchase info using regex extractor")
                return self._process_extracted_transactions(regex_results, method="regex")

        # 2. Fallback to LLM extraction
        retries = (
            max_retries if max_retries is not None else self.settings.llm_max_retries
        )
        prompt = self.prompts.render(
            "extraction",
            email_content=email_content,
            default_timezone=default_timezone,
        )

        try:
            logger.info(
                "Submitting email for purchase extraction (up to %d attempts)", retries
            )
            result = self.llm_client.generate_json(prompt, retries=retries)
        except LLMError as exc:
            logger.error(
                "Failed to extract purchase info after %d attempts: %s", retries, exc
            )
            return []

        payload = result.data

        if not payload or "transactions" not in payload:
            logger.info("No purchase information found in the email")
            return []

        transactions = payload.get("transactions", [])
        if not isinstance(transactions, list):
            logger.warning("Expected transactions list, but got %s", type(transactions))
            return []

        return self._process_extracted_transactions(transactions)

    def _process_extracted_dates(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Common date processing for extracted transactions."""
        for purchase_data in transactions:
            if purchase_data.get("purchase_date"):
                try:
                    # Parse the date and ensure it's in UTC
                    date_str = str(purchase_data["purchase_date"])
                    # Handle various date formats
                    if "T" in date_str:
                        date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    else:
                        # Try to parse common date formats
                        for fmt in [
                            "%Y-%m-%d %H:%M:%S",
                            "%Y-%m-%d %H:%M:%S %Z",
                            "%Y-%m-%d",
                            "%m/%d/%Y %H:%M:%S",
                            "%m/%d/%Y",
                            "%d %b %Y %H:%M:%S",
                            "%d %b %Y",
                            "%b %d, %Y %H:%M:%S",
                            "%b %d, %Y",
                        ]:
                            try:
                                date = datetime.strptime(date_str, fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            raise ValueError(f"Unable to parse date: {date_str}")

                    if date.tzinfo is None:
                        date = date.replace(tzinfo=timezone.utc)
                    else:
                        date = date.astimezone(timezone.utc)
                    purchase_data["purchase_date"] = date.strftime(
                        "%Y-%m-%d %H:%M:%S %Z"
                    )
                except (ValueError, TypeError) as e:
                    logger.warning("Invalid date format (%s). Using current time.", e)
                    purchase_data["purchase_date"] = datetime.now(timezone.utc).strftime(
                        "%Y-%m-%d %H:%M:%S %Z"
                    )
            else:
                logger.warning("No purchase date found, using current time")
                purchase_data["purchase_date"] = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S %Z"
                )
        return transactions

    def _process_extracted_transactions(self, transactions: List[Dict[str, Any]], method: str = "llm") -> List[Dict[str, Any]]:
        """Common processing for transactions (validation, dates, etc.)."""
        extracted_purchases = []
        for purchase_data in transactions:
            # Set extraction method if not already set
            if "extraction_method" not in purchase_data:
                purchase_data["extraction_method"] = method

            # Validate required fields based on transaction type
            is_deposit_withdrawal_or_reward = (
                "deposit" in purchase_data.get("transaction_type", "").lower()
                or "withdrawal" in purchase_data.get("transaction_type", "").lower()
                or "staking_reward" in purchase_data.get("transaction_type", "").lower()
            )

            if is_deposit_withdrawal_or_reward:
                required_fields = {"amount", "item_name", "vendor"}
            else:
                required_fields = {
                    "total_spent",
                    "currency",
                    "amount",
                    "item_name",
                    "vendor",
                }

            missing_fields = {
                field
                for field in required_fields
                if field not in purchase_data or purchase_data[field] is None
            }

            # Log extraction quality
            confidence = purchase_data.get("confidence", 0.5)
            notes = purchase_data.get("extraction_notes", "")
            logger.info("Extraction confidence: %.2f - %s", confidence, notes)
            log_event(
                self.event_logger,
                "extraction_completed",
                confidence=confidence,
                missing_fields=";".join(sorted(missing_fields))
                if missing_fields
                else "",
            )

            if (
                confidence < self.settings.min_confidence_threshold
                and self.settings.strict_validation
                and purchase_data.get("extraction_method") != "regex"  # Regex usually high confidence
            ):
                logger.warning(
                    "Extraction confidence %.2f below threshold %.2f",
                    confidence,
                    self.settings.min_confidence_threshold,
                )
                continue

            if missing_fields:
                logger.warning(
                    "Missing required field(s): %s", ", ".join(sorted(missing_fields))
                )
                if self.settings.strict_validation:
                    continue

            extracted_purchases.append(purchase_data)

        # Use our existing date processing
        return self._process_extracted_dates(extracted_purchases)

    def _validate_purchase_data(self, purchase_data: Dict[str, Any]) -> bool:
        """Validate extracted purchase data for basic sanity checks."""

        if not purchase_data:
            return False

        if not self.settings.enable_validation:
            return True

        strict = self.settings.strict_validation

        try:
            record = PurchaseRecord.from_raw(purchase_data)
        except ValueError:
            logger.warning("Purchase record failed numeric conversion")
            if self.settings.require_numeric_validation or strict:
                return False
            return True

        issues = self.validator.validate(record)
        for issue in issues:
            logger.warning("Validation issue for %s: %s", issue.field, issue.message)

        if issues and strict:
            return False

        return True

    def process_email(self, email_content: str) -> Dict[str, Any]:
        """Process an email to determine if it contains cryptocurrency purchase information."""
        processing_notes: List[str] = []

        # First check if it's likely a crypto purchase email
        if not self.is_crypto_purchase_email(email_content):
            logger.debug("Email classified as non-crypto-purchase")
            return {
                "has_purchase": False,
                "purchases": [],
                "processing_notes": ["Email not classified as crypto purchase"],
            }

        # If classified as purchase, extract the details
        extracted_purchases = self.extract_purchase_info(email_content)

        if not extracted_purchases:
            logger.warning(
                "Failed to extract purchase information despite positive classification"
            )
            processing_notes.append("Classification positive but extraction failed")
            return {
                "has_purchase": False,
                "purchases": [],
                "processing_notes": processing_notes,
            }

        validated_purchases = []
        for purchase_info in extracted_purchases:
            # Create a PurchaseRecord to pass to calculate_confidence
            try:
                purchase_record = PurchaseRecord.from_raw(purchase_info)

                # Calculate and update the confidence score
                purchase_info["confidence"] = calculate_confidence(purchase_record)

                # Validate the extracted data
                if self._validate_purchase_data(purchase_info):
                    # Normalize types for consistency (especially for regex extractors)
                    if purchase_record.amount is not None:
                        purchase_info["amount"] = float(purchase_record.amount)
                    if purchase_record.total_spent is not None:
                        purchase_info["total_spent"] = float(purchase_record.total_spent)
                    if purchase_record.fee_amount is not None:
                        purchase_info["fee_amount"] = float(purchase_record.fee_amount)

                    purchase_info["transaction_type"] = purchase_record.transaction_type
                    validated_purchases.append(purchase_info)
                else:
                    logger.warning("Extracted purchase data failed validation")
                    processing_notes.append(
                        f"Extracted data for {purchase_info.get('item_name')} failed validation"
                    )
            except Exception as e:
                logger.warning("Error processing extracted purchase: %s", e)
                processing_notes.append(f"Error processing extracted purchase: {e}")

        if not validated_purchases:
            return {
                "has_purchase": False,
                "purchases": [],
                "processing_notes": processing_notes,
            }

        logger.info("Successfully processed crypto purchase email")
        processing_notes.append(
            f"Successfully extracted and validated {len(validated_purchases)} purchase(s)"
        )

        return {
            "has_purchase": True,
            "purchases": validated_purchases,
            "processing_notes": processing_notes,
        }
