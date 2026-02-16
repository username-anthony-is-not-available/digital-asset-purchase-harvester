"""Specialized extractor for Swyftx (Australia) emails."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseExtractor


class SwyftxExtractor(BaseExtractor):
    """Extractor for Swyftx trade confirmation emails."""

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a Swyftx email."""
        sender_lower = sender.lower()
        if "swyftx.com" not in sender_lower:
            return False

        subject_lower = subject.lower()
        patterns = [
            r"trade confirmation",
            r"you've successfully bought",
            r"order filled",
        ]
        return any(re.search(p, subject_lower) for p in patterns) or "swyftx" in sender_lower

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Swyftx email."""
        purchases = []

        # Pattern: "You've successfully bought 1.5 ETH for $4,500.00 AUD"
        pattern = r"bought\s+([\d,.]+)\s+([A-Z]{3,5})\s+for\s+([$€£¥])?([\d,.]+)\s*([A-Z]{3})?"
        match = re.search(pattern, body, re.IGNORECASE)

        if match:
            amount = match.group(1).replace(",", "")
            crypto = match.group(2).upper()
            total_spent = match.group(4).replace(",", "")
            currency = match.group(5) or "AUD"  # Default to AUD for Swyftx

            if not match.group(5) and match.group(3):
                symbol_map = {"$": "AUD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                currency = symbol_map.get(match.group(3), "AUD")

            purchases.append(
                {
                    "amount": amount,
                    "item_name": crypto,
                    "total_spent": total_spent,
                    "currency": currency,
                    "vendor": "Swyftx",
                    "transaction_id": self._find_match(r"Receipt\s*#?\s*:?\s*([A-Z0-9\-]+)", body),
                    "extraction_method": "regex",
                }
            )

        return purchases
