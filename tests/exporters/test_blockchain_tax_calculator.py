from __future__ import annotations

import csv
from decimal import Decimal

import pytest

from digital_asset_harvester.exporters.blockchain_tax_calculator import (
    BlockchainTaxCalculatorReportGenerator,
    write_purchase_data_to_blockchain_tax_csv,
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
    ]


class TestBlockchainTaxCalculatorReportGenerator:
    def test_format_date(self):
        generator = BlockchainTaxCalculatorReportGenerator()
        assert generator._format_date("2023-01-15 12:30:00") == "2023-01-15 12:30:00"
        assert generator._format_date("2023-02-20") == "2023-02-20 00:00:00"

    def test_convert_purchase_to_btc_row(self, sample_purchases):
        generator = BlockchainTaxCalculatorReportGenerator()

        # Test "buy" transaction
        buy_row = generator._convert_purchase_to_btc_row(sample_purchases[0].model_dump())
        assert buy_row["Type"] == "Buy"
        assert buy_row["Amount"] == "1.0"
        assert buy_row["Asset"] == "BTC"
        assert buy_row["Quote Amount"] == "100.00"
        assert buy_row["Quote Asset"] == "USD"

        # Test "deposit" transaction
        deposit_row = generator._convert_purchase_to_btc_row(sample_purchases[1].model_dump())
        assert deposit_row["Type"] == "Deposit"
        assert deposit_row["Amount"] == "0.5"
        assert deposit_row["Asset"] == "ETH"


def test_write_purchase_data_to_blockchain_tax_csv(sample_purchases, tmp_path):
    output_file = tmp_path / "btc_report.csv"
    write_purchase_data_to_blockchain_tax_csv(sample_purchases, str(output_file))

    assert output_file.exists()

    with open(output_file, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        assert "Date" in header
        assert "Asset" in header
        rows = list(reader)
        assert len(rows) == 2
