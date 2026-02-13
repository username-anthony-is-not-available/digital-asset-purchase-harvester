"""Specialized extractor for Kraken emails."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseExtractor


class KrakenExtractor(BaseExtractor):
    """Extractor for Kraken trade confirmation emails."""

    # Kraken specific ticker mapping
    TICKER_MAP = {
        "XBT": "BTC",
        "XDG": "DOGE",
    }

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a Kraken email."""
        sender_lower = sender.lower()
        if "kraken.com" not in sender_lower:
            return False

        subject_lower = subject.lower()
        patterns = [
            r"trade confirmation",
            r"kraken order",
            r"staking reward received",
        ]
        return any(re.search(p, subject_lower) for p in patterns) or "kraken" in sender_lower

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Kraken email."""
        purchases = []

        # Standard Kraken pattern: "You bought 0.75 XBT (BTC) for $35,000.00 USD."
        # Or simple: "You have successfully bought 0.5 XMR for 50.00 EUR."
        pattern = r"(?:bought|buy)\s+([\d,.]+)\s+([A-Z0-9]+)(?:\s+\([A-Z0-9]+\))?\s+for\s+([$€£¥])?([\d,.]+)\s*([A-Z]{3})?"
        match = re.search(pattern, body, re.IGNORECASE)

        if match:
            amount = match.group(1).replace(",", "")
            crypto_raw = match.group(2).upper()
            crypto = self.TICKER_MAP.get(crypto_raw, crypto_raw)
            total_spent = match.group(4).replace(",", "")

            currency = match.group(5)
            if not currency and match.group(3):
                symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                currency = symbol_map.get(match.group(3), "USD")
            if not currency:
                currency = "USD"

            purchases.append(self._create_purchase_dict(amount, crypto, total_spent, currency, body))

        # Handle Staking Rewards
        # "We've credited your account with 10.5 ADA in staking rewards."
        if not purchases and "staking rewards" in body.lower():
            match = re.search(r"credited your account with\s+([\d,.]+)\s+([A-Z0-9]+)", body, re.IGNORECASE)
            if match:
                amount = match.group(1).replace(",", "")
                crypto_raw = match.group(2).upper()
                crypto = self.TICKER_MAP.get(crypto_raw, crypto_raw)

                purchase = self._create_purchase_dict(amount, crypto, None, "", body)
                purchase["transaction_type"] = "staking_reward"
                purchases.append(purchase)

        return purchases

    def _create_purchase_dict(self, amount: str, crypto: str, total_spent: str | None, currency: str, body: str) -> Dict[str, Any]:
        # Extract order reference or ID
        txn_id = self._find_match(r"(?:ID|Reference|Order Reference):\s*([A-Z0-9\-]+)", body)

        # Extract fee: "Fee: $105.00 USD"
        fee_amount = None
        fee_currency = currency
        fee_match = re.search(r"Fee:\s*([$€£¥])?([\d,.]+)\s*([A-Z]{3})?", body, re.IGNORECASE)
        if fee_match:
            fee_amount = fee_match.group(2).replace(",", "")
            if fee_match.group(3):
                fee_currency = fee_match.group(3)

        return {
            "amount": amount,
            "item_name": crypto,
            "total_spent": total_spent,
            "currency": currency,
            "vendor": "Kraken",
            "transaction_id": txn_id,
            "fee_amount": fee_amount,
            "fee_currency": fee_currency,
            "extraction_method": "regex",
        }
