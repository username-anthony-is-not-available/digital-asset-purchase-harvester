"""Specialized extractor for Bitfinex emails."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any, Dict, List

from .base import BaseExtractor


class BitfinexExtractor(BaseExtractor):
    """Extractor for Bitfinex trade execution emails."""

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a Bitfinex email."""
        sender_lower = sender.lower()
        if "bitfinex.com" not in sender_lower:
            return False

        subject_lower = subject.lower()
        return "trade execution" in subject_lower

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Bitfinex email."""
        purchases = []

        # Pattern: "Exchange Trade Execution - BUY 0.5 ETH @ 2500.0 USD on ETH/USD"
        # Often in the subject or body
        pattern = r"(BUY|SELL)\s+([\d,.]+)\s+([A-Z]{3,5})\s+@\s+([\d,.]+)\s+([A-Z]{3,5})"

        match = re.search(pattern, body if body else subject, re.IGNORECASE)
        if match:
            action = match.group(1).upper()
            amount = match.group(2).replace(",", "")
            crypto = match.group(3).upper()
            price_per_unit = match.group(4).replace(",", "")
            currency = match.group(5).upper()

            total_spent = Decimal(amount) * Decimal(price_per_unit)
            tx_type = "buy" if action == "BUY" else "withdrawal"

            purchases.append(
                {
                    "amount": amount,
                    "item_name": crypto,
                    "total_spent": str(total_spent),
                    "currency": currency,
                    "vendor": "Bitfinex",
                    "transaction_type": tx_type,
                    "transaction_id": self._find_match(r"Order\s*ID\s*:?\s*(\d+)", body),
                    "extraction_method": "regex",
                    "confidence": 0.98,
                }
            )

        return purchases
