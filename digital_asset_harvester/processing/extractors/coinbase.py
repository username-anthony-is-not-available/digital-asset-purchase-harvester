"""Specialized extractor for Coinbase emails."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseExtractor


class CoinbaseExtractor(BaseExtractor):
    """Extractor for Coinbase purchase confirmation emails."""

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a Coinbase email."""
        sender_lower = sender.lower()
        if "coinbase.com" not in sender_lower:
            return False

        subject_lower = subject.lower()
        patterns = [
            r"purchase of",
            r"you bought",
            r"you received",
            r"recent purchase",
        ]
        patterns += [r"staking reward"]
        return any(re.search(p, subject_lower) for p in patterns) or "coinbase" in sender_lower

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Coinbase email."""
        purchases = []

        # Try to find amount and crypto from subject or body
        # Pattern: "You successfully purchased 0.001 BTC for $100.00 USD."
        # Pattern: "You bought 0.5 BTC for $30,000.00 USD."
        purchase_pattern = r"(?:purchased|bought)\s+([\d,.]+)\s+([A-Z]{3,5})\s+for\s+([$€£¥])?([\d,.]+)\s*([A-Z]{3})?"
        match = re.search(purchase_pattern, body, re.IGNORECASE)

        if not match:
            # Try subject line
            # "Your Coinbase purchase of 0.001 BTC"
            subject_pattern = r"purchase of ([\d,.]+)\s+([A-Z]{3,5})"
            match_sub = re.search(subject_pattern, subject, re.IGNORECASE)
            if match_sub:
                amount = match_sub.group(1).replace(",", "")
                crypto = match_sub.group(2).upper()

                # Try to find price in body if subject matched
                price_match = re.search(r"for\s+([$€£¥])?([\d,.]+)\s*([A-Z]{3})?", body, re.IGNORECASE)
                if price_match:
                    total_spent = price_match.group(2).replace(",", "")
                    currency = price_match.group(5) or "USD"  # Default to USD if symbol found but no code
                    if not price_match.group(5) and price_match.group(1):
                        symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                        currency = symbol_map.get(price_match.group(1), "USD")
                else:
                    total_spent = None
                    currency = "USD"

                purchases.append(self._create_purchase_dict(amount, crypto, total_spent, currency, body))
        else:
            amount = match.group(1).replace(",", "")
            crypto = match.group(2).upper()
            total_spent = match.group(4).replace(",", "")

            currency = match.group(5)
            if not currency and match.group(3):
                symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                currency = symbol_map.get(match.group(3), "USD")
            if not currency:
                currency = "USD"

            purchases.append(self._create_purchase_dict(amount, crypto, total_spent, currency, body))

        # Handle Staking Rewards
        if not purchases and "staking reward" in body.lower():
            # Pattern: "You just earned 0.00001234 ETH in staking rewards!"
            match = re.search(
                r"(?:earned|received)\s+([\d,.]+)\s+([A-Z]{3,5})\s+in\s+staking rewards", body, re.IGNORECASE
            )
            if match:
                amount = match.group(1).replace(",", "")
                crypto = match.group(2).upper()
                purchase = self._create_purchase_dict(amount, crypto, None, "USD", body)
                purchase["transaction_type"] = "staking_reward"
                purchases.append(purchase)

        return purchases

    def _create_purchase_dict(
        self, amount: str, crypto: str, total_spent: str | None, currency: str, body: str
    ) -> Dict[str, Any]:
        # Extract transaction ID
        txn_id = self._find_match(r"Transaction ID:\s*([A-Z0-9\-]+)", body)

        # Extract fee
        fee_amount = None
        fee_currency = currency
        fee_match = re.search(r"(?:fee of|Coinbase Fee)\s*([$€£¥])?([\d,.]+)\s*([A-Z]{3})?", body, re.IGNORECASE)
        if fee_match:
            fee_amount = fee_match.group(2).replace(",", "")
            if fee_match.group(3):
                fee_currency = fee_match.group(3)

        return {
            "amount": amount,
            "item_name": crypto,
            "total_spent": total_spent,
            "currency": currency,
            "vendor": "Coinbase",
            "transaction_id": txn_id,
            "fee_amount": fee_amount,
            "fee_currency": fee_currency,
            "extraction_method": "regex",
        }
