"""Specialized extractor for Bitstamp emails."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseExtractor


class BitstampExtractor(BaseExtractor):
    """Extractor for Bitstamp trade confirmation emails."""

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a Bitstamp email."""
        sender_lower = sender.lower()
        if "bitstamp.net" not in sender_lower:
            return False

        subject_lower = subject.lower()
        patterns = [
            r"transaction confirmation",
            r"bought",
            r"sold",
        ]
        return any(re.search(p, subject_lower) for p in patterns)

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Bitstamp email."""
        purchases = []

        # Pattern: "You have successfully bought 0.5 BTC for 25,000.00 USD"
        # Pattern: "You have successfully sold 10.0 ETH for 20,000.00 USD"
        pattern = r"successfully\s+(bought|sold)\s+([\d,.]+)\s+([A-Z]{3,5})\s+for\s+([\d,.]+)\s+([A-Z]{3})"

        for match in re.finditer(pattern, body, re.IGNORECASE):
            action = match.group(1).lower()
            amount = match.group(2).replace(",", "")
            crypto = match.group(3).upper()
            total_spent = match.group(4).replace(",", "")
            currency = match.group(5).upper()

            tx_type = "buy" if action == "bought" else "withdrawal"

            purchases.append(
                {
                    "amount": amount,
                    "item_name": crypto,
                    "total_spent": total_spent,
                    "currency": currency,
                    "vendor": "Bitstamp",
                    "transaction_type": tx_type,
                    "transaction_id": self._find_match(r"Transaction\s*ID\s*:?\s*([A-Z0-9]+)", body),
                    "extraction_method": "regex",
                    "confidence": 0.98,
                }
            )

        return purchases
