"""Tests for the CSV writer utility."""

import csv
import os
from decimal import Decimal

from digital_asset_harvester.output.csv_writer import write_purchase_data_to_csv
from digital_asset_harvester.validation import PurchaseRecord


def test_write_purchase_data_to_csv(tmp_path):
    """Verify that purchase data is correctly written to a CSV file."""
    filepath = os.path.join(tmp_path, "purchases.csv")
    records = [
        PurchaseRecord(
            total_spent=Decimal("123.45"),
            currency="USD",
            amount=Decimal("0.01"),
            item_name="BTC",
            vendor="Coinbase",
            purchase_date="2024-01-10 10:00:00 UTC",
        ),
        PurchaseRecord(
            total_spent=Decimal("543.21"),
            currency="USD",
            amount=Decimal("0.2"),
            item_name="ETH",
            vendor="Binance",
            purchase_date="2024-01-11 11:00:00 UTC",
        ),
    ]

    write_purchase_data_to_csv(filepath, records)

    assert os.path.exists(filepath)

    with open(filepath, "r", newline="", encoding="utf-8") as csvfile:
        reader = list(csv.reader(csvfile))
        assert reader[0] == [
            "total_spent",
            "currency",
            "amount",
            "item_name",
            "vendor",
            "purchase_date",
        ]
        assert reader[1] == [
            "123.45",
            "USD",
            "0.01",
            "BTC",
            "Coinbase",
            "2024-01-10 10:00:00 UTC",
        ]
        assert reader[2] == [
            "543.21",
            "USD",
            "0.2",
            "ETH",
            "Binance",
            "2024-01-11 11:00:00 UTC",
        ]


def test_write_purchase_data_no_header(tmp_path):
    """Verify that the header is omitted when requested."""
    filepath = os.path.join(tmp_path, "purchases.csv")
    records = [
        PurchaseRecord(
            total_spent=Decimal("123.45"),
            currency="USD",
            amount=Decimal("0.01"),
            item_name="BTC",
            vendor="Coinbase",
            purchase_date="2024-01-10 10:00:00 UTC",
        )
    ]

    write_purchase_data_to_csv(filepath, records, include_header=False)

    with open(filepath, "r", newline="", encoding="utf-8") as csvfile:
        reader = list(csv.reader(csvfile))
        assert reader[0] == [
            "123.45",
            "USD",
            "0.01",
            "BTC",
            "Coinbase",
            "2024-01-10 10:00:00 UTC",
        ]


def test_write_purchase_data_empty_records(tmp_path):
    """Verify that an empty file is not created for empty records."""
    filepath = os.path.join(tmp_path, "purchases.csv")
    write_purchase_data_to_csv(filepath, [])
    assert not os.path.exists(filepath)
