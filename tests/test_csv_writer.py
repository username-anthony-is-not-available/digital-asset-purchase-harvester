import csv
from pathlib import Path
from digital_asset_harvester.output.csv_writer import write_purchase_data_to_csv

def test_write_purchase_data_to_csv(tmp_path: Path):
    output_file = tmp_path / "test.csv"
    purchases = [
        {
            "vendor": "Coinbase",
            "amount": 0.1,
            "currency": "BTC",
            "total_spent": 1000.0,
            "purchase_date": "2024-01-01",
        }
    ]

    write_purchase_data_to_csv(str(output_file), purchases)

    with open(output_file, "r") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["vendor"] == "Coinbase"
        assert rows[0]["amount"] == "0.1"
