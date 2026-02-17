"""CoinTracker CSV writer for digital_asset_harvester."""

from __future__ import annotations

import csv
from datetime import datetime
from typing import Any, Dict, List


class CoinTrackerReportGenerator:
    """Generator for CoinTracker-compatible CSV reports."""

    def _format_date(self, date_str: str) -> str:
        """Format date string to CoinTracker's required format (MM/DD/YYYY HH:MM:SS)."""
        if not date_str:
            return ""
        try:
            from dateutil import parser

            dt = parser.parse(date_str)
            return dt.strftime("%m/%d/%Y %H:%M:%S")
        except (ValueError, TypeError, ImportError):
            try:
                if " " in date_str:
                    parts = date_str.split()
                    if len(parts) > 2:
                        date_str = " ".join(parts[:2])
                    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                else:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.strftime("%m/%d/%Y %H:%M:%S")
            except (ValueError, TypeError):
                return date_str

    def _convert_purchase_to_cointracker_row(self, purchase: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single purchase record to a CoinTracker CSV row."""
        tx_type = purchase.get("transaction_type", "buy")

        # CoinTracker Universal format:
        # Date,Received Quantity,Received Currency,Sent Quantity,Sent Currency,Fee Quantity,Fee Currency,Tag
        row = {
            "Date": self._format_date(purchase.get("purchase_date", "")),
            "Received Quantity": str(purchase.get("amount", "")),
            "Received Currency": purchase.get("item_name", ""),
            "Sent Quantity": "",
            "Sent Currency": "",
            "Fee Quantity": str(purchase.get("fee_amount", "")) if purchase.get("fee_amount") is not None else "",
            "Fee Currency": purchase.get("fee_currency", ""),
            "Tag": "",
        }

        if tx_type == "deposit":
            pass  # Received only
        elif tx_type == "withdrawal":
            row.update(
                {
                    "Received Quantity": "",
                    "Received Currency": "",
                    "Sent Quantity": str(purchase.get("amount", "")),
                    "Sent Currency": purchase.get("item_name", ""),
                }
            )
        elif tx_type == "staking_reward":
            row["Tag"] = "staked"
        else:  # Default to buy
            row.update(
                {
                    "Sent Quantity": str(purchase.get("total_spent", "")),
                    "Sent Currency": purchase.get("currency", ""),
                }
            )

        return row

    def generate_csv_rows(self, purchases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate a list of CoinTracker-compatible CSV rows."""
        return [self._convert_purchase_to_cointracker_row(p) for p in purchases]


def write_purchase_data_to_cointracker_csv(purchases: List[Dict[str, Any]], output_file: str) -> None:
    """Write purchase data to a CoinTracker-compatible CSV file."""
    if not purchases:
        return

    fieldnames = [
        "Date",
        "Received Quantity",
        "Received Currency",
        "Sent Quantity",
        "Sent Currency",
        "Fee Quantity",
        "Fee Currency",
        "Tag",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        generator = CoinTrackerReportGenerator()

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
