"""Blockchain-Tax-Calculator CSV writer for digital_asset_harvester."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from typing import Any, Dict, List

from dateutil import parser


class BlockchainTaxCalculatorReportGenerator:
    """Generator for Blockchain-Tax-Calculator compatible CSV reports."""

    def _format_date(self, date_str: str) -> str:
        """Format date string to required format (YYYY-MM-DD HH:MM:SS)."""
        if not date_str:
            return ""
        try:
            dt = parser.parse(date_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError, parser.ParserError):
            return date_str

    def _convert_purchase_to_btc_row(self, purchase: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a single purchase record to a Blockchain-Tax-Calculator CSV row."""
        tx_type = purchase.get("transaction_type", "buy")

        # Mapping
        btc_type = {
            "buy": "Buy",
            "deposit": "Deposit",
            "withdrawal": "Withdraw",
            "staking_reward": "Staking",
        }.get(tx_type, "Buy")

        row = {
            "Date": self._format_date(purchase.get("purchase_date", "")),
            "Type": btc_type,
            "Amount": str(purchase.get("amount", "")),
            "Asset": purchase.get("item_name", ""),
            "Quote Amount": str(purchase.get("total_spent", "")),
            "Quote Asset": purchase.get("currency", ""),
            "Fee": str(purchase.get("fee_amount", "")) if purchase.get("fee_amount") is not None else "",
            "Fee Asset": purchase.get("fee_currency", ""),
            "ID": purchase.get("transaction_id", ""),
            "Description": f"Extracted from {purchase.get('vendor', 'Unknown')}"
            + (f" (Asset ID: {purchase.get('asset_id')})" if purchase.get("asset_id") else ""),
        }
        return row

    def generate_csv_rows(self, purchases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate a list of Blockchain-Tax-Calculator compatible CSV rows."""
        return [self._convert_purchase_to_btc_row(p) for p in purchases]


def write_purchase_data_to_blockchain_tax_csv(purchases: List[Dict[str, Any]], output_file: str) -> None:
    """Write purchase data to a Blockchain-Tax-Calculator compatible CSV file."""
    if not purchases:
        return

    fieldnames = [
        "Date",
        "Type",
        "Amount",
        "Asset",
        "Quote Amount",
        "Quote Asset",
        "Fee",
        "Fee Asset",
        "ID",
        "Description",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        generator = BlockchainTaxCalculatorReportGenerator()

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
