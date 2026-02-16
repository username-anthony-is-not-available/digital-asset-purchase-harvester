"""Specialized extractor for Newton (Canada) emails."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseExtractor


class NewtonExtractor(BaseExtractor):
    """Extractor for Newton trade confirmation emails."""

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a Newton email."""
        sender_lower = sender.lower()
        if "newton.co" not in sender_lower:
            return False

        subject_lower = subject.lower()
        patterns = [
            r"trade confirmation",
            r"you bought",
            r"transaction confirmation",
        ]
        return any(re.search(p, subject_lower) for p in patterns) or "newton" in sender_lower

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Newton email."""
        purchases = []

        # Pattern: "You bought 0.1 BTC for $5,000.00 CAD"
        # Also handles variations without CAD
        pattern = r"bought\s+([\d,.]+)\s+([A-Z]{3,5})\s+for\s+([$€£¥])?([\d,.]+)\s*([A-Z]{3})?"
        match = re.search(pattern, body, re.IGNORECASE)

        if match:
            amount = match.group(1).replace(",", "")
            crypto = match.group(2).upper()
            total_spent = match.group(4).replace(",", "")
            currency = match.group(5) or "CAD"  # Default to CAD for Newton

            if not match.group(5) and match.group(3):
                symbol_map = {"$": "CAD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                currency = symbol_map.get(match.group(3), "CAD")

            purchases.append(
                {
                    "amount": amount,
                    "item_name": crypto,
                    "total_spent": total_spent,
                    "currency": currency,
                    "vendor": "Newton",
                    "transaction_id": self._find_match(r"Reference\s*#?\s*:?\s*([A-Z0-9\-]+)", body),
                    "extraction_method": "regex",
                }
            )

        return purchases
