import pytest
from digital_asset_harvester.processing.extractors.gemini import GeminiExtractor
from digital_asset_harvester.processing.extractors.cryptocom import CryptocomExtractor
from digital_asset_harvester.processing.extractors.ftx import FTXExtractor
from tests.fixtures.emails import EMAIL_FIXTURES


def test_gemini_extractor():
    extractor = GeminiExtractor()
    email = EMAIL_FIXTURES["gemini_purchase"]
    subject = "Order Confirmation - Buy BTC"
    sender = "Gemini <orders@gemini.com>"
    body = email

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.005"
    assert results[0]["item_name"] == "BTC"
    assert results[0]["total_spent"] == "150.00"
    assert results[0]["currency"] == "USD"
    assert results[0]["vendor"] == "Gemini"
    assert results[0]["transaction_id"] == "GEM-2024-001"


def test_cryptocom_extractor():
    extractor = CryptocomExtractor()
    email = EMAIL_FIXTURES["complex_purchase"]
    subject = "Your order #12345 has been executed"
    sender = "Crypto Exchange <noreply@crypto.com>"
    body = email

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "2.5"
    assert results[0]["item_name"] == "SOL"
    assert results[0]["total_spent"] == "62.50"
    assert results[0]["currency"] == "USD"
    assert results[0]["vendor"] == "Crypto.com"
    assert results[0]["transaction_id"] == "12345"


def test_ftx_extractor():
    extractor = FTXExtractor()
    email = EMAIL_FIXTURES["ftx_purchase"]
    subject = "Trade Executed: BUY 10 MATIC"
    sender = "FTX <noreply@ftx.com>"
    body = email

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "10"
    assert results[0]["item_name"] == "MATIC"
    assert results[0]["total_spent"] == "8.50"
    assert results[0]["currency"] == "USD"
    assert results[0]["vendor"] == "FTX"
