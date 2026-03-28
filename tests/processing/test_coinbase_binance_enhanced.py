"""Enhanced unit tests for Coinbase and Binance extractors."""

import pytest
from digital_asset_harvester.processing.extractors.coinbase import CoinbaseExtractor
from digital_asset_harvester.processing.extractors.binance import BinanceExtractor


def test_coinbase_multi_purchase():
    """Test Coinbase extractor with multiple purchases in one email."""
    extractor = CoinbaseExtractor()
    subject = "Your Coinbase purchases"
    sender = "no-reply@coinbase.com"
    body = """
    You bought 0.1 BTC for $5,000.00 USD.
    You bought 1.0 ETH for $2,500.00 USD.
    """
    results = extractor.extract(subject, sender, body)
    assert len(results) == 2
    assert results[0]["amount"] == "0.1"
    assert results[0]["item_name"] == "BTC"
    assert results[1]["amount"] == "1.0"
    assert results[1]["item_name"] == "ETH"


def test_coinbase_fiat_first_variant():
    """Test Coinbase variant where fiat amount comes before crypto."""
    extractor = CoinbaseExtractor()
    subject = "Your Coinbase purchase"
    sender = "no-reply@coinbase.com"
    body = "You successfully purchased $100.00 of BTC."
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["item_name"] == "BTC"
    assert results[0]["total_spent"] == "100.00"
    assert results[0]["currency"] == "USD"


def test_coinbase_order_completed_variant():
    """Test Coinbase variant 'Order #... completed'."""
    extractor = CoinbaseExtractor()
    subject = "Coinbase Order #ABC-123 Completed"
    sender = "no-reply@coinbase.com"
    body = "Your order to buy 0.05 BTC for $3,000.00 USD has been completed. Transaction ID: TXN-999"
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.05"
    assert results[0]["item_name"] == "BTC"
    assert results[0]["transaction_id"] == "TXN-999"


def test_coinbase_multi_staking_rewards():
    """Test Coinbase extractor with multiple staking rewards."""
    extractor = CoinbaseExtractor()
    subject = "Your staking rewards"
    sender = "no-reply@coinbase.com"
    body = """
    You just earned 0.00001 ETH in staking rewards!
    You just earned 0.05 SOL in staking rewards!
    """
    results = extractor.extract(subject, sender, body)
    assert len(results) == 2
    assert results[0]["item_name"] == "ETH"
    assert results[0]["transaction_type"] == "staking_reward"
    assert results[1]["item_name"] == "SOL"
    assert results[1]["transaction_type"] == "staking_reward"


def test_binance_multi_trade_confirmation_blocks():
    """Test Binance extractor with multiple trade blocks."""
    extractor = BinanceExtractor()
    subject = "Trade Confirmation"
    sender = "do-not-reply@binance.com"
    body = """
    Order Details:
    Pair: BTC/USDT
    Side: Buy
    Amount: 0.002 BTC
    Price: 60,000.00 USDT
    Total: 120.00 USDT
    Fee: 0.000002 BTC

    Order Details:
    Pair: ETH/USDT
    Side: Buy
    Amount: 0.5 ETH
    Price: 3,000.00 USDT
    Total: 1,500.00 USDT
    Fee: 0.0005 ETH
    """
    results = extractor.extract(subject, sender, body)
    assert len(results) == 2
    assert results[0]["item_name"] == "BTC"
    assert results[0]["total_spent"] == "120.00"
    assert results[1]["item_name"] == "ETH"
    assert results[1]["total_spent"] == "1500.00"


def test_binance_sell_side():
    """Test Binance extractor with a Sell trade."""
    extractor = BinanceExtractor()
    subject = "Trade Confirmation"
    sender = "do-not-reply@binance.com"
    body = """
    Order Details:
    Pair: BTC/USDT
    Side: Sell
    Amount: 0.01 BTC
    Price: 60,000.00 USDT
    Total: 600.00 USDT
    """
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["item_name"] == "BTC"
    # Sell should be treated as withdrawal or similar for tax tracking
    assert results[0]["transaction_type"] == "withdrawal"


def test_binance_multi_one_liner():
    """Test Binance extractor with multiple one-liner buys."""
    extractor = BinanceExtractor()
    subject = "Your orders"
    sender = "do-not-reply@binance.com"
    body = """
    Your order to buy 0.1 ETH for 200.00 USD has been filled.
    Your order to buy 0.01 BTC for 600.00 USD has been filled.
    """
    results = extractor.extract(subject, sender, body)
    assert len(results) == 2
    assert results[0]["item_name"] == "ETH"
    assert results[1]["item_name"] == "BTC"
