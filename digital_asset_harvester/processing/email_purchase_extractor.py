"""Logic for identifying and extracting crypto purchase information from emails."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from digital_asset_harvester.config import HarvesterSettings, get_settings
from digital_asset_harvester.llm import LLMError, OllamaLLMClient
from digital_asset_harvester.prompts import DEFAULT_PROMPTS, PromptManager
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
    llm_client: OllamaLLMClient = field(default_factory=OllamaLLMClient)
    logger_factory: StructuredLoggerFactory = field(
        default_factory=StructuredLoggerFactory
    )
    validator: PurchaseValidator = field(init=False)
    event_logger: StructuredLoggerAdapter = field(init=False)
    prompts: PromptManager = field(default_factory=lambda: DEFAULT_PROMPTS)

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

    # Common cryptocurrency exchanges and platforms
    CRYPTO_EXCHANGES = {
        # Major global exchanges
        "coinbase",
        "binance",
        "kraken",
        "bitfinex",
        "bitstamp",
        "gemini",
        "huobi",
        "okx",
        "kucoin",
        "crypto.com",
        "ftx",
        "bybit",
        "gate.io",
        "bittrex",
        "poloniex",
        # Mid-tier exchanges
        "coinex",
        "bitmart",
        "mexc",
        "bitget",
        "lbank",
        "probit",
        # Australian exchanges
        "coinspot",
        "independent reserve",
        "btcmarkets",
        "swyftx",
        # Canadian exchanges
        "coinsquare",
        "bitbuy",
        "newton",
        "coinhub",
        "ndax",
        # P2P and decentralized
        "localbitcoins",
        "paxful",
        "bisq",
        # European exchanges
        "bitvavo",
        "luno",
        "bitpanda",
        "coinmama",
        # Asian exchanges
        "upbit",
        "bithumb",
        "korbit",
        "zaif",
        "bitflyer",
        "liquid",
        # Latin American
        "mercado bitcoin",
        "bitso",
        "ripio",
        # US-specific
        "coinbase pro",
        "coinbase exchange",
        "robinhood crypto",
        "cash app",
        "paypal",
        "venmo",
        # Others
        "cex.io",
        "changelly",
        "shapeshift",
    }

    # Cryptocurrency names and symbols
    CRYPTOCURRENCY_TERMS = {
        # Major cryptocurrencies
        "bitcoin",
        "btc",
        "ethereum",
        "eth",
        "litecoin",
        "ltc",
        "bitcoin cash",
        "bch",
        "ripple",
        "xrp",
        "cardano",
        "ada",
        "polkadot",
        "dot",
        "chainlink",
        "link",
        "stellar",
        "xlm",
        "dogecoin",
        "doge",
        "polygon",
        "matic",
        "solana",
        "sol",
        "avalanche",
        "avax",
        "terra",
        "luna",
        "cosmos",
        "atom",
        "algorand",
        "algo",
        "tezos",
        "xtz",
        "monero",
        "xmr",
        "zcash",
        "zec",
        "dash",
        "neo",
        "eos",
        "tron",
        "trx",
        "iota",
        "miota",
        "vechain",
        "vet",
        "qtum",
        "ont",
        "zil",
        # Stablecoins
        "tether",
        "usdt",
        "usd coin",
        "usdc",
        "binance usd",
        "busd",
        "dai",
        "tusd",
        "true usd",
        "pax",
        "paxos",
        "usdd",
        "frax",
        # Popular DeFi tokens
        "uniswap",
        "uni",
        "aave",
        "compound",
        "comp",
        "maker",
        "mkr",
        "synthetix",
        "snx",
        "curve",
        "crv",
        # Layer 2 and scaling
        "arbitrum",
        "arb",
        "optimism",
        "op",
        "immutable",
        "imx",
        # Memecoins
        "shiba inu",
        "shib",
        "pepe",
        "floki",
        # General terms
        "cryptocurrency",
        "crypto",
        "digital currency",
        "digital asset",
        "altcoin",
        "token",
        "coin",
    }

    # Purchase-related keywords
    PURCHASE_KEYWORDS = {
        "purchase",
        "bought",
        "buy",
        "order",
        "transaction",
        "payment",
        "receipt",
        "confirmation",
        "executed",
        "filled",
        "completed",
        "successful",
        "acquired",
        "deposit",
        "trade",
        "exchange",
        "convert",
        "swap",
        "market order",
        "limit order",
        "instant buy",
        "recurring buy",
        "auto-invest",
    }

    # Email patterns that indicate non-purchase content
    NON_PURCHASE_PATTERNS = {
        "newsletter",
        "unsubscribe",
        "marketing",
        "promotion",
        "survey",
        "feedback",
        "educational",
        "news",
        "update",
        "announcement",
        "blog",
        "article",
        "webinar",
        "invite",
        "referral program",
        "contest",
        "giveaway",
        "airdrop notification",
        "price alert",
        "market analysis",
        "weekly report",
        "monthly summary",
    }

    def _contains_keywords(self, text: str, keywords: Set[str]) -> bool:
        """Check if text contains any of the specified keywords (case-insensitive)."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def _extract_email_metadata(self, email_content: str) -> Dict[str, str]:
        """Extract subject, sender, and body from email content."""
        lines = email_content.split("\n")
        metadata = {"subject": "", "sender": "", "body": ""}

        for i, line in enumerate(lines):
            if line.startswith("Subject: "):
                metadata["subject"] = line[9:].strip()
            elif line.startswith("From: "):
                metadata["sender"] = line[6:].strip()
            elif line.startswith("Body: "):
                metadata["body"] = "\n".join(lines[i + 1 :]).strip()
                break

        return metadata

    def _is_likely_crypto_related(self, email_content: str) -> bool:
        """Quick keyword-based check to see if email might be crypto-related."""
        metadata = self._extract_email_metadata(email_content)
        full_text = f"{metadata['subject']} {metadata['sender']} {metadata['body']}"

        # Check for crypto exchanges in sender or content
        has_crypto_exchange = self._contains_keywords(
            metadata["sender"], self.CRYPTO_EXCHANGES
        )
        has_crypto_terms = self._contains_keywords(full_text, self.CRYPTOCURRENCY_TERMS)

        return has_crypto_exchange or has_crypto_terms

    def _is_likely_purchase_related(self, email_content: str) -> bool:
        """Check if email contains purchase-related keywords."""
        metadata = self._extract_email_metadata(email_content)
        full_text = f"{metadata['subject']} {metadata['body']}"

        has_purchase_keywords = self._contains_keywords(
            full_text, self.PURCHASE_KEYWORDS
        )
        has_non_purchase_patterns = self._contains_keywords(
            full_text, self.NON_PURCHASE_PATTERNS
        )

        return has_purchase_keywords and not has_non_purchase_patterns

    def _should_skip_llm_analysis(self, email_content: str) -> bool:
        """Determine if email can be quickly filtered out without LLM analysis."""
        metadata = self._extract_email_metadata(email_content)
        full_text = f"{metadata['subject']} {metadata['sender']} {metadata['body']}"

        # Skip if contains clear non-purchase patterns
        if self._contains_keywords(full_text, self.NON_PURCHASE_PATTERNS):
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

        if is_purchase and confidence < self.settings.min_confidence_threshold:
            logger.info(
                "Classification below confidence threshold (%.2f < %.2f)",
                confidence,
                self.settings.min_confidence_threshold,
            )
            return False

        return bool(is_purchase)

    def extract_purchase_info(
        self,
        email_content: str,
        max_retries: Optional[int] = None,
        default_timezone: str = "UTC",
    ) -> Optional[Dict[str, Any]]:
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
            return None

        purchase_data = result.data

        if purchase_data is None:
            logger.info("No purchase information found in the email")
            return None

        # Validate required fields
        required_fields = {"total_spent", "currency", "amount", "item_name", "vendor"}
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
            missing_fields=";".join(sorted(missing_fields)) if missing_fields else "",
        )

        if (
            confidence < self.settings.min_confidence_threshold
            and self.settings.strict_validation
        ):
            logger.warning(
                "Extraction confidence %.2f below threshold %.2f",
                confidence,
                self.settings.min_confidence_threshold,
            )
            return None

        if missing_fields:
            logger.warning(
                "Missing required field(s): %s", ", ".join(sorted(missing_fields))
            )
            if self.settings.strict_validation:
                return None

        # Process the purchase date
        if purchase_data.get("purchase_date"):
            try:
                # Parse the date and ensure it's in UTC
                date_str = purchase_data["purchase_date"]
                # Handle various date formats
                if "T" in date_str:
                    date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                else:
                    # Try to parse common date formats
                    for fmt in [
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d",
                        "%m/%d/%Y %H:%M:%S",
                        "%m/%d/%Y",
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
                purchase_data["purchase_date"] = datetime.now(timezone.utc).strftime(
                    "%Y-%m-%d %H:%M:%S %Z"
                )
        else:
            logger.warning("No purchase date found, using current time")
            purchase_data["purchase_date"] = datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )

        # Clean up the response by removing extraction metadata
        cleaned_data = {
            k: v
            for k, v in purchase_data.items()
            if k not in ["confidence", "extraction_notes"]
        }

        return cleaned_data

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
                "processing_notes": ["Email not classified as crypto purchase"],
            }

        # If classified as purchase, extract the details
        purchase_info = self.extract_purchase_info(email_content)

        if not purchase_info:
            logger.warning(
                "Failed to extract purchase information despite positive classification"
            )
            processing_notes.append("Classification positive but extraction failed")
            return {
                "has_purchase": False,
                "processing_notes": processing_notes,
            }

        # Validate the extracted data
        if not self._validate_purchase_data(purchase_info):
            logger.warning("Extracted purchase data failed validation")
            processing_notes.append("Extracted data failed validation checks")
            return {
                "has_purchase": False,
                "processing_notes": processing_notes,
            }

        logger.info("Successfully processed crypto purchase email")
        processing_notes.append("Successfully extracted and validated purchase data")

        return {
            "has_purchase": True,
            "purchase_info": purchase_info,
            "processing_notes": processing_notes,
        }
