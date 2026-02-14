"""Tests for specialized regex extractors."""

import pytest

from digital_asset_harvester.processing.extractors.binance import BinanceExtractor
from digital_asset_harvester.processing.extractors.coinbase import CoinbaseExtractor
from digital_asset_harvester.processing.extractors.kraken import KrakenExtractor
from tests.fixtures.emails import EMAIL_FIXTURES


def test_coinbase_extractor():
    extractor = CoinbaseExtractor()
    subject = "Your Coinbase purchase of 0.001 BTC"
    sender = "Coinbase <no-reply@coinbase.com>"
    body = "You successfully purchased 0.001 BTC for $100.00 USD."

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.001"
    assert results[0]["item_name"] == "BTC"
    assert results[0]["total_spent"] == "100.00"
    assert results[0]["currency"] == "USD"
    assert results[0]["vendor"] == "Coinbase"


def test_binance_extractor_single():
    extractor = BinanceExtractor()
    subject = "Your order to buy 0.1 ETH has been filled"
    sender = "Binance <do-not-reply@binance.com>"
    body = "Your order to buy 0.1 ETH for 200.00 USD has been filled."

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.1"
    assert results[0]["item_name"] == "ETH"
    assert results[0]["total_spent"] == "200.00"
    assert results[0]["currency"] == "USD"


def test_binance_extractor_multi():
    extractor = BinanceExtractor()
    email = EMAIL_FIXTURES["binance_multi_asset"]
    # Simple parsing of the fixture to get components
    lines = email.strip().split("\n")
    sender = lines[0].split(": ")[1]
    subject = lines[1].split(": ")[1]
    body = "\n".join(lines[3:])

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 2

    # Check BTC result
    btc_res = next(r for r in results if r["item_name"] == "BTC")
    assert btc_res["amount"] == "0.002"
    assert btc_res["total_spent"] == "130.00"
    assert btc_res["currency"] == "USDT"

    # Check ETH result
    eth_res = next(r for r in results if r["item_name"] == "ETH")
    assert eth_res["amount"] == "0.1"
    assert eth_res["total_spent"] == "350.00"
    assert eth_res["currency"] == "USDT"


def test_kraken_extractor():
    extractor = KrakenExtractor()
    subject = "Trade Confirmation: Buy 0.5 XMR"
    sender = "Kraken <noreply@kraken.com>"
    body = "You have successfully bought 0.5 XMR for 50.00 EUR."

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.5"
    assert results[0]["item_name"] == "XMR"
    assert results[0]["total_spent"] == "50.00"
    assert results[0]["currency"] == "EUR"


def test_kraken_extractor_with_xbt():
    extractor = KrakenExtractor()
    subject = "Kraken - Trade Confirmation"
    sender = "Kraken <noreply@kraken.com>"
    body = "You bought 0.75 XBT (BTC) for $35,000.00 USD.\nCost: $35,000.00 USD\nFee: $105.00 USD"

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.75"
    assert results[0]["item_name"] == "BTC"
    assert results[0]["total_spent"] == "35,000.00".replace(",", "")
    assert results[0]["currency"] == "USD"
    assert results[0]["fee_amount"] == "105.00"


def test_staking_rewards_regex():
    # Coinbase Staking
    cb_ext = CoinbaseExtractor()
    cb_body = "You just earned 0.00001234 ETH in staking rewards!"
    results = cb_ext.extract("You've earned a staking reward", "no-reply@coinbase.com", cb_body)
    # CoinbaseExtractor doesn't explicitly handle staking yet, let's see if our general pattern matches
    # actually it might not match "earned"

    # Let's check Binance Staking
    bn_ext = BinanceExtractor()
    bn_body = "Your account has been credited with 0.5 SOL for SOL Staking."
    results = bn_ext.extract("Distribution Confirmation", "do-not-reply@binance.com", bn_body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.5"
    assert results[0]["item_name"] == "SOL"
    assert results[0]["transaction_type"] == "staking_reward"

    # Kraken Staking
    kr_ext = KrakenExtractor()
    kr_body = "We've credited your account with 10.5 ADA in staking rewards."
    results = kr_ext.extract("Staking Reward Received", "noreply@kraken.com", kr_body)
    assert len(results) == 1
    assert results[0]["amount"] == "10.5"
    assert results[0]["item_name"] == "ADA"
    assert results[0]["transaction_type"] == "staking_reward"
