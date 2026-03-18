"""Specialized extractor for Independent Reserve (Australia) emails."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseExtractor


class IndependentReserveExtractor(BaseExtractor):
    """Extractor for Independent Reserve trade confirmation emails."""

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is an Independent Reserve email."""
        sender_lower = sender.lower()
        if "independentreserve.com" not in sender_lower:
            return False

        subject_lower = subject.lower()
        patterns = [
            r"trade confirmation",
            r"order filled",
            r"buy order",
        ]
        return any(re.search(p, subject_lower) for p in patterns) or "independent reserve" in sender_lower

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Independent Reserve email."""
        purchases = []

        # Pattern: "You have successfully bought 0.1 BTC for $5,000.00 AUD"
        # Or: "Bought 0.1 BTC at $50,000.00 AUD"
        # Or: "Amount: 0.1 BTC, Rate: 50,000 AUD, Total: 5,000 AUD"

        # 1. Direct sentence pattern
        pattern1 = r"(?:bought|purchased)\s+([\d,.]+)\s+([A-Z]{3,5})\s+for\s+([$])?([\d,.]+)\s*([A-Z]{3})?"

        for match in re.finditer(pattern1, body, re.IGNORECASE):
            amount_str = match.group(1).replace(",", "")
            crypto = match.group(2).upper()
            total_str = match.group(4).replace(",", "")
            currency = match.group(5) or "AUD"

            try:
                purchases.append({
                    "amount": str(float(amount_str)),
                    "item_name": crypto,
                    "total_spent": str(float(total_str)),
                    "currency": currency,
                    "vendor": "Independent Reserve",
                    "transaction_id": self._find_match(r"\b(?:Reference|Ref|Order ID):?\s*([A-Z0-9\-]+)", body),
                    "extraction_method": "regex",
                })
            except (ValueError, TypeError):
                continue

        return purchases
