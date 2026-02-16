"""Standardized test bench for exchange extractors using synthetic email templates."""

import pytest
from digital_asset_harvester.processing.extractors.coinbase import CoinbaseExtractor
from digital_asset_harvester.processing.extractors.binance import BinanceExtractor
from digital_asset_harvester.processing.extractors.kraken import KrakenExtractor
from digital_asset_harvester.processing.extractors.gemini import GeminiExtractor
from digital_asset_harvester.processing.extractors.cryptocom import CryptocomExtractor
from digital_asset_harvester.processing.extractors.ftx import FTXExtractor
from digital_asset_harvester.processing.extractors.coinspot import CoinSpotExtractor
from digital_asset_harvester.processing.extractors.newton import NewtonExtractor
from digital_asset_harvester.processing.extractors.swyftx import SwyftxExtractor
from digital_asset_harvester.processing.extractors.btcmarkets import BTCMarketsExtractor

# Test data mapping: (ExtractorClass, Subject, Sender, Body, ExpectedResults)
TEST_CASES = [
    # Coinbase Cases
    (
        CoinbaseExtractor,
        "Your Coinbase purchase of 0.001 BTC",
        "Coinbase <no-reply@coinbase.com>",
        "You successfully purchased 0.001 BTC for $100.00 USD.",
        [{"amount": "0.001", "item_name": "BTC", "total_spent": "100.00", "currency": "USD", "vendor": "Coinbase"}],
    ),
    (
        CoinbaseExtractor,
        "You've earned a staking reward",
        "no-reply@coinbase.com",
        "You just earned 0.00001234 ETH in staking rewards!",
        [{"amount": "0.00001234", "item_name": "ETH", "transaction_type": "staking_reward", "vendor": "Coinbase"}],
    ),
    # Binance Cases
    (
        BinanceExtractor,
        "Your order to buy 0.1 ETH has been filled",
        "Binance <do-not-reply@binance.com>",
        "Your order to buy 0.1 ETH for 200.00 USD has been filled.",
        [{"amount": "0.1", "item_name": "ETH", "total_spent": "200.00", "currency": "USD"}],
    ),
    (
        BinanceExtractor,
        "Distribution Confirmation",
        "do-not-reply@binance.com",
        "Your account has been credited with 0.5 SOL for SOL Staking.",
        [{"amount": "0.5", "item_name": "SOL", "transaction_type": "staking_reward"}],
    ),
    (
        BinanceExtractor,
        "Trade Confirmation",
        "do-not-reply@binance.com",
        """
        Order Details:
        - Pair: BTC/USDT
        - Side: Buy
        - Amount: 0.002 BTC
        - Price: 65,000.00 USDT
        - Total: 130.00 USDT
        - Fee: 0.000002 BTC
        """,
        [
            {
                "amount": "0.002",
                "item_name": "BTC",
                "total_spent": "130.00",
                "currency": "USDT",
                "fee_amount": "0.000002",
                "fee_currency": "BTC",
            }
        ],
    ),
    # Kraken Cases
    (
        KrakenExtractor,
        "Trade Confirmation: Buy 0.5 XMR",
        "Kraken <noreply@kraken.com>",
        "You have successfully bought 0.5 XMR for 50.00 EUR.",
        [{"amount": "0.5", "item_name": "XMR", "total_spent": "50.00", "currency": "EUR"}],
    ),
    (
        KrakenExtractor,
        "Staking Reward Received",
        "noreply@kraken.com",
        "We've credited your account with 10.5 ADA in staking rewards.",
        [{"amount": "10.5", "item_name": "ADA", "transaction_type": "staking_reward"}],
    ),
    (
        KrakenExtractor,
        "Kraken - Trade Confirmation",
        "noreply@kraken.com",
        "You bought 0.75 XBT (BTC) for $35,000.00 USD.\nCost: $35,000.00 USD\nFee: $105.00 USD",
        [{"amount": "0.75", "item_name": "BTC", "total_spent": "35000.00", "currency": "USD", "fee_amount": "105.00"}],
    ),
    # Gemini Cases
    (
        GeminiExtractor,
        "Order Confirmation - Buy BTC",
        "Gemini <orders@gemini.com>",
        "Your order to purchase 0.005 BTC for $150.00 has been completed.\nTransaction ID: GEM-2024-001",
        [
            {
                "amount": "0.005",
                "item_name": "BTC",
                "total_spent": "150.00",
                "currency": "USD",
                "vendor": "Gemini",
                "transaction_id": "GEM-2024-001",
            }
        ],
    ),
    # Crypto.com Cases
    (
        CryptocomExtractor,
        "Your order #12345 has been executed",
        "Crypto Exchange <noreply@crypto.com>",
        "Your market order #12345 to buy 2.5 SOL has been filled at a price of $25.00 per SOL.\nTotal cost: $62.50 USD.",
        [
            {
                "amount": "2.5",
                "item_name": "SOL",
                "total_spent": "62.50",
                "currency": "USD",
                "vendor": "Crypto.com",
                "transaction_id": "12345",
            }
        ],
    ),
    # FTX Cases
    (
        FTXExtractor,
        "Trade Executed: BUY 10 MATIC",
        "FTX <noreply@ftx.com>",
        "Trade Details:\nAmount: 10 MATIC\nPrice per unit: $0.85\nTotal: $8.50 USD",
        [{"amount": "10", "item_name": "MATIC", "total_spent": "8.50", "currency": "USD", "vendor": "FTX"}],
    ),
    # CoinSpot Cases
    (
        CoinSpotExtractor,
        "Purchase Confirmation",
        "CoinSpot <support@coinspot.com.au>",
        "You have successfully purchased 50 ADA for $25.00 AUD.\nReference: CS-20240115-001",
        [
            {
                "amount": "50",
                "item_name": "ADA",
                "total_spent": "25.00",
                "currency": "AUD",
                "vendor": "CoinSpot",
                "transaction_id": "CS-20240115-001",
            }
        ],
    ),
    # Newton Cases
    (
        NewtonExtractor,
        "Trade Confirmation",
        "Newton <support@newton.co>",
        "You bought 0.1 BTC for $5,000.00 CAD.\nReference: NEWT-12345",
        [
            {
                "amount": "0.1",
                "item_name": "BTC",
                "total_spent": "5000.00",
                "currency": "CAD",
                "vendor": "Newton",
                "transaction_id": "NEWT-12345",
            }
        ],
    ),
    # Swyftx Cases
    (
        SwyftxExtractor,
        "Trade Confirmation",
        "Swyftx <noreply@swyftx.com.au>",
        "You've successfully bought 1.5 ETH for $4,500.00 AUD.\nReceipt: SWY-998877",
        [
            {
                "amount": "1.5",
                "item_name": "ETH",
                "total_spent": "4500.00",
                "currency": "AUD",
                "vendor": "Swyftx",
                "transaction_id": "SWY-998877",
            }
        ],
    ),
    # BTCMarkets Cases
    (
        BTCMarketsExtractor,
        "Buy Order Filled",
        "BTC Markets <noreply@btcmarkets.net>",
        "Your buy order for 0.05 BTC has been filled at $60,000.00 AUD.\nOrder ID: BTCM-554433",
        [
            {
                "amount": "0.05",
                "item_name": "BTC",
                "total_spent": "60000.00",
                "currency": "AUD",
                "vendor": "BTCMarkets",
                "transaction_id": "BTCM-554433",
            }
        ],
    ),
    # Edge Case: Thousands separator and different currency
    (
        CoinbaseExtractor,
        "Your Coinbase purchase of 1.234 BTC",
        "Coinbase <no-reply@coinbase.com>",
        "You successfully purchased 1.234 BTC for €50,000.00 EUR.",
        [{"amount": "1.234", "item_name": "BTC", "total_spent": "50000.00", "currency": "EUR", "vendor": "Coinbase"}],
    ),
    # Edge Case: Ticker mapping for Kraken (XDG -> DOGE)
    (
        KrakenExtractor,
        "Trade Confirmation: Buy 1000 XDG",
        "Kraken <noreply@kraken.com>",
        "You have successfully bought 1,000 XDG for $100.00 USD.",
        [{"amount": "1000", "item_name": "DOGE", "total_spent": "100.00", "currency": "USD"}],
    ),
]


