"""Specialized extractor for CoinSpot emails."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseExtractor


class CoinSpotExtractor(BaseExtractor):
    """Extractor for CoinSpot purchase confirmation emails."""

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a CoinSpot email."""
        # We consider any email from coinspot.com as potentially handleable.
        # The extract() method will then attempt to find purchase details.
        return "coinspot.com" in sender.lower()

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from CoinSpot email."""
        purchases = []

        # CoinSpot pattern: "You have successfully purchased 50 ADA for $25.00 AUD."
        # Pattern: purchased ([\d,.]+) ([A-Z0-9]+) for ([$€£¥])?([\d,.]+) ([A-Z]{3})?
        pattern = r"purchased\s+([\d,.]+)\s+([A-Z0-9]+)\s+for\s+([$€£¥])?([\d,.]+)\s*([A-Z]{3})?"

        for match in re.finditer(pattern, body, re.IGNORECASE):
            amount = match.group(1).replace(",", "")
            crypto = match.group(2).upper()
            total_spent = match.group(4).replace(",", "")

            currency = match.group(5)
            if not currency and match.group(3):
                symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "A$": "AUD"}
                currency = symbol_map.get(match.group(3), "USD")
            if not currency:
                currency = "AUD"  # CoinSpot is Australian

            purchases.append(self._create_purchase_dict(amount, crypto, total_spent, currency, body))

        return purchases

    def _create_purchase_dict(
        self, amount: str, crypto: str, total_spent: str | None, currency: str, body: str
    ) -> Dict[str, Any]:
        # Extract Reference: CS-20240115-001
        txn_id = self._find_match(r"Reference:\s*([A-Z0-9\-]+)", body)

        return {
            "amount": amount,
            "item_name": crypto,
            "total_spent": total_spent,
            "currency": currency,
            "vendor": "CoinSpot",
            "transaction_id": txn_id,
            "extraction_method": "regex",
        }
