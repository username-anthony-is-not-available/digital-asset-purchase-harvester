from __future__ import annotations

import csv
import io
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from digital_asset_harvester.exporters.koinly import (
    KoinlyReportGenerator,
    write_purchase_data_to_koinly_csv,
)
from digital_asset_harvester.validation.schemas import PurchaseRecord


@pytest.fixture
def sample_purchases():
    return [
        PurchaseRecord(
            total_spent=Decimal("100.00"),
            currency="USD",
            amount=Decimal("1.0"),
            item_name="BTC",
            vendor="Coinbase",
            purchase_date="2023-01-15 12:30:00",
            transaction_type="buy",
            transaction_id="txn123",
        ),
        PurchaseRecord(
            total_spent=None,
            currency="",
            amount=Decimal("0.5"),
            item_name="ETH",
            vendor="Binance",
            purchase_date="2023-02-20",
            transaction_type="deposit",
            transaction_id="txn456",
        ),
        PurchaseRecord(
            total_spent=None,
            currency="",
            amount=Decimal("2.0"),
            item_name="SOL",
            vendor="Kraken",
            purchase_date="2023/03/10",
            transaction_type="withdrawal",
            transaction_id="txn789",
        ),
    ]


class TestKoinlyReportGenerator:
    def test_format_date(self):
        generator = KoinlyReportGenerator()
        assert generator._format_date("2023-01-15 12:30:00") == "2023-01-15 12:30:00"
        assert generator._format_date("2023-02-20") == "2023-02-20 00:00:00"
        assert generator._format_date("2023/03/10") == "2023-03-10 00:00:00"
        assert generator._format_date("") == ""
        assert generator._format_date("invalid-date") == "invalid-date"

    def test_convert_purchase_to_koinly_row(self, sample_purchases):
        generator = KoinlyReportGenerator()

        # Test "buy" transaction
        buy_row = generator._convert_purchase_to_koinly_row(sample_purchases[0].model_dump())
        assert buy_row["Label"] == "buy"
        assert buy_row["Sent Amount"] == "100.00"
        assert buy_row["Sent Currency"] == "USD"
        assert buy_row["Received Amount"] == "1.0"
        assert buy_row["Received Currency"] == "BTC"
        assert buy_row["TxHash"] == "txn123"
        assert buy_row["Description"] == "Buy from Coinbase"

        # Test "deposit" transaction
        deposit_row = generator._convert_purchase_to_koinly_row(sample_purchases[1].model_dump())
        assert deposit_row["Label"] == "deposit"
        assert deposit_row["Sent Amount"] == ""
        assert deposit_row["Sent Currency"] == ""
        assert deposit_row["Received Amount"] == "0.5"
        assert deposit_row["Received Currency"] == "ETH"
        assert deposit_row["TxHash"] == "txn456"
        assert deposit_row["Description"] == "Deposit from Binance"

        # Test "withdrawal" transaction
        withdrawal_row = generator._convert_purchase_to_koinly_row(sample_purchases[2].model_dump())
        assert withdrawal_row["Label"] == "withdrawal"
        assert withdrawal_row["Sent Amount"] == "2.0"
        assert withdrawal_row["Sent Currency"] == "SOL"
        assert withdrawal_row["Received Amount"] == ""
        assert withdrawal_row["Received Currency"] == ""
        assert withdrawal_row["TxHash"] == "txn789"
        assert withdrawal_row["Description"] == "Withdrawal from Kraken"

    def test_convert_staking_reward_to_koinly_row(self):
        generator = KoinlyReportGenerator()
        reward = {
            "transaction_type": "staking_reward",
            "amount": Decimal("0.01"),
            "item_name": "ETH",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-01",
        }
        row = generator._convert_purchase_to_koinly_row(reward)
        assert row["Label"] == "staking"
        assert row["Received Amount"] == "0.01"
        assert row["Received Currency"] == "ETH"
        assert row["Sent Amount"] == ""
        assert row["Sent Currency"] == ""
        assert row["Description"] == "Staking_reward from Coinbase"

    def test_generate_csv_rows(self, sample_purchases):
        generator = KoinlyReportGenerator()
        purchase_dicts = [p.model_dump() for p in sample_purchases]
        rows = generator.generate_csv_rows(purchase_dicts)
        assert len(rows) == 3
        assert rows[0]["Label"] == "buy"
        assert rows[1]["Label"] == "deposit"
        assert rows[2]["Label"] == "withdrawal"


def test_write_purchase_data_to_koinly_csv(sample_purchases, tmp_path):
    output_file = tmp_path / "koinly_report.csv"
    write_purchase_data_to_koinly_csv(sample_purchases, str(output_file))

    assert output_file.exists()

    with open(output_file, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        assert header == [
            "Date",
            "Sent Amount",
            "Sent Currency",
            "Received Amount",
            "Received Currency",
            "Fee Amount",
            "Fee Currency",
            "Net Worth Amount",
            "Net Worth Currency",
            "Label",
            "Description",
            "TxHash",
        ]
        rows = list(reader)
        assert len(rows) == 3
        assert rows[0][9] == "buy"
        assert rows[1][9] == "deposit"
        assert rows[2][9] == "withdrawal"


def test_write_purchase_data_to_koinly_csv_empty_list(tmp_path):
    output_file = tmp_path / "empty_report.csv"
    write_purchase_data_to_koinly_csv([], str(output_file))
    assert not output_file.exists()
