"""Tests for the EmailPurchaseExtractor component."""

from __future__ import annotations

import pytest

from digital_asset_harvester import get_settings_with_overrides
from tests.fixtures.emails import EMAIL_FIXTURES


def test_is_crypto_purchase_email_positive(mocker):
    email_content = "Subject: Coinbase receipt\nFrom: no-reply@coinbase.com\nBody: You bought 0.1 BTC"
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.return_value = mocker.Mock(
        data={
            "is_crypto_purchase": True,
            "confidence": 0.9,
            "reasoning": "Direct purchase confirmation",
        }
    )
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    settings = get_settings_with_overrides(enable_preprocessing=False)
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)
    assert extractor.is_crypto_purchase_email(email_content) is True


def test_is_crypto_purchase_email_low_confidence(mocker):
    email_content = "Subject: Coinbase receipt\nFrom: no-reply@coinbase.com\nBody: You bought 0.1 BTC"
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.return_value = mocker.Mock(
        data={"is_crypto_purchase": True, "confidence": 0.4, "reasoning": "Uncertain"}
    )
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    settings = get_settings_with_overrides(enable_preprocessing=False)
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)
    assert extractor.is_crypto_purchase_email(email_content) is False


def test_extract_purchase_info_success(mocker):
    email_content = "Subject: Binance trade\nBody: Amount: 0.25 ETH Total: $500"
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.return_value = mocker.Mock(
        data={
            "transactions": [
                {
                    "total_spent": 500.0,
                    "currency": "USD",
                    "amount": 0.25,
                    "item_name": "ETH",
                    "vendor": "Binance",
                    "purchase_date": "2024-01-01 12:00:00",
                    "confidence": 0.9,
                    "extraction_notes": "",
                }
            ]
        }
    )
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    settings = get_settings_with_overrides(enable_preprocessing=False)
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)
    result = extractor.extract_purchase_info(email_content)
    assert len(result) == 1
    assert result[0] == {
        "total_spent": 500.0,
        "currency": "USD",
        "amount": 0.25,
        "item_name": "ETH",
        "vendor": "Binance",
        "purchase_date": "2024-01-01 12:00:00 UTC",
        "confidence": 0.9,
        "extraction_notes": "",
        "extraction_method": "llm",
    }


def test_extract_purchase_info_missing_fields_strict(mocker):
    email_content = "Subject: Binance trade\nBody: Amount: 0.25 ETH Total: $500"
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.return_value = mocker.Mock(
        data={
            "transactions": [
                {
                    "total_spent": 500.0,
                    "currency": "USD",
                    "amount": 0.25,
                    "confidence": 0.9,
                    "extraction_notes": "",
                }
            ]
        }
    )
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    settings = get_settings_with_overrides(enable_preprocessing=False, strict_validation=True)
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)
    assert extractor.extract_purchase_info(email_content) == []


def test_process_email_successful_path(mocker, monkeypatch):
    email_content = "Subject: Coinbase\nFrom: no-reply@coinbase.com\nBody: You bought 0.05 BTC"
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.side_effect = [
        mocker.Mock(
            data={
                "is_crypto_purchase": True,
                "confidence": 0.9,
                "reasoning": "Purchase confirmed",
            }
        ),
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "total_spent": 1000.0,
                        "currency": "USD",
                        "amount": 0.05,
                        "item_name": "BTC",
                        "vendor": "Coinbase",
                        "purchase_date": "2024-02-02 10:10:10",
                        "confidence": 0.9,
                        "extraction_notes": "",
                    }
                ]
            }
        ),
    ]
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    settings = get_settings_with_overrides(enable_regex_extractors=False)
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)
    result = extractor.process_email(email_content)
    assert result["has_purchase"] is True
    assert len(result["purchases"]) == 1
    assert result["purchases"][0]["vendor"] == "Coinbase"
    assert "Successfully extracted" in result["processing_notes"][0]


def test_process_email_filtered_by_preprocessing(mocker):
    email_content = "Subject: Dinner order\nFrom: restaurant@example.com\nBody: Your order has shipped"
    mocker.patch("digital_asset_harvester.processing.email_purchase_extractor.get_llm_client")
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    extractor = EmailPurchaseExtractor()
    result = extractor.process_email(email_content)
    assert result["has_purchase"] is False
    assert result["purchases"] == []
    assert "Email not classified as crypto purchase" in result["processing_notes"][0]


