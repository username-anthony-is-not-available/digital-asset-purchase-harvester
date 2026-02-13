"""Validation utilities for purchase data."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Optional

from .schemas import PurchaseRecord

logger = logging.getLogger(__name__)

ISO_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3,5}$")
CRYPTO_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,10}$")

KNOWN_CRYPTO_NAMES = {
    "bitcoin",
    "btc",
    "ethereum",
    "eth",
    "litecoin",
    "ltc",
    "solana",
    "sol",
    "dogecoin",
    "doge",
    "cardano",
    "ada",
    "polkadot",
    "dot",
    "ripple",
    "xrp",
    "binance coin",
    "bnb",
    "tether",
    "usdt",
    "usd coin",
    "usdc",
}


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str


class PurchaseValidator:
    def __init__(self, *, allow_unknown_crypto: bool = True) -> None:
        self.allow_unknown_crypto = allow_unknown_crypto

    def validate(self, record: PurchaseRecord) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        if record.total_spent is not None and record.total_spent <= Decimal("0"):
            issues.append(ValidationIssue("total_spent", "must be greater than zero"))

        if record.amount is not None and record.amount <= Decimal("0"):
            issues.append(ValidationIssue("amount", "must be greater than zero"))

        if record.currency and not ISO_CURRENCY_PATTERN.match(record.currency.upper()):
            issues.append(ValidationIssue("currency", "must be ISO 4217 uppercase code"))

        lower_item = record.item_name.lower()
        if not lower_item:
            issues.append(ValidationIssue("item_name", "is required"))
        elif lower_item not in KNOWN_CRYPTO_NAMES and not self.allow_unknown_crypto:
            issues.append(ValidationIssue("item_name", "unknown cryptocurrency"))

        if not record.vendor.strip():
            issues.append(ValidationIssue("vendor", "is required"))

        if not record.purchase_date.strip():
            issues.append(ValidationIssue("purchase_date", "is required"))

        return issues
