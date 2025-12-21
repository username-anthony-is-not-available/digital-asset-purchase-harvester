import csv
import os
from decimal import Decimal
from unittest.mock import mock_open, patch
from digital_asset_harvester.output.csv_writer import write_purchase_data_to_csv
from digital_asset_harvester.validation.schemas import PurchaseRecord

def test_write_purchase_data_to_csv_handles_empty_data():
    with patch("builtins.open", mock_open()) as mock_file:
        write_purchase_data_to_csv("test.csv", [])
        mock_file.assert_not_called()

def test_write_purchase_data_to_csv_writes_records():
    purchase_data = [
        PurchaseRecord(
            total_spent=Decimal("100.00"),
            currency="USD",
            amount=Decimal("1.0"),
            item_name="BTC",
            vendor="TestVendor",
            purchase_date="2023-01-01",
        )
    ]

    m = mock_open()
    with patch("builtins.open", m):
        write_purchase_data_to_csv("test.csv", purchase_data)

    m.assert_called_once_with("test.csv", "w", newline="")
    handle = m()
    handle.write.assert_any_call("total_spent,currency,amount,item_name,vendor,purchase_date\r\n")
