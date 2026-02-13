"""Specialized extractor for Gemini emails."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseExtractor


class GeminiExtractor(BaseExtractor):
    """Extractor for Gemini purchase confirmation emails."""

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a Gemini email."""
        sender_lower = sender.lower()
        if "gemini.com" not in sender_lower:
            return False

        subject_lower = subject.lower()
        patterns = [
            r"order confirmation",
            r"purchase",
            r"buy",
        ]
        return any(re.search(p, subject_lower) for p in patterns) or "gemini" in sender_lower

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Gemini email."""
        purchases = []

        # Gemini pattern: "Your order to purchase 0.005 BTC for $150.00 has been completed."
        pattern = r"order to purchase\s+([\d,.]+)\s+([A-Z]{3,5})\s+for\s+([$€£¥])?([\d,.]+)"
        match = re.search(pattern, body, re.IGNORECASE)

        if match:
            amount = match.group(1).replace(",", "")
            crypto = match.group(2).upper()
            total_spent = match.group(4).replace(",", "")

            currency = "USD"
            if match.group(3):
                symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                currency = symbol_map.get(match.group(3), "USD")

            purchases.append(self._create_purchase_dict(amount, crypto, total_spent, currency, body))

        return purchases

    def _create_purchase_dict(
        self, amount: str, crypto: str, total_spent: str | None, currency: str, body: str
    ) -> Dict[str, Any]:
        # Extract transaction ID
        txn_id = self._find_match(r"Transaction ID:\s*([A-Z0-9\-]+)", body)

        return {
            "amount": amount,
            "item_name": crypto,
            "total_spent": total_spent,
            "currency": currency,
            "vendor": "Gemini",
            "transaction_id": txn_id,
            "extraction_method": "regex",
        }
