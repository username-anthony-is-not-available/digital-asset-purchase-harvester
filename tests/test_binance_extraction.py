"""Tests for Binance-specific extraction improvements."""

from __future__ import annotations

import pytest

from digital_asset_harvester import get_settings_with_overrides
from digital_asset_harvester.processing.email_purchase_extractor import EmailPurchaseExtractor
from tests.fixtures.emails import EMAIL_FIXTURES


def test_extract_binance_multi_asset(mocker, monkeypatch):
    """Test that multiple assets are correctly extracted from a Binance trade confirmation."""
    email_content = EMAIL_FIXTURES["binance_multi_asset"]

    # Mock the LLM to return two transactions as expected from the new prompt
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.side_effect = [
        # Classification
        mocker.Mock(data={"is_crypto_purchase": True, "confidence": 0.95, "reasoning": "Trade confirmation"}),
        # Extraction
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "transaction_type": "buy",
                        "total_spent": 130.0,
                        "currency": "USDT",
                        "amount": 0.002,
                        "item_name": "BTC",
                        "vendor": "Binance",
                        "purchase_date": "2024-03-20 14:00:00",
                        "confidence": 0.95,
                    },
                    {
                        "transaction_type": "buy",
                        "total_spent": 350.0,
                        "currency": "USDT",
                        "amount": 0.1,
                        "item_name": "ETH",
                        "vendor": "Binance",
                        "purchase_date": "2024-03-20 14:00:00",
                        "confidence": 0.95,
                    },
                ]
            }
        ),
    ]

    settings = get_settings_with_overrides(enable_preprocessing=False)
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)

    result = extractor.process_email(email_content)

    assert result["has_purchase"] is True
    assert len(result["purchases"]) == 2

    # Check first purchase
    assert result["purchases"][0]["item_name"] == "BTC"
    assert result["purchases"][0]["amount"] == 0.002
    assert result["purchases"][0]["total_spent"] == 130.0

    # Check second purchase
    assert result["purchases"][1]["item_name"] == "ETH"
    assert result["purchases"][1]["amount"] == 0.1
    assert result["purchases"][1]["total_spent"] == 350.0


def test_extract_binance_order_execution(mocker):
    """Test extraction from Binance Order Execution Notice."""
    email_content = EMAIL_FIXTURES["binance_order_execution"]

    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.side_effect = [
        # Classification
        mocker.Mock(data={"is_crypto_purchase": True, "confidence": 0.95, "reasoning": "Order execution notice"}),
        # Extraction
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "transaction_type": "buy",
                        "total_spent": 900.0,
                        "currency": "USDT",
                        "amount": 5.0,
                        "item_name": "SOL",
                        "vendor": "Binance",
                        "purchase_date": "2024-03-21 09:15:00",
                        "transaction_id": "987654321",
                        "confidence": 0.95,
                    }
                ]
            }
        ),
    ]

    settings = get_settings_with_overrides(enable_preprocessing=False)
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)

    result = extractor.process_email(email_content)

    assert result["has_purchase"] is True
    assert len(result["purchases"]) == 1
    assert result["purchases"][0]["item_name"] == "SOL"
    assert result["purchases"][0]["amount"] == 5.0
    assert result["purchases"][0]["transaction_id"] == "987654321"
