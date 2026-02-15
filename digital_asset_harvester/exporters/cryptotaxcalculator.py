"""CryptoTaxCalculator CSV writer for digital_asset_harvester."""

from __future__ import annotations

import csv
from datetime import datetime
from typing import Any, Dict, List


class CryptoTaxCalculatorReportGenerator:
    """Generator for CryptoTaxCalculator-compatible CSV reports."""

    def _format_date(self, date_str: str) -> str:
        """Format date string to CTC's required format."""
        # CTC often expects 'YYYY-MM-DD HH:MM:SS' or ISO format
        if not date_str:
            return ""
        try:
            if " " in date_str:
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            else:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return date_str

    def _convert_purchase_to_ctc_row(self, purchase: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single purchase record to a CTC CSV row."""
        tx_type = purchase.get("transaction_type", "buy")

        # Mapping
        ctc_type = {
            "buy": "Buy",
            "deposit": "Deposit",
            "withdrawal": "Withdraw",
            "staking_reward": "Staking",
        }.get(tx_type, "Buy")

        row = {
            "Timestamp (UTC)": self._format_date(purchase.get("purchase_date", "")),
            "Type": ctc_type,
            "Base Currency": purchase.get("item_name", ""),
            "Base Amount": str(purchase.get("amount", "")),
            "Quote Currency": purchase.get("currency", ""),
            "Quote Amount": str(purchase.get("total_spent", "")),
            "Fee Currency": purchase.get("fee_currency", ""),
            "Fee Amount": str(purchase.get("fee_amount", "")) if purchase.get("fee_amount") is not None else "",
            "From": purchase.get("vendor", ""),
            "To": "",
            "ID": purchase.get("transaction_id", ""),
            "Description": f"Extracted from {purchase.get('vendor', 'Unknown')}" + (f" (Asset ID: {purchase.get('asset_id')})" if purchase.get('asset_id') else ""),
        }
        return row

    def generate_csv_rows(self, purchases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate a list of CTC-compatible CSV rows."""
        return [self._convert_purchase_to_ctc_row(p) for p in purchases]


def write_purchase_data_to_ctc_csv(purchases: List[Dict[str, Any]], output_file: str) -> None:
    """Write purchase data to a CTC-compatible CSV file."""
    if not purchases:
        return

    fieldnames = [
        "Timestamp (UTC)",
        "Type",
        "Base Currency",
        "Base Amount",
        "Quote Currency",
        "Quote Amount",
        "Fee Currency",
        "Fee Amount",
        "From",
        "To",
        "ID",
        "Description",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        generator = CryptoTaxCalculatorReportGenerator()

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
