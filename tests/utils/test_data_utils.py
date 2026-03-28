import pytest

from digital_asset_harvester.utils.data_utils import denormalize_from_frontend, normalize_for_frontend


def test_normalize_for_frontend():
    purchase = {
        "total_spent": 100.0,
        "amount": 0.001,
        "item_name": "BTC",
        "confidence": 0.9,
        "fee_amount": 1.0,
        "fee_currency": "USD",
    }

    normalized = normalize_for_frontend(purchase)

    assert normalized["review_status"] == "pending"
    assert normalized["confidence_score"] == 0.9
    assert normalized["crypto_currency"] == "BTC"
    assert normalized["crypto_amount"] == 0.001
    assert normalized["amount"] == 100.0
    assert normalized["fee_amount"] == 1.0
    assert normalized["fee_currency"] == "USD"
    assert normalized["asset_id"] is None
    assert normalized["fiat_amount_base"] is None


def test_normalize_for_frontend_empty():
    normalized = normalize_for_frontend({})
    assert normalized["review_status"] == "pending"
    assert normalized["fee_amount"] is None
    assert normalized["fee_currency"] == ""


def test_denormalize_from_frontend():
    frontend_data = {
        "amount": 100.0,
        "crypto_amount": 0.001,
        "crypto_currency": "BTC",
        "confidence_score": 0.9,
        "asset_id": "bitcoin",
    }

    denormalized = denormalize_from_frontend(frontend_data)

    assert denormalized["item_name"] == "BTC"
    assert denormalized["total_spent"] == 100.0
    assert denormalized["amount"] == 0.001
    assert denormalized["confidence"] == 0.9
    assert denormalized["asset_id"] == "bitcoin"
