"""Specialized extractor for Crypto.com emails."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseExtractor


class CryptocomExtractor(BaseExtractor):
    """Extractor for Crypto.com purchase confirmation emails."""

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a Crypto.com email."""
        sender_lower = sender.lower()
        if "crypto.com" not in sender_lower:
            return False

        subject_lower = subject.lower()
        patterns = [
            r"order",
            r"executed",
            r"buy",
            r"filled",
        ]
        return any(re.search(p, subject_lower) for p in patterns)

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Crypto.com email."""
        purchases = []

        # Crypto.com pattern: "Your market order to buy 2.5 SOL has been filled at a price of $25.00 per SOL."
        # "Total cost: $62.50 USD."
        amount_match = re.search(r"buy\s+([\d,.]+)\s+([A-Z]{3,5})", body, re.IGNORECASE)
        total_match = re.search(r"Total cost:\s*([$€£¥])?([\d,.]+)\s*([A-Z]{3})?", body, re.IGNORECASE)

        if amount_match and total_match:
            amount = amount_match.group(1).replace(",", "")
            crypto = amount_match.group(2).upper()
            total_spent = total_match.group(2).replace(",", "")

            currency = total_match.group(3)
            if not currency and total_match.group(1):
                symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                currency = symbol_map.get(total_match.group(1), "USD")
            if not currency:
                currency = "USD"

            purchases.append(self._create_purchase_dict(amount, crypto, total_spent, currency, body))

        return purchases

    def _create_purchase_dict(self, amount: str, crypto: str, total_spent: str | None, currency: str, body: str) -> Dict[str, Any]:
        # Extract order ID
        txn_id = self._find_match(r"order\s+#?([A-Z0-9\-]+)", body)

        return {
            "amount": amount,
            "item_name": crypto,
            "total_spent": total_spent,
            "currency": currency,
            "vendor": "Crypto.com",
            "transaction_id": txn_id,
            "extraction_method": "regex",
        }
