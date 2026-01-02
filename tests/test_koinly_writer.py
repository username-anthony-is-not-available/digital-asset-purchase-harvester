"""Tests for Koinly CSV writer functionality."""
import os
import tempfile
import csv
from digital_asset_harvester.output.koinly_writer import (
    KoinlyReportGenerator,
    write_purchase_data_to_koinly_csv,
)


def test_koinly_report_generator_format_date():
    """Test date formatting for Koinly."""
    generator = KoinlyReportGenerator()
    
    # Test various date formats
    assert generator._format_date("2024-01-15 10:30:00") == "2024-01-15 10:30:00"
    assert generator._format_date("2024-01-15") == "2024-01-15 00:00:00"
    assert generator._format_date("2024/01/15") == "2024-01-15 00:00:00"
    
    # Test empty date (should return current time)
    result = generator._format_date("")
    assert len(result) == 19  # YYYY-MM-DD HH:MM:SS format


def test_koinly_report_generator_convert_purchase():
    """Test converting purchase record to Koinly row."""
    generator = KoinlyReportGenerator()
    
    purchase = {
        "total_spent": 100.50,
        "currency": "USD",
        "amount": 0.002,
        "item_name": "BTC",
        "vendor": "Coinbase",
        "purchase_date": "2024-01-15 10:30:00",
        "transaction_id": "abc123",
    }
    
    row = generator._convert_purchase_to_koinly_row(purchase)
    
    assert row["Date"] == "2024-01-15 10:30:00"
    assert row["Sent Amount"] == "100.5"
    assert row["Sent Currency"] == "USD"
    assert row["Received Amount"] == "0.002"
    assert row["Received Currency"] == "BTC"
    assert row["Label"] == "purchase"
    assert "Coinbase" in row["Description"]
    assert row["TxHash"] == "abc123"


def test_koinly_report_generator_generate_csv_rows():
    """Test generating multiple CSV rows."""
    generator = KoinlyReportGenerator()
    
    purchases = [
        {
            "total_spent": 100,
            "currency": "USD",
            "amount": 0.002,
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-15",
        },
        {
            "total_spent": 50,
            "currency": "EUR",
            "amount": 1.5,
            "item_name": "ETH",
            "vendor": "Binance",
            "purchase_date": "2024-01-16",
        },
    ]
    
    rows = generator.generate_csv_rows(purchases)
    
    assert len(rows) == 2
    assert rows[0]["Sent Currency"] == "USD"
    assert rows[1]["Sent Currency"] == "EUR"


def test_write_purchase_data_to_koinly_csv():
    """Test writing purchase data to CSV file."""
    purchases = [
        {
            "total_spent": 100,
            "currency": "USD",
            "amount": 0.002,
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-15",
            "transaction_id": "tx123",
        }
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_koinly.csv")
        write_purchase_data_to_koinly_csv(purchases, filepath)
        
        # Verify file was created
        assert os.path.exists(filepath)
        
        # Verify content
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]["Sent Currency"] == "USD"
            assert rows[0]["Received Currency"] == "BTC"
            assert "Coinbase" in rows[0]["Description"]


def test_write_purchase_data_to_koinly_csv_empty():
    """Test that empty purchases don't create a file."""
    purchases = []
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_empty_koinly.csv")
        write_purchase_data_to_koinly_csv(purchases, filepath)
        
        # Verify file was not created
        assert not os.path.exists(filepath)


def test_write_purchase_data_to_koinly_csv_with_objects():
    """Test writing purchase data from objects (not dicts)."""
    
    class PurchaseObject:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    purchases = [
        PurchaseObject(
            total_spent=200,
            currency="GBP",
            amount=0.005,
            item_name="BTC",
            vendor="Kraken",
            purchase_date="2024-02-01",
            transaction_id="tx456",
        )
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_objects_koinly.csv")
        write_purchase_data_to_koinly_csv(purchases, filepath)
        
        # Verify file was created
        assert os.path.exists(filepath)
        
        # Verify content
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            assert rows[0]["Sent Currency"] == "GBP"
            assert rows[0]["Received Amount"] == "0.005"
