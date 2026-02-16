"""Specialized extractor for BTCMarkets (Australia) emails."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseExtractor


class BTCMarketsExtractor(BaseExtractor):
    """Extractor for BTCMarkets trade confirmation emails."""

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a BTCMarkets email."""
        sender_lower = sender.lower()
        if "btcmarkets.net" not in sender_lower:
            return False

        subject_lower = subject.lower()
        patterns = [
            r"buy order filled",
            r"trade confirmation",
            r"order processed",
        ]
        return any(re.search(p, subject_lower) for p in patterns) or "btc markets" in sender_lower

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from BTCMarkets email."""
        purchases = []

        # Pattern: "Your buy order for 0.05 BTC has been filled at $60,000.00 AUD"
        # Or: "Bought 0.05 BTC for 3,000 AUD"
        pattern = r"(?:order for|bought)\s+([\d,.]+)\s+([A-Z]{3,5})\s+(?:has been filled at|for)\s+([$€£¥])?([\d,.]+)\s*([A-Z]{3})?"
        match = re.search(pattern, body, re.IGNORECASE)

        if match:
            amount = match.group(1).replace(",", "")
            crypto = match.group(2).upper()
            total_spent = match.group(4).replace(",", "")
            currency = match.group(5) or "AUD"  # Default to AUD for BTCMarkets

            if not match.group(5) and match.group(3):
                symbol_map = {"$": "AUD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                currency = symbol_map.get(match.group(3), "AUD")

            purchases.append(
                {
                    "amount": amount,
                    "item_name": crypto,
                    "total_spent": total_spent,
                    "currency": currency,
                    "vendor": "BTCMarkets",
                    "transaction_id": self._find_match(r"Order\s*ID\s*:?\s*([A-Z0-9\-]+)", body),
                    "extraction_method": "regex",
                }
            )

        return purchases