def test_process_email_with_coinbase_fixture(mocker, monkeypatch):
    email_content = EMAIL_FIXTURES["coinbase_purchase"]
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.side_effect = [
        mocker.Mock(
            data={
                "is_crypto_purchase": True,
                "confidence": 0.9,
                "reasoning": "Purchase confirmed",
            }
        ),
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "total_spent": 100.0,
                        "currency": "USD",
                        "amount": 0.001,
                        "item_name": "BTC",
                        "vendor": "Coinbase",
                        "purchase_date": "2024-01-01 12:00:00",
                        "confidence": 0.9,
                        "extraction_notes": "",
                    }
                ]
            }
        ),
    ]
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    settings = get_settings_with_overrides(enable_regex_extractors=False)
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)
    result = extractor.process_email(email_content)
    assert result["has_purchase"] is True
    assert result["purchases"][0]["vendor"] == "Coinbase"


def test_process_email_with_binance_fixture(mocker, monkeypatch):
    email_content = EMAIL_FIXTURES["binance_purchase"]
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.side_effect = [
        mocker.Mock(
            data={
                "is_crypto_purchase": True,
                "confidence": 0.9,
                "reasoning": "Purchase confirmed",
            }
        ),
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "total_spent": 200.0,
                        "currency": "USD",
                        "amount": 0.1,
                        "item_name": "ETH",
                        "vendor": "Binance",
                        "purchase_date": "2024-01-02 12:00:00",
                        "confidence": 0.9,
                        "extraction_notes": "",
                    }
                ]
            }
        ),
    ]
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    extractor = EmailPurchaseExtractor(llm_client=mock_llm_client)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)
    result = extractor.process_email(email_content)
    assert result["has_purchase"] is True
    assert result["purchases"][0]["vendor"] == "Binance"


def test_process_email_with_non_purchase_fixture(mocker, monkeypatch):
    email_content = EMAIL_FIXTURES["non_purchase"]
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.return_value = mocker.Mock(
        data={
            "is_crypto_purchase": False,
            "confidence": 0.9,
            "reasoning": "Price alert",
        }
    )
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    extractor = EmailPurchaseExtractor(llm_client=mock_llm_client)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)
    result = extractor.process_email(email_content)
    assert result["has_purchase"] is False


def test_process_email_with_binance_deposit_fixture(mocker, monkeypatch):
    email_content = EMAIL_FIXTURES["binance_deposit"]
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.side_effect = [
        mocker.Mock(
            data={
                "is_crypto_purchase": True,
                "confidence": 0.9,
                "reasoning": "Deposit confirmed",
            }
        ),
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "transaction_type": "deposit",
                        "total_spent": None,
                        "currency": None,
                        "amount": 0.1,
                        "item_name": "BTC",
                        "vendor": "Binance",
                        "purchase_date": "2024-01-02 12:00:00",
                        "confidence": 0.9,
                        "extraction_notes": "",
                    }
                ]
            }
        ),
    ]
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    extractor = EmailPurchaseExtractor(llm_client=mock_llm_client)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)
    result = extractor.process_email(email_content)
    assert result["has_purchase"] is True
    assert result["purchases"][0]["vendor"] == "Binance"
    assert result["purchases"][0]["amount"] == 0.1
    assert result["purchases"][0]["item_name"] == "BTC"


def test_process_email_with_binance_withdrawal_fixture(mocker, monkeypatch):
    email_content = EMAIL_FIXTURES["binance_withdrawal"]
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.side_effect = [
        mocker.Mock(
            data={
                "is_crypto_purchase": True,
                "confidence": 0.9,
                "reasoning": "Withdrawal confirmed",
            }
        ),
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "transaction_type": "withdrawal",
                        "total_spent": None,
                        "currency": None,
                        "amount": 0.5,
                        "item_name": "ETH",
                        "vendor": "Binance",
                        "purchase_date": "2024-01-02 12:00:00",
                        "confidence": 0.9,
                        "extraction_notes": "",
                    }
                ]
            }
        ),
    ]
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    extractor = EmailPurchaseExtractor(llm_client=mock_llm_client)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)
    result = extractor.process_email(email_content)
    assert result["has_purchase"] is True
    assert result["purchases"][0]["vendor"] == "Binance"
    assert result["purchases"][0]["amount"] == 0.5
    assert result["purchases"][0]["item_name"] == "ETH"


