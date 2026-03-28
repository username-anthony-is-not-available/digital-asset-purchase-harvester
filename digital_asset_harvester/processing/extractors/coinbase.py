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

        # 1. Look for standard buy patterns in body (find all for multi-purchase)
        # Pattern: "You successfully purchased 0.001 BTC for $100.00 USD."
        # Pattern: "You bought 0.5 BTC for $30,000.00 USD."
        # Pattern: "Your order to buy 0.05 BTC for $3,000.00 USD has been completed."
        buy_patterns = [
            r"(?:purchased|bought|buy)\s+([\d,.]+)\s+([A-Z]{3,5})\s+for\s+([$€£¥])?([\d,.]+)\s*([A-Z]{3})?",
            r"purchased\s+([$€£¥])?([\d,.]+)\s+of\s+([A-Z]{3,5})",
        ]

        for pattern in buy_patterns:
            for match in re.finditer(pattern, body, re.IGNORECASE):
                if "of" in pattern:
                    # purchased $100 of BTC
                    amount = None
                    crypto = match.group(3).upper()
                    total_spent = match.group(2).replace(",", "")
                    currency_symbol = match.group(1)
                    currency = "USD"
                    if currency_symbol:
                        symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                        currency = symbol_map.get(currency_symbol, "USD")
                else:
                    # bought 0.1 BTC for $100
                    amount = match.group(1).replace(",", "")
                    crypto = match.group(2).upper()
                    total_spent = match.group(4).replace(",", "")
                    currency = match.group(5)
                    if not currency and match.group(3):
                        symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                        currency = symbol_map.get(match.group(3), "USD")
                    if not currency:
                        currency = "USD"

                purchases.append(
                    self._create_purchase_dict(amount, crypto, total_spent, currency, body, "buy")
                )

        # 2. Try subject line if nothing found in body
        if not purchases:
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
                    currency = price_match.group(5) or "USD"
                    if not price_match.group(5) and price_match.group(1):
                        symbol_map = {"$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY"}
                        currency = symbol_map.get(price_match.group(1), "USD")
                else:
                    total_spent = None
                    currency = "USD"

                purchases.append(
                    self._create_purchase_dict(amount, crypto, total_spent, currency, body, "buy")
                )

        # 3. Handle Staking Rewards
        if "staking reward" in body.lower() or "staking reward" in subject.lower():
            # Pattern: "You just earned 0.00001234 ETH in staking rewards!"
            for match in re.finditer(
                r"(?:earned|received)\s+([\d,.]+)\s+([A-Z]{3,5})\s+in\s+staking rewards", body, re.IGNORECASE
            ):
                amount = match.group(1).replace(",", "")
                crypto = match.group(2).upper()
                purchases.append(
                    self._create_purchase_dict(amount, crypto, None, "USD", body, "staking_reward")
                )

        return purchases

    def _create_purchase_dict(
        self,
        amount: str | None,
        crypto: str,
        total_spent: str | None,
        currency: str,
        body: str,
        transaction_type: str = "buy",
    ) -> Dict[str, Any]:
        # Extract transaction ID
        txn_id = self._find_match(r"(?:Transaction ID|Order\s*#):\s*([A-Z0-9\-]+)", body)

        # Extract fee
        fee_amount = None
        fee_currency = currency
        fee_match = re.search(
            r"(?:fee of|Coinbase Fee)\s*([$€£¥])?([\d,.]+)\s*([A-Z]{3})?", body, re.IGNORECASE
        )
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
            "transaction_type": transaction_type,
            "fee_amount": fee_amount,
            "fee_currency": fee_currency,
            "extraction_method": "regex",
        }
