"""CSV output helpers."""
from __future__ import annotations

import csv
from typing import Any, Dict, Iterable, Union


def write_purchase_data_to_csv(filepath: str, records: Iterable[Union[object, Dict[str, Any]]], include_header: bool = True) -> None:
    """Write purchase records to a CSV file.

    - `records` can be an iterable of objects or dictionaries with the keys:
      `total_spent`, `currency`, `amount`, `item_name`, `vendor`, `purchase_date`,
      `transaction_id`, `transaction_type`, `fee_amount`, `fee_currency`, `extraction_notes`.
    - If `records` is empty, the function does not create a file.
    """
    records_list = list(records)
    if not records_list:
        return

    header = [
        "total_spent",
        "currency",
        "amount",
        "item_name",
        "vendor",
        "purchase_date",
        "transaction_id",
        "transaction_type",
        "fee_amount",
        "fee_currency",
        "extraction_notes",
    ]

    def _fmt(val):
        if val is None:
            return ""
        return str(val)

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if include_header:
            writer.writerow(header)
        for rec in records_list:
            if isinstance(rec, dict):
                row = [
                    _fmt(rec.get("total_spent")),
                    _fmt(rec.get("currency")),
                    _fmt(rec.get("amount")),
                    _fmt(rec.get("item_name")),
                    _fmt(rec.get("vendor")),
                    _fmt(rec.get("purchase_date")),
                    _fmt(rec.get("transaction_id")),
                    _fmt(rec.get("transaction_type", "buy")),
                    _fmt(rec.get("fee_amount")),
                    _fmt(rec.get("fee_currency")),
                    _fmt(rec.get("extraction_notes")),
                ]
            else:
                row = [
                    _fmt(getattr(rec, "total_spent", None)),
                    _fmt(getattr(rec, "currency", None)),
                    _fmt(getattr(rec, "amount", None)),
                    _fmt(getattr(rec, "item_name", None)),
                    _fmt(getattr(rec, "vendor", None)),
                    _fmt(getattr(rec, "purchase_date", None)),
                    _fmt(getattr(rec, "transaction_id", None)),
                    _fmt(getattr(rec, "transaction_type", "buy")),
                    _fmt(getattr(rec, "fee_amount", None)),
                    _fmt(getattr(rec, "fee_currency", None)),
                    _fmt(getattr(rec, "extraction_notes", None)),
                ]
            writer.writerow(row)
