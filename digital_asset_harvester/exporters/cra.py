"""CRA-ready CSV writer for digital_asset_harvester."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from fpdf import FPDF
from fpdf.enums import XPos, YPos


class CRAReportGenerator:
    """Generator for CRA-ready CSV reports (e.g., for Wealthsimple Tax)."""

    def __init__(self, base_fiat_currency: str = "CAD"):
        self.base_fiat_currency = base_fiat_currency

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
            f"Sent Quantity ({self.base_fiat_currency})": str(purchase.get("fiat_amount_base", ""))
            if purchase.get("fiat_amount_base")
            else "",
            "Fee Quantity": str(purchase.get("fee_amount", "")) if purchase.get("fee_amount") is not None else "",
            "Fee Currency": purchase.get("fee_currency", ""),
            "Description": f"Transaction at {purchase.get('vendor', 'Unknown')}"
            + (f" (Asset ID: {purchase.get('asset_id')})" if purchase.get("asset_id") else ""),
        }
        return row

    def generate_csv_rows(self, purchases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate a list of CRA-ready CSV rows."""
        return [self._convert_purchase_to_cra_row(p) for p in purchases]


def write_purchase_data_to_cra_csv(
    purchases: List[Dict[str, Any]], output_file: str, base_fiat_currency: str = "CAD"
) -> None:
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
        f"Sent Quantity ({base_fiat_currency})",
        "Fee Quantity",
        "Fee Currency",
        "Description",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        generator = CRAReportGenerator(base_fiat_currency=base_fiat_currency)

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


class CRAPDFGenerator(FPDF):
    """PDF Generator for CRA reports."""

    def header(self) -> None:
        """Add report header."""
        self.set_font("helvetica", "B", 16)
        self.cell(0, 10, "CRA Digital Asset Purchase Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(10)

    def footer(self) -> None:
        """Add report footer."""
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")


def write_purchase_data_to_cra_pdf(
    purchases: List[Dict[str, Any]], output_file: str, base_fiat_currency: str = "CAD"
) -> None:
    """Write purchase data to a CRA-ready PDF file."""
    pdf = CRAPDFGenerator()
    pdf.alias_nb_pages()

    if not purchases:
        pdf.add_page()
        pdf.set_font("helvetica", size=12)
        pdf.cell(0, 10, "No transactions found.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.output(output_file)
        return

    purchase_dicts = []
    for p in purchases:
        if isinstance(p, dict):
            purchase_dicts.append(p)
        elif hasattr(p, "model_dump"):
            purchase_dicts.append(p.model_dump())
        else:
            purchase_dicts.append(vars(p))

    # Grouping logic
    # Key: (vendor, asset, currency)
    summary = defaultdict(lambda: {"quantity": 0.0, "total_spent": 0.0})

    for p in purchase_dicts:
        vendor = p.get("vendor") or "Unknown"
        asset = p.get("item_name") or "Unknown"
        try:
            amount = float(p.get("amount") or 0)
        except (ValueError, TypeError):
            amount = 0.0

        if p.get("fiat_amount_base"):
            spent = float(p["fiat_amount_base"])
            currency = base_fiat_currency
        else:
            try:
                spent = float(p.get("total_spent") or 0)
            except (ValueError, TypeError):
                spent = 0.0
            currency = p.get("currency") or "CAD"

        key = (vendor, asset, currency)
        summary[key]["quantity"] += amount
        summary[key]["total_spent"] += spent

    pdf.add_page()
    pdf.set_font("helvetica", size=12)

    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Summary by Exchange and Asset", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    # Group summary by currency then vendor for display
    currency_groups = defaultdict(lambda: defaultdict(list))
    for (vendor, asset, currency), data in summary.items():
        currency_groups[currency][vendor].append({"asset": asset, **data})

    for currency, vendors in currency_groups.items():
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, f"Currency: {currency}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)

        for vendor, items in vendors.items():
            pdf.set_font("helvetica", "B", 12)
            pdf.cell(0, 10, f"Exchange: {vendor}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("helvetica", size=10)

            # Table Header
            pdf.cell(40, 8, "Asset", border=1)
            pdf.cell(50, 8, "Total Quantity", border=1)
            pdf.cell(50, 8, "Total Spent", border=1)
            pdf.ln()

            currency_total = 0.0
            for item in items:
                pdf.cell(40, 8, str(item["asset"]), border=1)
                pdf.cell(50, 8, f"{item['quantity']:.8f}", border=1)
                pdf.cell(50, 8, f"{item['total_spent']:.2f}", border=1)
                pdf.ln()
                currency_total += item["total_spent"]

            # Subtotal for vendor in this currency
            pdf.set_font("helvetica", "B", 10)
            pdf.cell(90, 8, f"Total for {vendor} ({currency})", border=1)
            pdf.cell(50, 8, f"{currency_total:.2f}", border=1)
            pdf.ln(10)

    # Detailed Transactions
    pdf.add_page()
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Detailed Transactions", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)

    pdf.set_font("helvetica", size=8)
    # Header
    pdf.cell(25, 8, "Date", border=1)
    pdf.cell(25, 8, "Exchange", border=1)
    pdf.cell(20, 8, "Type", border=1)
    pdf.cell(20, 8, "Asset", border=1)
    pdf.cell(30, 8, "Asset ID", border=1)
    pdf.cell(20, 8, "Quantity", border=1)
    pdf.cell(25, 8, "Spent", border=1)
    pdf.cell(25, 8, f"Spent ({base_fiat_currency})", border=1)
    pdf.ln()

    for p in purchase_dicts:
        pdf.cell(25, 8, str(p.get("purchase_date") or ""), border=1)
        pdf.cell(25, 8, str(p.get("vendor") or "Unknown"), border=1)
        pdf.cell(20, 8, str(p.get("transaction_type") or "buy"), border=1)
        pdf.cell(20, 8, str(p.get("item_name") or ""), border=1)
        pdf.cell(30, 8, str(p.get("asset_id") or ""), border=1)
        pdf.cell(20, 8, str(p.get("amount") or ""), border=1)
        pdf.cell(25, 8, f"{p.get('total_spent') or ''} {p.get('currency') or ''}", border=1)
        pdf.cell(25, 8, f"{p.get('fiat_amount_base') or ''}", border=1)
        pdf.ln()

    pdf.output(output_file)
