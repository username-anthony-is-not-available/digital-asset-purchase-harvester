"""CRA-ready CSV writer for digital_asset_harvester."""

from __future__ import annotations

import csv
from datetime import datetime
from typing import Any, Dict, List


class CRAReportGenerator:
    """Generator for CRA-ready CSV reports (e.g., for Wealthsimple Tax)."""

    def _convert_purchase_to_cra_row(self, purchase: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single purchase record to a CRA-ready CSV row."""
        tx_type = purchase.get("transaction_type", "buy")

        # Mapping
        cra_type = {
            "buy": "Buy",
            "deposit": "Deposit",
            "withdrawal": "Withdraw",
            "staking_reward": "Staking",
        }.get(tx_type, "Buy")

        row = {
            "Date": purchase.get("purchase_date", ""),
            "Type": cra_type,
            "Received Quantity": str(purchase.get("amount", "")),
            "Received Currency": purchase.get("item_name", ""),
            "Sent Quantity": str(purchase.get("total_spent", "")),
            "Sent Currency": purchase.get("currency", ""),
            "Fee Quantity": str(purchase.get("fee_amount", "")) if purchase.get("fee_amount") is not None else "",
            "Fee Currency": purchase.get("fee_currency", ""),
            "Description": f"Transaction at {purchase.get('vendor', 'Unknown')}",
        }
        return row

    def generate_csv_rows(self, purchases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate a list of CRA-ready CSV rows."""
        return [self._convert_purchase_to_cra_row(p) for p in purchases]


def write_purchase_data_to_cra_csv(purchases: List[Dict[str, Any]], output_file: str) -> None:
    """Write purchase data to a CRA-ready CSV file."""
    if not purchases:
        return

    fieldnames = [
        "Date",
        "Type",
        "Received Quantity",
        "Received Currency",
        "Sent Quantity",
        "Sent Currency",
        "Fee Quantity",
        "Fee Currency",
        "Description",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        generator = CRAReportGenerator()

        purchase_dicts = []
        for p in purchases:
            if isinstance(p, dict):
                purchase_dicts.append(p)
            else:
                purchase_dicts.append(vars(p))

        rows = generator.generate_csv_rows(purchase_dicts)
        writer.writerows(rows)
