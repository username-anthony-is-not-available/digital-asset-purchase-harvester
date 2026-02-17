"""Unit tests for the CoinTracker exporter."""

import os
import csv
import pytest
from digital_asset_harvester.exporters.cointracker import (
    CoinTrackerReportGenerator,
    write_purchase_data_to_cointracker_csv,
)


def test_cointracker_buy_row():
    generator = CoinTrackerReportGenerator()
    purchase = {
        "purchase_date": "2023-01-01 12:00:00 UTC",
        "item_name": "BTC",
        "amount": 0.1,
        "total_spent": 2000.0,
        "currency": "USD",
        "vendor": "Coinbase",
        "transaction_type": "buy",
        "fee_amount": 10.0,
        "fee_currency": "USD",
    }
    row = generator._convert_purchase_to_cointracker_row(purchase)

    assert row["Date"] == "01/01/2023 12:00:00"
    assert row["Received Quantity"] == "0.1"
    assert row["Received Currency"] == "BTC"
    assert row["Sent Quantity"] == "2000.0"
    assert row["Sent Currency"] == "USD"
    assert row["Fee Quantity"] == "10.0"
    assert row["Fee Currency"] == "USD"
    assert row["Tag"] == ""


def test_cointracker_deposit_row():
    generator = CoinTrackerReportGenerator()
    purchase = {
        "purchase_date": "2023-01-01 12:00:00 UTC",
        "item_name": "BTC",
        "amount": 0.5,
        "vendor": "Personal Wallet",
        "transaction_type": "deposit",
    }
    row = generator._convert_purchase_to_cointracker_row(purchase)

    assert row["Received Quantity"] == "0.5"
    assert row["Received Currency"] == "BTC"
    assert row["Sent Quantity"] == ""
    assert row["Sent Currency"] == ""


def test_cointracker_withdrawal_row():
    generator = CoinTrackerReportGenerator()
    purchase = {
        "purchase_date": "2023-01-01 12:00:00 UTC",
        "item_name": "ETH",
        "amount": 1.0,
        "vendor": "My Wallet",
        "transaction_type": "withdrawal",
    }
    row = generator._convert_purchase_to_cointracker_row(purchase)

    assert row["Received Quantity"] == ""
    assert row["Received Currency"] == ""
    assert row["Sent Quantity"] == "1.0"
    assert row["Sent Currency"] == "ETH"


def test_cointracker_staking_reward_row():
    generator = CoinTrackerReportGenerator()
    purchase = {
        "purchase_date": "2023-01-01 12:00:00 UTC",
        "item_name": "SOL",
        "amount": 0.05,
        "vendor": "Solana",
        "transaction_type": "staking_reward",
    }
    row = generator._convert_purchase_to_cointracker_row(purchase)

    assert row["Received Quantity"] == "0.05"
    assert row["Received Currency"] == "SOL"
    assert row["Tag"] == "staked"


def test_write_cointracker_csv(tmp_path):
    output_file = tmp_path / "cointracker.csv"
    purchases = [
        {
            "purchase_date": "2023-01-01 12:00:00 UTC",
            "item_name": "BTC",
            "amount": 0.1,
            "total_spent": 2000.0,
            "currency": "USD",
            "vendor": "Coinbase",
            "transaction_type": "buy",
        }
    ]

    write_purchase_data_to_cointracker_csv(purchases, str(output_file))

    assert os.path.exists(output_file)
    with open(output_file, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["Received Currency"] == "BTC"
        assert rows[0]["Sent Quantity"] == "2000.0"
