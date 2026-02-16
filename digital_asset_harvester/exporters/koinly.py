"""Koinly CSV writer for digital_asset_harvester."""

from __future__ import annotations

import csv
from datetime import datetime
from typing import Any, Dict, List


class KoinlyReportGenerator:
    """Generator for Koinly-compatible CSV reports."""

    def _format_date(self, date_str: str) -> str:
        """Format date string to Koinly's required format."""
        if not date_str:
            return ""
        try:
            if " " in date_str:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            try:
                dt = datetime.strptime(date_str, "%Y/%m/%d")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                return date_str

    def _convert_purchase_to_koinly_row(self, purchase: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single purchase record to a Koinly CSV row."""
        tx_type = purchase.get("transaction_type", "buy")
        row = {
            "Date": self._format_date(purchase.get("purchase_date", "")),
            "Fee Amount": str(purchase.get("fee_amount", "")) if purchase.get("fee_amount") is not None else "",
            "Fee Currency": purchase.get("fee_currency", ""),
            "Net Worth Amount": "",
            "Net Worth Currency": "",
            "Description": f"{tx_type.capitalize()} from {purchase.get('vendor', 'Unknown')}"
            + (f" (Asset ID: {purchase.get('asset_id')})" if purchase.get("asset_id") else ""),
            "TxHash": purchase.get("transaction_id", ""),
        }

        if tx_type == "deposit":
            row.update(
                {
                    "Label": "deposit",
                    "Sent Amount": "",
                    "Sent Currency": "",
                    "Received Amount": str(purchase.get("amount", "")),
                    "Received Currency": purchase.get("item_name", ""),
                }
            )
        elif tx_type == "withdrawal":
            row.update(
                {
                    "Label": "withdrawal",
                    "Sent Amount": str(purchase.get("amount", "")),
                    "Sent Currency": purchase.get("item_name", ""),
                    "Received Amount": "",
                    "Received Currency": "",
                }
            )
        elif tx_type == "staking_reward":
            row.update(
                {
                    "Label": "staking",
                    "Sent Amount": "",
                    "Sent Currency": "",
                    "Received Amount": str(purchase.get("amount", "")),
                    "Received Currency": purchase.get("item_name", ""),
                }
            )
        else:  # Default to buy
            row.update(
                {
                    "Label": "buy",
                    "Sent Amount": str(purchase.get("total_spent", "")),
                    "Sent Currency": purchase.get("currency", ""),
                    "Received Amount": str(purchase.get("amount", "")),
                    "Received Currency": purchase.get("item_name", ""),
                }
            )

        return row

    def generate_csv_rows(self, purchases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate a list of Koinly-compatible CSV rows."""
        return [self._convert_purchase_to_koinly_row(p) for p in purchases]


def write_purchase_data_to_koinly_csv(purchases: List[Dict[str, Any]], output_file: str) -> None:
    """Write purchase data to a Koinly-compatible CSV file."""
    if not purchases:
        return

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
        generator = KoinlyReportGenerator()

        # Handle both dicts and objects
        purchase_dicts = []
        for p in purchases:
            if isinstance(p, dict):
                purchase_dicts.append(p)
            elif hasattr(p, "model_dump"):
                purchase_dicts.append(p.model_dump())
            else:
                purchase_dicts.append(vars(p))

        rows = generator.generate_csv_rows(purchase_dicts)
        writer.writerows(rows)
