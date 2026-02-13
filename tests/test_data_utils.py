"""Tests for data mapping and normalization utilities."""

from __future__ import annotations

import pytest
from digital_asset_harvester.utils.data_utils import normalize_for_frontend, denormalize_from_frontend


def test_normalize_for_frontend_basic():
    purchase = {
        "total_spent": 100.0,
        "currency": "USD",
        "amount": 0.01,
        "item_name": "BTC",
        "vendor": "Coinbase",
        "purchase_date": "2023-01-01",
        "confidence": 0.95
    }

    normalized = normalize_for_frontend(purchase)

    assert normalized["amount"] == 100.0  # Should be total_spent
    assert normalized["crypto_amount"] == 0.01
    assert normalized["crypto_currency"] == "BTC"
    assert normalized["confidence_score"] == 0.95
    assert normalized["review_status"] == "pending"
    assert normalized["item_name"] == "BTC"  # Original should still be there
    assert normalized["total_spent"] == 100.0 # Original should still be there


def test_normalize_for_frontend_already_normalized():
    purchase = {
        "amount": 100.0,
        "crypto_amount": 0.01,
        "crypto_currency": "BTC",
        "review_status": "approved",
        "confidence_score": 0.95
    }

    normalized = normalize_for_frontend(purchase)

    assert normalized["amount"] == 100.0
    assert normalized["crypto_amount"] == 0.01
    assert normalized["review_status"] == "approved"
    assert normalized["confidence_score"] == 0.95


def test_denormalize_from_frontend_basic():
    purchase = {
        "amount": 100.0,  # Fiat in frontend
        "currency": "USD",
        "crypto_amount": 0.01,
        "crypto_currency": "BTC",
        "vendor": "Coinbase",
        "purchase_date": "2023-01-01",
        "confidence_score": 0.95,
        "review_status": "pending"
    }

    denormalized = denormalize_from_frontend(purchase)

    assert denormalized["total_spent"] == 100.0
    assert denormalized["amount"] == 0.01
    assert denormalized["item_name"] == "BTC"
    assert denormalized["confidence"] == 0.95


def test_denormalize_from_frontend_missing_fields():
    purchase = {
        "amount": 100.0,
        "currency": "USD"
    }

    denormalized = denormalize_from_frontend(purchase)

    assert denormalized["amount"] == 100.0 # Stays as amount if no crypto_amount
    assert "total_spent" not in denormalized # Wait, should it?
    # In my implementation:
    # if "crypto_amount" in denormalized:
    #    if "amount" in denormalized:
    #        denormalized["total_spent"] = denormalized["amount"]
    #    denormalized["amount"] = denormalized["crypto_amount"]

    # So if crypto_amount is missing, nothing happens to amount.
    # This is correct for generic records.


def test_roundtrip():
    original = {
        "total_spent": 100.0,
        "currency": "USD",
        "amount": 0.01,
        "item_name": "BTC",
        "vendor": "Coinbase",
        "purchase_date": "2023-01-01",
        "confidence": 0.95
    }

    normalized = normalize_for_frontend(original)
    denormalized = denormalize_from_frontend(normalized)

    assert denormalized["total_spent"] == original["total_spent"]
    assert denormalized["amount"] == original["amount"]
    assert denormalized["item_name"] == original["item_name"]
    assert denormalized["currency"] == original["currency"]
    assert denormalized["confidence"] == original["confidence"]
