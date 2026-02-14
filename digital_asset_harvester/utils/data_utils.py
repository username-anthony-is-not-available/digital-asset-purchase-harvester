"""Utility functions for data mapping and normalization."""

from __future__ import annotations

from typing import Any, Dict


def normalize_for_frontend(purchase: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map backend/LLM fields to frontend-compatible fields.

    LLM returns: total_spent (fiat), amount (crypto), item_name (crypto)
    Frontend expects: amount (fiat), crypto_amount (crypto), crypto_currency (crypto)
    """
    normalized = purchase.copy()

    # Initialize review status if missing
    if "review_status" not in normalized:
        normalized["review_status"] = "pending"

    # Map confidence scores
    if "confidence" in normalized and "confidence_score" not in normalized:
        normalized["confidence_score"] = normalized["confidence"]

    # Ensure item_name and amount are mapped for frontend
    if "item_name" in normalized and "crypto_currency" not in normalized:
        normalized["crypto_currency"] = normalized["item_name"]

    if "amount" in normalized and "crypto_amount" not in normalized:
        # Note: The LLM 'amount' is actually the crypto amount.
        # But in the existing UI, 'amount' was used for fiat.
        normalized["crypto_amount"] = normalized["amount"]
        if "total_spent" in normalized:
            normalized["amount"] = normalized["total_spent"]

    # Handle fees (already use backend names in frontend for these)
    if "fee_amount" not in normalized:
        normalized["fee_amount"] = None
    if "fee_currency" not in normalized:
        normalized["fee_currency"] = ""

    if "asset_id" not in normalized:
        normalized["asset_id"] = None

    return normalized


def denormalize_from_frontend(purchase: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map frontend fields back to backend/exporter compatible fields.

    Frontend has: amount (fiat), crypto_amount (crypto), crypto_currency (crypto)
    Backend/Exporters expect: total_spent (fiat), amount (crypto), item_name (crypto)
    """
    denormalized = purchase.copy()

    # Restore item_name
    if "crypto_currency" in denormalized:
        denormalized["item_name"] = denormalized["crypto_currency"]

    # Restore amounts
    if "crypto_amount" in denormalized:
        # Before we overwrite 'amount', check if it was used for fiat
        # In frontend, 'amount' is fiat.
        if "amount" in denormalized:
            denormalized["total_spent"] = denormalized["amount"]

        # Restore crypto amount to its original key
        denormalized["amount"] = denormalized["crypto_amount"]

    # Restore confidence
    if "confidence_score" in denormalized:
        denormalized["confidence"] = denormalized["confidence_score"]

    # Ensure asset_id is preserved
    if "asset_id" in denormalized:
        # already has the right key
        pass

    return denormalized
