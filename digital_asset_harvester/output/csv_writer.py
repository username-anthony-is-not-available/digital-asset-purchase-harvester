"""CSV output helpers."""
from __future__ import annotations

import csv
from typing import Iterable


def write_purchase_data_to_csv(filepath: str, records: Iterable[object], include_header: bool = True) -> None:
    """Write purchase records to a CSV file.

    - `records` should be an iterable of objects with the attributes:
      `total_spent`, `currency`, `amount`, `item_name`, `vendor`, `purchase_date`.
    - If `records` is empty, the function does not create a file.
    """
    records_list = list(records)
    if not records_list:
        return

    header = ["total_spent", "currency", "amount", "item_name", "vendor", "purchase_date"]

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if include_header:
            writer.writerow(header)
        for rec in records_list:
            writer.writerow(
                [
                    str(rec.total_spent),
                    rec.currency,
                    str(rec.amount),
                    rec.item_name,
                    rec.vendor,
                    rec.purchase_date,
                ]
            )