@pytest.mark.parametrize("extractor_class, subject, sender, body, expected_list", TEST_CASES)
def test_extractor_positive(extractor_class, subject, sender, body, expected_list):
    """Test that extractors correctly handle and extract data from valid emails."""
    extractor = extractor_class()

    # Check can_handle
    assert extractor.can_handle(subject, sender, body) is True, f"{extractor_class.__name__} should handle this email"

    # Check extraction
    results = extractor.extract(subject, sender, body)
    assert len(results) == len(expected_list), f"Expected {len(expected_list)} results, got {len(results)}"

    for i, expected in enumerate(expected_list):
        actual = results[i]
        for key, value in expected.items():
            assert actual.get(key) == value, f"Mismatch in {key}: expected {value}, got {actual.get(key)}"


NEGATIVE_TEST_CASES = [
    (CoinbaseExtractor, "Security Alert", "security@coinbase.com", "New login detected"),
    (BinanceExtractor, "Price Alert", "alerts@binance.com", "BTC is up 10%"),
    (KrakenExtractor, "Withdrawal Confirmed", "noreply@kraken.com", "You withdrew 1 ETH"),
    (GeminiExtractor, "Statement Ready", "no-reply@gemini.com", "Your monthly statement is ready"),
    (CryptocomExtractor, "Price Alert", "no-reply@crypto.com", "BTC is at $50,000"),
    (FTXExtractor, "Newsletter", "noreply@ftx.com", "Read our latest updates"),
]


@pytest.mark.parametrize("extractor_class, subject, sender, body", NEGATIVE_TEST_CASES)
def test_extractor_negative(extractor_class, subject, sender, body):
    """Test that extractors correctly ignore irrelevant emails."""
    extractor = extractor_class()
    # For some extractors, can_handle might be True but extract returns empty list,
    # or can_handle itself might be False.
    if extractor.can_handle(subject, sender, body):
        results = extractor.extract(subject, sender, body)
        assert len(results) == 0, f"{extractor_class.__name__} should not have extracted data from this email"
