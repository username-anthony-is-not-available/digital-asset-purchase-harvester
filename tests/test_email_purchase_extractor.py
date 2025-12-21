"""Tests for the EmailPurchaseExtractor component."""

from __future__ import annotations


def test_is_crypto_purchase_email_positive(extractor_factory):
    email_content = "Subject: Coinbase receipt\nFrom: no-reply@coinbase.com\nBody: You bought 0.1 BTC"
    responses = [
        {
            "is_crypto_purchase": True,
            "confidence": 0.9,
            "reasoning": "Direct purchase confirmation",
        }
    ]

    extractor = extractor_factory(responses)
    assert extractor.is_crypto_purchase_email(email_content) is True


def test_is_crypto_purchase_email_low_confidence(extractor_factory):
    email_content = "Subject: Coinbase receipt\nFrom: no-reply@coinbase.com\nBody: You bought 0.1 BTC"
    responses = [
        {
            "is_crypto_purchase": True,
            "confidence": 0.4,
            "reasoning": "Uncertain",
        }
    ]

    extractor = extractor_factory(responses)
    assert extractor.is_crypto_purchase_email(email_content) is False


def test_extract_purchase_info_success(extractor_factory):
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

    extractor = extractor_factory(responses)
    result = extractor.extract_purchase_info(email_content)

    assert result == {
        "total_spent": 500.0,
        "currency": "USD",
        "amount": 0.25,
        "item_name": "ETH",
        "vendor": "Binance",
        "purchase_date": "2024-01-01 12:00:00 UTC",
    }


def test_extract_purchase_info_missing_fields_strict(extractor_factory):
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

    extractor = extractor_factory(responses)
    assert extractor.extract_purchase_info(email_content) is None


def test_process_email_successful_path(extractor_factory):
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
