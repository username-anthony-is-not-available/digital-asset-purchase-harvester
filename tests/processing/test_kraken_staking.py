"""Tests for Kraken staking rewards extraction."""

import pytest
from digital_asset_harvester.processing.extractors.kraken import KrakenExtractor


def test_kraken_staking_summary_extraction():
    extractor = KrakenExtractor()
    subject = "Your weekly staking rewards are here!"
    sender = "Kraken <noreply@kraken.com>"
    body = """
    Hello,

    You've earned the following rewards this week:

    * 0.00123456 ETH
    * 10.50000000 ADA
    * 0.50000000 SOL

    Transaction ID: KR-STAKE-SUMMARY-2024-W12
    These rewards have been credited to your account.
    """

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)

    # Verify that multiple rewards are extracted from the summary format
    assert len(results) == 3

    eth_res = next(r for r in results if r["item_name"] == "ETH")
    assert eth_res["amount"] == "0.00123456"
    assert eth_res["transaction_type"] == "staking_reward"
    assert eth_res["transaction_id"] == "KR-STAKE-SUMMARY-2024-W12"

    ada_res = next(r for r in results if r["item_name"] == "ADA")
    assert ada_res["amount"] == "10.50000000"
    assert ada_res["transaction_type"] == "staking_reward"

    sol_res = next(r for r in results if r["item_name"] == "SOL")
    assert sol_res["amount"] == "0.50000000"
    assert sol_res["transaction_type"] == "staking_reward"


def test_kraken_staking_payout_summary_subject():
    extractor = KrakenExtractor()
    subject = "Staking Payout Summary"
    sender = "Kraken <noreply@kraken.com>"
    body = "We've credited your account with 10.5 ADA in staking rewards."

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "10.5"
    assert results[0]["item_name"] == "ADA"
    assert results[0]["transaction_type"] == "staking_reward"


def test_kraken_flexible_staking_patterns():
    extractor = KrakenExtractor()
    subject = "Staking reward received"
    sender = "Kraken <noreply@kraken.com>"

    # Alternative phrasing
    body = "Your staking reward of 0.05 DOT has been deposited into your account."
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "0.05"
    assert results[0]["item_name"] == "DOT"
    assert results[0]["transaction_type"] == "staking_reward"
