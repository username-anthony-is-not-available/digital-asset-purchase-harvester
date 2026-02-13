"""CSV output helpers."""
from __future__ import annotations

import csv
from typing import Any, Dict, Iterable, Union


def write_purchase_data_to_csv(filepath: str, records: Iterable[Union[object, Dict[str, Any]]], include_header: bool = True) -> None:
    """Write purchase records to a CSV file.

    - `records` can be an iterable of objects or dictionaries with the keys:
      `total_spent`, `currency`, `amount`, `item_name`, `vendor`, `purchase_date`,
      `transaction_id`, `transaction_type`.
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
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if include_header:
            writer.writerow(header)
        for rec in records_list:
            if isinstance(rec, dict):
                row = [
                    str(rec.get("total_spent", "")),
                    rec.get("currency", ""),
                    str(rec.get("amount", "")),
                    rec.get("item_name", ""),
                    rec.get("vendor", ""),
                    rec.get("purchase_date", ""),
                    rec.get("transaction_id", ""),
                    rec.get("transaction_type", "buy"),
                ]
            else:
                row = [
                    str(getattr(rec, "total_spent", "")),
                    getattr(rec, "currency", ""),
                    str(getattr(rec, "amount", "")),
                    getattr(rec, "item_name", ""),
                    getattr(rec, "vendor", ""),
                    getattr(rec, "purchase_date", ""),
                    getattr(rec, "transaction_id", ""),
                    getattr(rec, "transaction_type", "buy"),
                ]
            writer.writerow(row)
