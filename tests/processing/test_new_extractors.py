import pytest
from digital_asset_harvester.processing.extractors.gemini import GeminiExtractor
from digital_asset_harvester.processing.extractors.cryptocom import CryptocomExtractor
from digital_asset_harvester.processing.extractors.ftx import FTXExtractor
from digital_asset_harvester.processing.extractors.newton import NewtonExtractor
from digital_asset_harvester.processing.extractors.btcmarkets import BTCMarketsExtractor
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


def test_newton_extractor():
    extractor = NewtonExtractor()
    subject = "Newton Trade Confirmation"
    sender = "Newton <support@newton.co>"
    body = "You bought 0.1 BTC for $5,000.00 CAD. Reference #NT-123"

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.1"
    assert results[0]["item_name"] == "BTC"
    assert results[0]["total_spent"] == "5000.00"
    assert results[0]["currency"] == "CAD"
    assert results[0]["vendor"] == "Newton"
    assert results[0]["transaction_id"] == "NT-123"


def test_btcmarkets_extractor_total():
    extractor = BTCMarketsExtractor()
    subject = "BTCMarkets Trade Confirmation"
    sender = "BTCMarkets <noreply@btcmarkets.net>"
    body = "Bought 0.05 BTC for 3,000 AUD. Order ID: BTC-456"

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.05"
    assert results[0]["item_name"] == "BTC"
    assert results[0]["total_spent"] == "3000.0"
    assert results[0]["currency"] == "AUD"
    assert results[0]["vendor"] == "BTCMarkets"
    assert results[0]["transaction_id"] == "BTC-456"


def test_btcmarkets_extractor_price():
    extractor = BTCMarketsExtractor()
    subject = "BTCMarkets Trade Confirmation"
    sender = "BTCMarkets <noreply@btcmarkets.net>"
    body = "Your buy order for 0.05 BTC has been filled at $60,000.00 AUD. Order ID: BTC-789"

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.05"
    assert results[0]["item_name"] == "BTC"
    assert results[0]["total_spent"] == "3000.0"  # 0.05 * 60000
    assert results[0]["currency"] == "AUD"
    assert results[0]["vendor"] == "BTCMarkets"
    assert results[0]["transaction_id"] == "BTC-789"


from digital_asset_harvester.processing.extractors.bitstamp import BitstampExtractor
from digital_asset_harvester.processing.extractors.bitfinex import BitfinexExtractor

def test_bitstamp_extractor_buy():
    extractor = BitstampExtractor()
    subject = "Transaction confirmation"
    sender = "Bitstamp <noreply@bitstamp.net>"
    body = "You have successfully bought 0.5 BTC for 25,000.00 USD. Transaction ID: BTST12345"

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.5"
    assert results[0]["item_name"] == "BTC"
    assert results[0]["total_spent"] == "25000.00"
    assert results[0]["currency"] == "USD"
    assert results[0]["vendor"] == "Bitstamp"
    assert results[0]["transaction_type"] == "buy"
    assert results[0]["transaction_id"] == "BTST12345"

def test_bitstamp_extractor_sell():
    extractor = BitstampExtractor()
    subject = "Transaction confirmation"
    sender = "Bitstamp <noreply@bitstamp.net>"
    body = "You have successfully sold 10.0 ETH for 20,000.00 USD."

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "10.0"
    assert results[0]["item_name"] == "ETH"
    assert results[0]["total_spent"] == "20000.00"
    assert results[0]["currency"] == "USD"
    assert results[0]["transaction_type"] == "withdrawal"

def test_bitfinex_extractor_buy():
    extractor = BitfinexExtractor()
    subject = "Exchange Trade Execution - BUY ETH/USD"
    sender = "Bitfinex <no-reply@bitfinex.com>"
    body = "Exchange Trade Execution - BUY 0.5 ETH @ 2500.0 USD on ETH/USD. Order ID: 987654321"

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.5"
    assert results[0]["item_name"] == "ETH"
    assert float(results[0]["total_spent"]) == 1250.0
    assert results[0]["currency"] == "USD"
    assert results[0]["vendor"] == "Bitfinex"
    assert results[0]["transaction_type"] == "buy"
    assert results[0]["transaction_id"] == "987654321"

def test_bitfinex_extractor_sell():
    extractor = BitfinexExtractor()
    subject = "Exchange Trade Execution - SELL BTC/USD"
    sender = "Bitfinex <no-reply@bitfinex.com>"
    body = "Exchange Trade Execution - SELL 0.1 BTC @ 50000.0 USD on BTC/USD."

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.1"
    assert results[0]["item_name"] == "BTC"
    assert float(results[0]["total_spent"]) == 5000.0
    assert results[0]["currency"] == "USD"
    assert results[0]["transaction_type"] == "withdrawal"
