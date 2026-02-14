import os
import tempfile
from digital_asset_harvester.exporters.cra import write_purchase_data_to_cra_pdf

def test_write_purchase_data_to_cra_pdf():
    purchases = [
        {
            "vendor": "Binance",
            "item_name": "BTC",
            "amount": 0.5,
            "total_spent": 30000.0,
            "currency": "CAD",
            "purchase_date": "2023-01-01",
            "transaction_type": "buy"
        },
        {
            "vendor": "Binance",
            "item_name": "BTC",
            "amount": 0.1,
            "total_spent": 6000.0,
            "currency": "CAD",
            "purchase_date": "2023-02-01",
            "transaction_type": "buy"
        },
        {
            "vendor": "Coinbase",
            "item_name": "ETH",
            "amount": 2.0,
            "total_spent": 5000.0,
            "currency": "CAD",
            "purchase_date": "2023-03-01",
            "transaction_type": "buy"
        }
    ]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        output_file = tmp.name

    try:
        write_purchase_data_to_cra_pdf(purchases, output_file)
        assert os.path.exists(output_file)
        assert os.path.getsize(output_file) > 0
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)

def test_write_purchase_data_to_cra_pdf_empty():
    purchases = []
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        output_file = tmp.name

    try:
        write_purchase_data_to_cra_pdf(purchases, output_file)
        # Should now create a file with "No transactions found"
        assert os.path.exists(output_file)
        assert os.path.getsize(output_file) > 0
    finally:
        if os.path.exists(output_file):
            os.remove(output_file)