def test_process_email_with_coinbase_staking_reward(mocker, monkeypatch):
    email_content = EMAIL_FIXTURES["coinbase_staking_reward"]
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.side_effect = [
        mocker.Mock(
            data={
                "is_crypto_purchase": True,
                "confidence": 0.9,
                "reasoning": "Staking reward earned",
            }
        ),
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "transaction_type": "staking_reward",
                        "total_spent": None,
                        "currency": None,
                        "amount": 0.00001234,
                        "item_name": "ETH",
                        "vendor": "Coinbase",
                        "purchase_date": "2025-01-01 12:00:00",
                        "transaction_id": "CB-STAKE-2025-ABC",
                        "confidence": 0.9,
                        "extraction_notes": "",
                    }
                ]
            }
        ),
    ]
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    extractor = EmailPurchaseExtractor(llm_client=mock_llm_client)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)
    result = extractor.process_email(email_content)
    assert result["has_purchase"] is True
    assert result["purchases"][0]["transaction_type"] == "staking_reward"
    assert result["purchases"][0]["amount"] == 0.00001234
    assert result["purchases"][0]["transaction_id"] == "CB-STAKE-2025-ABC"


def test_process_email_with_binance_staking_reward(mocker, monkeypatch):
    email_content = EMAIL_FIXTURES["binance_staking_reward"]
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.side_effect = [
        mocker.Mock(
            data={
                "is_crypto_purchase": True,
                "confidence": 0.9,
                "reasoning": "Distribution confirmation",
            }
        ),
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "transaction_type": "staking_reward",
                        "total_spent": None,
                        "currency": None,
                        "amount": 0.5,
                        "item_name": "SOL",
                        "vendor": "Binance",
                        "purchase_date": "2025-01-01 12:00:00",
                        "transaction_id": "BIN-STAKE-2025-XYZ",
                        "confidence": 0.9,
                        "extraction_notes": "",
                    }
                ]
            }
        ),
    ]
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    extractor = EmailPurchaseExtractor(llm_client=mock_llm_client)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)
    result = extractor.process_email(email_content)
    assert result["has_purchase"] is True
    assert result["purchases"][0]["transaction_type"] == "staking_reward"
    assert result["purchases"][0]["amount"] == 0.5
    assert result["purchases"][0]["transaction_id"] == "BIN-STAKE-2025-XYZ"


def test_process_email_with_kraken_staking_reward(mocker, monkeypatch):
    email_content = EMAIL_FIXTURES["kraken_staking_reward"]
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.side_effect = [
        mocker.Mock(
            data={
                "is_crypto_purchase": True,
                "confidence": 0.9,
                "reasoning": "Staking reward received",
            }
        ),
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "transaction_type": "staking_reward",
                        "total_spent": None,
                        "currency": None,
                        "amount": 10.5,
                        "item_name": "ADA",
                        "vendor": "Kraken",
                        "purchase_date": "2025-01-01 12:00:00",
                        "transaction_id": "KR-STAKE-2025-999",
                        "confidence": 0.9,
                        "extraction_notes": "",
                    }
                ]
            }
        ),
    ]
    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    extractor = EmailPurchaseExtractor(llm_client=mock_llm_client)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)
    result = extractor.process_email(email_content)
    assert result["has_purchase"] is True
    assert result["purchases"][0]["transaction_type"] == "staking_reward"
    assert result["purchases"][0]["amount"] == 10.5
    assert result["purchases"][0]["transaction_id"] == "KR-STAKE-2025-999"


def test_process_email_with_currency_conversion(mocker, monkeypatch):
    email_content = "Subject: Coinbase\nBody: You bought 0.05 BTC for 1000 USD"
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.side_effect = [
        mocker.Mock(data={"is_crypto_purchase": True, "confidence": 1.0}),
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "total_spent": 1000.0,
                        "currency": "USD",
                        "amount": 0.05,
                        "item_name": "BTC",
                        "vendor": "Coinbase",
                        "purchase_date": "2024-01-01 12:00:00",
                        "confidence": 1.0,
                    }
                ]
            }
        ),
    ]

    mock_fx_service = mocker.patch("digital_asset_harvester.processing.email_purchase_extractor.fx_service")
    from decimal import Decimal

    mock_fx_service.get_rate.return_value = Decimal("1.35")

    from digital_asset_harvester.processing.email_purchase_extractor import (
        EmailPurchaseExtractor,
    )

    settings = get_settings_with_overrides(
        enable_regex_extractors=False, enable_currency_conversion=True, base_fiat_currency="CAD"
    )
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)

    result = extractor.process_email(email_content)
    assert result["has_purchase"] is True
    assert result["purchases"][0]["fiat_amount_cad"] == 1350.0
    mock_fx_service.get_rate.assert_called_once_with("2024-01-01 12:00:00 UTC", "USD", "CAD")
