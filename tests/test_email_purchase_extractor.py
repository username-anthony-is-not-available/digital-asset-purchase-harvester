"""Tests for the EmailPurchaseExtractor component."""

from __future__ import annotations

import pytest

from digital_asset_harvester import get_settings_with_overrides
from tests.fixtures.emails import EMAIL_FIXTURES


@pytest.fixture
def settings_with_preprocessing_disabled():
    """Returns settings with preprocessing disabled."""
    return get_settings_with_overrides(enable_preprocessing=False)


@pytest.fixture
def extractor_factory_no_preprocessing(
    settings_with_preprocessing_disabled, extractor_factory
):
    """Returns an extractor factory with preprocessing disabled."""

    def _factory(responses):
        extractor = extractor_factory(responses)
        extractor.settings = settings_with_preprocessing_disabled
        return extractor

    return _factory


def test_is_crypto_purchase_email_positive(extractor_factory_no_preprocessing):
    # Keep the no-preprocessing fixture to ensure the classifier is tested in isolation
    email_content = "Subject: Coinbase receipt\nFrom: no-reply@coinbase.com\nBody: You bought 0.1 BTC"

    responses = [
        {
            "is_crypto_purchase": True,
            "confidence": 0.9,
            "reasoning": "Direct purchase confirmation",
        }
    ]

    extractor = extractor_factory_no_preprocessing(responses)
    assert extractor.is_crypto_purchase_email(email_content) is True


def test_is_crypto_purchase_email_low_confidence(extractor_factory_no_preprocessing):
    email_content = "Subject: Coinbase receipt\nFrom: no-reply@coinbase.com\nBody: You bought 0.1 BTC"
    responses = [
        {
            "is_crypto_purchase": True,
            "confidence": 0.4,
            "reasoning": "Uncertain",
        }
    ]

    extractor = extractor_factory_no_preprocessing(responses)
    assert extractor.is_crypto_purchase_email(email_content) is False


def test_extract_purchase_info_success(extractor_factory_no_preprocessing):
    email_content = "Subject: Binance trade\nBody: Amount: 0.25 ETH Total: $500"
    responses = [
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

    extractor = extractor_factory_no_preprocessing(responses)
    result = extractor.extract_purchase_info(email_content)

    assert result == {
        "total_spent": 500.0,
        "currency": "USD",
        "amount": 0.25,
        "item_name": "ETH",
        "vendor": "Binance",
        "purchase_date": "2024-01-01 12:00:00 UTC",
    }


def test_extract_purchase_info_missing_fields_strict(
    extractor_factory_no_preprocessing,
):
    email_content = "Subject: Binance trade\nBody: Amount: 0.25 ETH Total: $500"
    responses = [
        {
            "total_spent": 500.0,
            "currency": "USD",
            "amount": 0.25,
            "confidence": 0.9,
            "extraction_notes": "",
        }
    ]

    extractor = extractor_factory_no_preprocessing(responses)
    assert extractor.extract_purchase_info(email_content) is None


def test_process_email_successful_path(extractor_factory, monkeypatch):
    email_content = "Subject: Coinbase\nFrom: no-reply@coinbase.com\nBody: You bought 0.05 BTC"
    responses = [
        {
            "is_crypto_purchase": True,
            "confidence": 0.9,
            "reasoning": "Purchase confirmed",
        },
        {
            "total_spent": 1000.0,
            "currency": "USD",
            "amount": 0.05,
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-02-02 10:10:10",
            "confidence": 0.9,
            "extraction_notes": "",
        },
    ]

    extractor = extractor_factory(responses)
    # Ensure preprocessing doesn't filter the email in this test
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)

    result = extractor.process_email(email_content)

    assert result["has_purchase"] is True
    assert result["purchase_info"]["vendor"] == "Coinbase"
    assert "Successfully extracted" in result["processing_notes"][0]


def test_process_email_filtered_by_preprocessing(extractor_factory):
    # This email shouldn't pass preprocessing because it lacks crypto terms
    email_content = "Subject: Dinner order\nFrom: restaurant@example.com\nBody: Your order has shipped"

    extractor = extractor_factory([])
    result = extractor.process_email(email_content)

    assert result == {
        "has_purchase": False,
        "processing_notes": ["Email not classified as crypto purchase"],
    }


def test_process_email_with_coinbase_fixture(extractor_factory, monkeypatch):
    email_content = EMAIL_FIXTURES["coinbase_purchase"]
    responses = [
        {
            "is_crypto_purchase": True,
            "confidence": 0.9,
            "reasoning": "Purchase confirmed",
        },
        {
            "total_spent": 100.0,
            "currency": "USD",
            "amount": 0.001,
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-01 12:00:00",
            "confidence": 0.9,
            "extraction_notes": "",
        },
    ]

    extractor = extractor_factory(responses)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)

    result = extractor.process_email(email_content)

    assert result["has_purchase"] is True
    assert result["purchase_info"]["vendor"] == "Coinbase"


def test_process_email_with_binance_fixture(extractor_factory, monkeypatch):
    email_content = EMAIL_FIXTURES["binance_purchase"]
    responses = [
        {
            "is_crypto_purchase": True,
            "confidence": 0.9,
            "reasoning": "Purchase confirmed",
        },
        {
            "total_spent": 200.0,
            "currency": "USD",
            "amount": 0.1,
            "item_name": "ETH",
            "vendor": "Binance",
            "purchase_date": "2024-01-02 12:00:00",
            "confidence": 0.9,
            "extraction_notes": "",
        },
    ]

    extractor = extractor_factory(responses)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)

    result = extractor.process_email(email_content)

    assert result["has_purchase"] is True
    assert result["purchase_info"]["vendor"] == "Binance"


def test_process_email_with_non_purchase_fixture(extractor_factory, monkeypatch):
    email_content = EMAIL_FIXTURES["non_purchase"]
    responses = [
        {
            "is_crypto_purchase": False,
            "confidence": 0.9,
            "reasoning": "Price alert",
        }
    ]

    extractor = extractor_factory(responses)
    monkeypatch.setattr(extractor, "_should_skip_llm_analysis", lambda x: False)
    monkeypatch.setattr(extractor, "_is_likely_crypto_related", lambda x: True)
    monkeypatch.setattr(extractor, "_is_likely_purchase_related", lambda x: True)

    result = extractor.process_email(email_content)

    assert result["has_purchase"] is False
