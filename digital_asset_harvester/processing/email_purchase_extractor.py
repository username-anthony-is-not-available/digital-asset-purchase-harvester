"""Logic for identifying and extracting crypto purchase information from emails."""

import email
import logging
import time
from decimal import Decimal
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from pydantic import ValidationError

from digital_asset_harvester.config import HarvesterSettings, get_settings
from digital_asset_harvester.confidence import calculate_confidence
from digital_asset_harvester.utils.pii_scrubber import PIIScrubber
from digital_asset_harvester.utils.asset_mapping import mapper as asset_mapper
from digital_asset_harvester.utils.fx_rates import fx_service
from digital_asset_harvester.llm import get_llm_client
from digital_asset_harvester.llm.ollama_client import LLMError
from digital_asset_harvester.llm.provider import LLMProvider
from digital_asset_harvester.prompts import DEFAULT_PROMPTS, PromptManager
from digital_asset_harvester.ingest.email_parser import decode_header_value, extract_body
from digital_asset_harvester.processing.extractors import registry
from digital_asset_harvester.processing.constants import (
    CRYPTO_EXCHANGES,
    CRYPTO_EXCHANGES_PATTERN,
    CRYPTOCURRENCY_TERMS,
    CRYPTOCURRENCY_TERMS_PATTERN,
    NON_PURCHASE_PATTERNS,
    NON_PURCHASE_PATTERNS_PATTERN,
    PURCHASE_KEYWORDS,
    PURCHASE_KEYWORDS_PATTERN,
)
from digital_asset_harvester.validation import PurchaseRecord, PurchaseValidator
from digital_asset_harvester.telemetry import (
    MetricsTracker,
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
    logger_factory: StructuredLoggerFactory = field(default_factory=StructuredLoggerFactory)
    validator: PurchaseValidator = field(init=False)
    pii_scrubber: PIIScrubber = field(init=False)
    event_logger: StructuredLoggerAdapter = field(init=False)
    metrics: MetricsTracker = field(default_factory=MetricsTracker)
    prompts: PromptManager = field(default_factory=lambda: DEFAULT_PROMPTS)
    _metadata_cache: OrderedDict[str, Dict[str, str]] = field(default_factory=OrderedDict, init=False)
    _MAX_CACHE_SIZE: int = 1000

    def __post_init__(self) -> None:
        self.validator = PurchaseValidator(allow_unknown_crypto=self.settings.allow_unknown_cryptos)
        # Initialize PII scrubber with crypto terms to avoid over-scrubbing
        skip_terms = set(CRYPTOCURRENCY_TERMS) | set(CRYPTO_EXCHANGES)
        self.pii_scrubber = PIIScrubber(skip_terms=skip_terms)
        self.event_logger = self.logger_factory.build(
            __name__,
            default_fields={
                "component": "email_purchase_extractor",
                "strict_validation": self.settings.strict_validation,
            },
        )

    def _contains_keywords(self, text: str, pattern: Any) -> bool:
        """Check if text matches the specified regex pattern."""
        return bool(pattern.search(text))

    def _extract_email_metadata(self, email_content: str) -> Dict[str, str]:
        """Extract subject, sender, and body from email content with caching."""
        if email_content in self._metadata_cache:
            # Move to end for LRU
            self._metadata_cache.move_to_end(email_content)
            return self._metadata_cache[email_content]

        metadata = {"subject": "", "sender": "", "body": ""}

        # Check if it looks like a raw RFC 5322 message
        # A simple heuristic: starts with a common header or has a colon in the first non-empty line
        first_line = ""
        for line in email_content.split("\n"):
            if line.strip():
                first_line = line
                break

        if ":" in first_line and first_line.split(":")[0].replace("-", "").isalnum():
            # Use standard email library for robust parsing
            msg = email.message_from_string(email_content)
            metadata["subject"] = decode_header_value(msg.get("subject", ""))
            metadata["sender"] = decode_header_value(msg.get("from", ""))
            metadata["body"] = extract_body(msg)

            # Special case: If our CLI-formatted "Body: " marker is present and body is still empty
            if not metadata["body"] or len(metadata["body"]) < 10:
                for line in email_content.split("\n"):
                    if line.lower().startswith("body: "):
                        metadata["body"] = line[6:].strip()
                        break

        # Fallback if standard parsing failed to get basic metadata
        if not metadata["subject"] and not metadata["sender"]:
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
                    body_started = True
                    body_lines.append(line_strip[6:].strip())
                elif not line_strip:
                    if metadata["subject"] or metadata["sender"]:
                        body_started = True
                elif ":" not in line_strip:
                    if metadata["subject"] or metadata["sender"]:
                        body_started = True
                        body_lines.append(line)

            if body_lines:
                metadata["body"] = "\n".join(body_lines).strip()

        self._metadata_cache[email_content] = metadata
        if len(self._metadata_cache) > self._MAX_CACHE_SIZE:
            self._metadata_cache.popitem(last=False)

        return metadata

    def _is_likely_crypto_related(self, email_content: str) -> bool:
        """Quick keyword-based check to see if email might be crypto-related."""
        metadata = self._extract_email_metadata(email_content)
        full_text = f"{metadata['subject']} {metadata['sender']} {metadata['body']}"

        # Check for crypto exchanges in sender or content
        has_crypto_exchange = self._contains_keywords(metadata["sender"], CRYPTO_EXCHANGES_PATTERN)
        has_crypto_terms = self._contains_keywords(full_text, CRYPTOCURRENCY_TERMS_PATTERN)

        return has_crypto_exchange or has_crypto_terms

    def _is_likely_purchase_related(self, email_content: str) -> bool:
        """Check if email contains purchase-related keywords."""
        metadata = self._extract_email_metadata(email_content)
        full_text = f"{metadata['subject']} {metadata['body']}"

        has_purchase_keywords = self._contains_keywords(full_text, PURCHASE_KEYWORDS_PATTERN)
        has_non_purchase_patterns = self._contains_keywords(full_text, NON_PURCHASE_PATTERNS_PATTERN)

        return has_purchase_keywords and not has_non_purchase_patterns

    def _scrub_pii_if_enabled(self, email_content: str) -> str:
        """Apply PII scrubbing to email content if enabled in settings or privacy mode."""
        if self.settings.enable_pii_scrubbing or self.settings.enable_privacy_mode:
            logger.debug("PII scrubbing enabled, processing email content")
            return self.pii_scrubber.scrub(email_content)
        return email_content

    def _should_skip_llm_analysis(self, email_content: str) -> bool:
        """Determine if email can be quickly filtered out without LLM analysis."""
        metadata = self._extract_email_metadata(email_content)
        full_text = f"{metadata['subject']} {metadata['sender']} {metadata['body']}"

        # Skip if contains clear non-purchase patterns
        if self._contains_keywords(full_text, NON_PURCHASE_PATTERNS_PATTERN):
            return True

        # Skip if doesn't contain any crypto-related terms
        if not self._is_likely_crypto_related(email_content):
            return True

        return False

    def is_crypto_purchase_email(self, email_content: str, max_retries: Optional[int] = None) -> bool:
        self.metrics.increment("classification_total")
        retries = max_retries if max_retries is not None else self.settings.llm_max_retries

        if self.settings.enable_preprocessing:
            if self._should_skip_llm_analysis(email_content):
                logger.debug("Skipping LLM analysis - email filtered out by preprocessing")
                self.metrics.increment("classification_skipped_preprocessing")
                return False

            if not (self._is_likely_crypto_related(email_content) and self._is_likely_purchase_related(email_content)):
                logger.debug("Email doesn't meet basic crypto + purchase criteria")
                return False

        # Apply PII scrubbing before sending to LLM
        scrubbed_content = self._scrub_pii_if_enabled(email_content)
        prompt = self.prompts.render("classification", email_content=scrubbed_content)

        try:
            logger.info("Submitting email for classification (up to %d attempts)", retries)
            start_time = time.time()
            result = self.llm_client.generate_json(prompt, retries=retries)
            duration = time.time() - start_time
            self.metrics.record_latency("llm_classification", duration)
            self.metrics.increment("llm_calls_total")
            if result.metadata and result.metadata.get("cached"):
                self.metrics.increment("llm_cache_hits")
            else:
                self.metrics.increment("llm_cache_misses")

            if result.metadata and result.metadata.get("fallback_used"):
                self.metrics.increment("llm_fallback_usage")

        except LLMError as exc:
            logger.error("Failed to categorize email after %d attempts: %s", retries, exc)
            self.metrics.increment("llm_calls_failed")
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
            self.metrics.increment("extraction_regex_attempts")
            metadata = self._extract_email_metadata(email_content)
            regex_results = registry.extract(metadata["subject"], metadata["sender"], metadata["body"])
            if regex_results:
                logger.info("Successfully extracted purchase info using regex extractor")
                self.metrics.increment("extraction_regex_success")
                return self._process_extracted_transactions(regex_results, method="regex")

        # 2. Fallback to LLM extraction
        self.metrics.increment("extraction_llm_attempts")
        retries = max_retries if max_retries is not None else self.settings.llm_max_retries

        # Apply PII scrubbing before sending to LLM
        scrubbed_content = self._scrub_pii_if_enabled(email_content)
        prompt = self.prompts.render(
            "extraction",
            email_content=scrubbed_content,
            default_timezone=default_timezone,
        )

        try:
            logger.info("Submitting email for purchase extraction (up to %d attempts)", retries)
            start_time = time.time()
            result = self.llm_client.generate_json(prompt, retries=retries)
            duration = time.time() - start_time
            self.metrics.record_latency("llm_extraction", duration)
            self.metrics.increment("llm_calls_total")
            if result.metadata and result.metadata.get("cached"):
                self.metrics.increment("llm_cache_hits")
            else:
                self.metrics.increment("llm_cache_misses")

            if result.metadata and result.metadata.get("fallback_used"):
                self.metrics.increment("llm_fallback_usage")

            self.metrics.increment("extraction_llm_success")
        except LLMError as exc:
            logger.error("Failed to extract purchase info after %d attempts: %s", retries, exc)
            self.metrics.increment("llm_calls_failed")
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
                    purchase_data["purchase_date"] = date.strftime("%Y-%m-%d %H:%M:%S %Z")
                except (ValueError, TypeError) as e:
                    logger.warning("Invalid date format (%s). Using current time.", e)
                    purchase_data["purchase_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
            else:
                logger.warning("No purchase date found, using current time")
                purchase_data["purchase_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
        return transactions

    def _process_extracted_transactions(
        self, transactions: List[Dict[str, Any]], method: str = "llm"
    ) -> List[Dict[str, Any]]:
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
                field for field in required_fields if field not in purchase_data or purchase_data[field] is None
            }

            # Log extraction quality
            confidence = purchase_data.get("confidence", 0.5)
            notes = purchase_data.get("extraction_notes", "")
            logger.info("Extraction confidence: %.2f - %s", confidence, notes)
            log_event(
                self.event_logger,
                "extraction_completed",
                confidence=confidence,
                missing_fields=";".join(sorted(missing_fields)) if missing_fields else "",
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
                logger.warning("Missing required field(s): %s", ", ".join(sorted(missing_fields)))
                if self.settings.strict_validation:
                    continue

            extracted_purchases.append(purchase_data)

        # Use our existing date processing
        return self._process_extracted_dates(extracted_purchases)

    def _validate_purchase_data(self, purchase_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate extracted purchase data for basic sanity checks."""

        if not purchase_data:
            return False, ["No data to validate"]

        if not self.settings.enable_validation:
            return True, []

        strict = self.settings.strict_validation
        validation_errors = []

        try:
            # Pydantic validation handles numeric conversion and basic constraints
            record = PurchaseRecord.model_validate(purchase_data)
        except (ValueError, ValidationError) as e:
            if isinstance(e, ValidationError):
                for error in e.errors():
                    field = str(error["loc"][0]) if error["loc"] else "unknown"
                    msg = f"Validation issue for {field}: {error['msg']}"
                    logger.warning(msg)
                    validation_errors.append(msg)
            else:
                logger.warning("Purchase record failed validation: %s", e)
                validation_errors.append(str(e))

            if self.settings.require_numeric_validation or strict:
                return False, validation_errors
            return True, validation_errors

        # Extra validation (e.g., unknown crypto)
        issues = self.validator.validate(record)
        for issue in issues:
            msg = f"Validation issue for {issue.field}: {issue.message}"
            logger.warning(msg)
            validation_errors.append(msg)

        if issues and strict:
            return False, validation_errors

        return True, validation_errors

    def process_email(self, email_content: str) -> Dict[str, Any]:
        """Process an email to determine if it contains cryptocurrency purchase information."""
        processing_notes: List[str] = []

        # First check if it's likely a crypto purchase email
        if not self.is_crypto_purchase_email(email_content):
            logger.debug("Email classified as non-crypto-purchase")
            reason = "Email did not match required keywords for crypto purchases"
            return {
                "has_purchase": False,
                "purchases": [],
                "processing_notes": [f"Email not classified as crypto purchase: {reason}"],
                "metrics": self.metrics,
            }

        # If classified as purchase, extract the details
        extracted_purchases = self.extract_purchase_info(email_content)

        if not extracted_purchases:
            logger.warning("Failed to extract purchase information despite positive classification")
            reason = "LLM failed to identify structured purchase data in the email body"
            processing_notes.append(f"Classification positive but extraction failed: {reason}")
            return {
                "has_purchase": False,
                "purchases": [],
                "processing_notes": processing_notes,
                "metrics": self.metrics,
            }

        validated_purchases = []
        for purchase_info in extracted_purchases:
            try:
                # 1. Populate asset_id if not already present
                if not purchase_info.get("asset_id") and purchase_info.get("item_name"):
                    purchase_info["asset_id"] = asset_mapper.get_asset_id(purchase_info["item_name"])

                # 2. Perform currency conversion if enabled
                if (
                    self.settings.enable_currency_conversion
                    and purchase_info.get("total_spent")
                    and purchase_info.get("currency")
                ):
                    from_curr = purchase_info["currency"]
                    to_curr = self.settings.base_fiat_currency
                    p_date = purchase_info.get("purchase_date", "")

                    rate = fx_service.get_rate(p_date, from_curr, to_curr)
                    if rate:
                        # Use Decimal for calculation
                        cad_amount = Decimal(str(purchase_info["total_spent"])) * rate
                        purchase_info["fiat_amount_cad"] = cad_amount
                        logger.info(f"Converted {purchase_info['total_spent']} {from_curr} to {cad_amount} {to_curr}")

                # 3. Validate the extracted data (includes Pydantic validation)
                is_valid, validation_issues = self._validate_purchase_data(purchase_info)
                if not is_valid:
                    logger.warning("Extracted purchase data failed validation")
                    reason = "; ".join(validation_issues)
                    processing_notes.append(
                        f"Extracted data for {purchase_info.get('item_name')} failed validation: {reason}"
                    )
                    continue

                # 4. Create a PurchaseRecord for confidence calculation and type normalization
                purchase_record = PurchaseRecord.model_validate(purchase_info)

                # Calculate and update the confidence score
                purchase_info["confidence"] = calculate_confidence(purchase_record)

                # Normalize types for consistency in the output dictionary
                if purchase_record.amount is not None:
                    purchase_info["amount"] = float(purchase_record.amount)
                if purchase_record.total_spent is not None:
                    purchase_info["total_spent"] = float(purchase_record.total_spent)
                if purchase_record.fee_amount is not None:
                    purchase_info["fee_amount"] = float(purchase_record.fee_amount)
                if purchase_record.fiat_amount_cad is not None:
                    purchase_info["fiat_amount_cad"] = float(purchase_record.fiat_amount_cad)

                purchase_info["transaction_type"] = purchase_record.transaction_type
                validated_purchases.append(purchase_info)
            except Exception as e:
                logger.warning("Error processing extracted purchase: %s", e)
                processing_notes.append(f"Error processing extracted purchase: {e}")

        if not validated_purchases:
            return {
                "has_purchase": False,
                "purchases": [],
                "processing_notes": processing_notes,
                "metrics": self.metrics,
            }

        logger.info("Successfully processed crypto purchase email")
        processing_notes.append(f"Successfully extracted and validated {len(validated_purchases)} purchase(s)")

        return {
            "has_purchase": True,
            "purchases": validated_purchases,
            "processing_notes": processing_notes,
            "metrics": self.metrics,
        }
