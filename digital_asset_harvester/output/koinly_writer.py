"""Koinly CSV output helpers."""
from __future__ import annotations

import csv
from datetime import datetime
from typing import Iterable, Dict, Any


class KoinlyReportGenerator:
    """Generate Koinly-compatible CSV reports from purchase data."""

    def format_transaction(self, purchase: Dict[str, Any]) -> Dict[str, str]:
        """Convert a purchase record to Koinly Universal CSV format.
        
        Koinly Universal format requires:
        - Date: YYYY-MM-DD HH:mm:ss (UTC)
        - Sent Amount: Amount sent (for purchases, this is fiat)
        - Sent Currency: Currency sent (e.g., USD, EUR)
        - Received Amount: Amount received (crypto amount)
        - Received Currency: Crypto symbol (e.g., BTC, ETH)
        - Fee Amount: (optional)
        - Fee Currency: (optional)
        - Label: Transaction type (e.g., "trade", "buy")
        - TxHash: (optional) Transaction hash
        """
        # Parse the date and format it properly
        purchase_date = purchase.get("purchase_date", "")
        try:
            # Try to parse and format the date to Koinly's expected format
            if purchase_date:
                # Handle various date formats
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"]:
                    try:
                        parsed_date = datetime.strptime(purchase_date, fmt)
                        formatted_date = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                        break
                    except ValueError:
                        continue
                else:
                    # If no format matched, use the original
                    formatted_date = purchase_date
            else:
                formatted_date = ""
        except Exception:
            formatted_date = purchase_date

        return {
            "Date": formatted_date,
            "Sent Amount": str(purchase.get("total_spent", "")),
            "Sent Currency": purchase.get("currency", ""),
            "Received Amount": str(purchase.get("amount", "")),
            "Received Currency": purchase.get("item_name", ""),
            "Fee Amount": "",
            "Fee Currency": "",
            "Label": "buy",
            "TxHash": "",
        }

    def generate_csv_data(self, purchases: Iterable[Dict[str, Any]]) -> list[Dict[str, str]]:
        """Convert purchase records to Koinly format."""
        return [self.format_transaction(purchase) for purchase in purchases]


def write_purchase_data_to_koinly_csv(
    records: Iterable[Dict[str, Any]], 
    filepath: str, 
    include_header: bool = True
) -> None:
    """Write purchase records to a Koinly-compatible CSV file.
    
    Args:
        records: An iterable of purchase dictionaries with keys:
                 total_spent, currency, amount, item_name, vendor, purchase_date
        filepath: Path to the output CSV file
        include_header: Whether to include column headers (default: True)
    """
    records_list = list(records)
    if not records_list:
        return

    generator = KoinlyReportGenerator()
    koinly_records = generator.generate_csv_data(records_list)

    # Koinly Universal CSV format headers
    headers = [
        "Date",
        "Sent Amount",
        "Sent Currency",
        "Received Amount",
        "Received Currency",
        "Fee Amount",
        "Fee Currency",
        "Label",
        "TxHash",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        if include_header:
            writer.writeheader()
        writer.writerows(koinly_records)
