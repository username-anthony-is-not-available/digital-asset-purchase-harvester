"""Specialized extractor for Binance emails."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .base import BaseExtractor


class BinanceExtractor(BaseExtractor):
    """Extractor for Binance trade confirmation emails."""

    def can_handle(self, subject: str, sender: str, body: str) -> bool:
        """Check if this is a Binance email."""
        sender_lower = sender.lower()
        if "binance.com" not in sender_lower:
            return False

        subject_lower = subject.lower()
        patterns = [
            r"trade confirmation",
            r"order to buy",
            r"order execution",
            r"filled",
            r"deposit successful",
            r"withdrawal successful",
            r"distribution confirmation",
        ]
        return any(re.search(p, subject_lower) for p in patterns)

    def extract(self, subject: str, sender: str, body: str) -> List[Dict[str, Any]]:
        """Extract data from Binance email."""
        purchases = []

        # Handle structured "Order Details" block
        if "Order Details:" in body or "Details:" in body:
            # Split by blocks if multi-asset
            blocks = re.split(r"\n\s*\n", body)
            for block in blocks:
                if "Amount:" in block and ("Price:" in block or "Total:" in block or "Total Cost:" in block):
                    amount = self._find_match(r"Amount:\s*([\d,.]+)\s*([A-Z0-9]+)?", block, 1)
                    crypto = self._find_match(r"Amount:\s*[\d,.]+\s*([A-Z0-9]+)", block, 1)

                    if not crypto:
                         # Try to find from Pair if available
                         pair = self._find_match(r"Pair:\s*([A-Z0-9]+)/", block, 1) or self._find_match(r"Trading Pair:\s*([A-Z0-9]+)/", block, 1)
                         if pair:
                             crypto = pair

                    total_spent = self._find_match(r"(?:Total|Total Cost):\s*([\d,.]+)", block, 1)
                    currency = self._find_match(r"(?:Total|Total Cost):\s*[\d,.]+\s*([A-Z0-9]+)", block, 1)

                    if not currency:
                        # Try to find from Price
                        currency = self._find_match(r"Price:\s*[\d,.]+\s*([A-Z0-9]+)", block, 1)

                    if amount and crypto:
                        purchases.append(self._create_purchase_dict(
                            amount.replace(",", ""),
                            crypto.upper(),
                            total_spent.replace(",", "") if total_spent else None,
                            currency.upper() if currency else "USDT",
                            block,
                            body
                        ))

        # Handle simple one-liner
        # "Your order to buy 0.1 ETH for 200.00 USD has been filled."
        if not purchases:
            match = re.search(r"buy\s+([\d,.]+)\s+([A-Z]{3,5})\s+for\s+([\d,.]+)\s+([A-Z]{3,5})", body, re.IGNORECASE)
            if match:
                purchases.append(self._create_purchase_dict(
                    match.group(1).replace(",", ""),
                    match.group(2).upper(),
                    match.group(3).replace(",", ""),
                    match.group(4).upper(),
                    body,
                    body
                ))

        # Handle Staking Rewards
        # "Your account has been credited with 0.5 SOL for SOL Staking."
        if not purchases and "Staking" in body:
            match = re.search(r"credited with\s+([\d,.]+)\s+([A-Z]{3,5})", body, re.IGNORECASE)
            if match:
                purchase = self._create_purchase_dict(
                    match.group(1).replace(",", ""),
                    match.group(2).upper(),
                    None,
                    "",
                    body,
                    body
                )
                purchase["transaction_type"] = "staking_reward"
                purchases.append(purchase)

        # Handle Deposits/Withdrawals
        if not purchases and ("deposited" in body.lower() or "withdrawn" in body.lower()):
            match = re.search(r"(?:deposited|withdrawn)\s+([\d,.]+)\s+([A-Z]{3,5})", body, re.IGNORECASE)
            if match:
                purchase = self._create_purchase_dict(
                    match.group(1).replace(",", ""),
                    match.group(2).upper(),
                    None,
                    "",
                    body,
                    body
                )
                purchase["transaction_type"] = "deposit" if "deposited" in body.lower() else "withdrawal"
                purchases.append(purchase)

        return purchases

    def _create_purchase_dict(self, amount: str, crypto: str, total_spent: str | None, currency: str, context: str, full_body: str = "") -> Dict[str, Any]:
        # Extract transaction ID or Reference - try context first, then full body
        txn_id = self._find_match(r"(?:Transaction ID|Reference|Order\s*#)\s*:?\s*([A-Z0-9#\-]+)", context)
        if not txn_id and full_body:
            txn_id = self._find_match(r"(?:Transaction ID|Reference|Order\s*#)\s*:?\s*([A-Z0-9#\-]+)", full_body)

        # Extract fee from context, fall back to full body
        fee_amount = self._find_match(r"Fee:\s*([\d,.]+)", context)
        fee_currency = self._find_match(r"Fee:\s*[\d,.]+\s*([A-Z0-9]+)", context)

        if not fee_amount and full_body:
            fee_amount = self._find_match(r"Fee:\s*([\d,.]+)", full_body)
            fee_currency = self._find_match(r"Fee:\s*[\d,.]+\s*([A-Z0-9]+)", full_body)

        return {
            "amount": amount,
            "item_name": crypto,
            "total_spent": total_spent,
            "currency": currency,
            "vendor": "Binance",
            "transaction_id": txn_id,
            "fee_amount": fee_amount.replace(",", "") if fee_amount else None,
            "fee_currency": fee_currency.upper() if fee_currency else None,
            "extraction_method": "regex",
        }
