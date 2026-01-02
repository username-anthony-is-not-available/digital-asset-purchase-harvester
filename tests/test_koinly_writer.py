"""Tests for the Koinly writer utility."""

import csv
import os
from decimal import Decimal

import pytest

from digital_asset_harvester.output.koinly_writer import (
    KoinlyReportGenerator,
    write_purchase_data_to_koinly_csv,
)
from digital_asset_harvester.validation import PurchaseRecord


def test_koinly_report_generator_format_transaction():
    """Verify that a purchase record is correctly formatted for Koinly."""
    generator = KoinlyReportGenerator()
    
    purchase = {
        "total_spent": "123.45",
        "currency": "USD",
        "amount": "0.01",
        "item_name": "BTC",
        "vendor": "Coinbase",
        "purchase_date": "2024-01-10 10:00:00",
    }
    
    formatted = generator.format_transaction(purchase)
    
    assert formatted["Date"] == "2024-01-10 10:00:00"
    assert formatted["Sent Amount"] == "123.45"
    assert formatted["Sent Currency"] == "USD"
    assert formatted["Received Amount"] == "0.01"
    assert formatted["Received Currency"] == "BTC"
    assert formatted["Label"] == "buy"
    assert formatted["Fee Amount"] == ""
    assert formatted["Fee Currency"] == ""
    assert formatted["TxHash"] == ""


def test_koinly_report_generator_format_transaction_with_various_date_formats():
    """Verify date parsing handles various formats."""
    generator = KoinlyReportGenerator()
    
    test_cases = [
        ("2024-01-10 10:00:00", "2024-01-10 10:00:00"),
        ("2024-01-10", "2024-01-10 00:00:00"),
        ("2024-01-10T10:00:00", "2024-01-10 10:00:00"),
    ]
    
    for input_date, expected_output in test_cases:
        purchase = {
            "total_spent": "100",
            "currency": "USD",
            "amount": "0.01",
            "item_name": "BTC",
            "vendor": "Test",
            "purchase_date": input_date,
        }
        
        formatted = generator.format_transaction(purchase)
        assert formatted["Date"] == expected_output


def test_write_purchase_data_to_koinly_csv(tmp_path):
    """Verify that purchase data is correctly written to a Koinly CSV file."""
    filepath = os.path.join(tmp_path, "koinly_purchases.csv")
    
    purchases = [
        {
            "total_spent": "123.45",
            "currency": "USD",
            "amount": "0.01",
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-10 10:00:00",
        },
        {
            "total_spent": "543.21",
            "currency": "USD",
            "amount": "0.2",
            "item_name": "ETH",
            "vendor": "Binance",
            "purchase_date": "2024-01-11 11:00:00",
        },
    ]

    write_purchase_data_to_koinly_csv(purchases, filepath)

    assert os.path.exists(filepath)

    with open(filepath, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        
        assert len(rows) == 2
        
        # Check first row
        assert rows[0]["Date"] == "2024-01-10 10:00:00"
        assert rows[0]["Sent Amount"] == "123.45"
        assert rows[0]["Sent Currency"] == "USD"
        assert rows[0]["Received Amount"] == "0.01"
        assert rows[0]["Received Currency"] == "BTC"
        assert rows[0]["Label"] == "buy"
        
        # Check second row
        assert rows[1]["Date"] == "2024-01-11 11:00:00"
        assert rows[1]["Sent Amount"] == "543.21"
        assert rows[1]["Sent Currency"] == "USD"
        assert rows[1]["Received Amount"] == "0.2"
        assert rows[1]["Received Currency"] == "ETH"
        assert rows[1]["Label"] == "buy"


def test_write_purchase_data_to_koinly_csv_no_header(tmp_path):
    """Verify that the header is omitted when requested."""
    filepath = os.path.join(tmp_path, "koinly_purchases.csv")
    
    purchases = [
        {
            "total_spent": "123.45",
            "currency": "USD",
            "amount": "0.01",
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-10 10:00:00",
        }
    ]

    write_purchase_data_to_koinly_csv(purchases, filepath, include_header=False)

    with open(filepath, "r", newline="", encoding="utf-8") as csvfile:
        reader = list(csv.reader(csvfile))
        # First row should be data, not headers
        assert reader[0][0] == "2024-01-10 10:00:00"
        assert reader[0][1] == "123.45"


def test_write_purchase_data_to_koinly_csv_empty_records(tmp_path):
    """Verify that an empty file is not created for empty records."""
    filepath = os.path.join(tmp_path, "koinly_purchases.csv")
    write_purchase_data_to_koinly_csv([], filepath)
    assert not os.path.exists(filepath)


def test_koinly_report_generator_handles_missing_fields():
    """Verify that missing fields are handled gracefully."""
    generator = KoinlyReportGenerator()
    
    purchase = {
        "total_spent": "100",
        "currency": "USD",
    }
    
    formatted = generator.format_transaction(purchase)
    
    assert formatted["Sent Amount"] == "100"
    assert formatted["Sent Currency"] == "USD"
    assert formatted["Received Amount"] == ""
    assert formatted["Received Currency"] == ""
    assert formatted["Date"] == ""
