"""Koinly CSV writer for digital_asset_harvester."""

from __future__ import annotations

import csv
from typing import Any, Dict, List


class KoinlyReportGenerator:
    """Generator for Koinly-compatible CSV reports."""

    def __init__(self) -> None:
        """Initialize the Koinly report generator."""
        pass

    def generate_report(self, purchases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate Koinly-compatible report from purchase data."""
        # Placeholder implementation
        return purchases


def write_purchase_data_to_koinly_csv(purchases: List[Dict[str, Any]], output_file: str) -> None:
    """Write purchase data to a Koinly-compatible CSV file."""
    if not purchases:
        return

    # Koinly universal format columns
    fieldnames = [
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

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for purchase in purchases:
            # Map our purchase data to Koinly format
            row = {
                "Date": purchase.get("date", ""),
                "Sent Amount": purchase.get("amount", ""),
                "Sent Currency": purchase.get("fiat_currency", "USD"),
                "Received Amount": purchase.get("crypto_amount", ""),
                "Received Currency": purchase.get("currency", ""),
                "Fee Amount": "",
                "Fee Currency": "",
                "Net Worth Amount": "",
                "Net Worth Currency": "",
                "Label": "buy",
                "Description": (f"Purchase from {purchase.get('vendor', 'Unknown')}"),
                "TxHash": purchase.get("transaction_id", ""),
            }
            writer.writerow(row)
