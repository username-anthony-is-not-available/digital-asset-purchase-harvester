"""Koinly CSV output helpers."""

from __future__ import annotations

import csv
from typing import Iterable


class KoinlyReportGenerator:
    """Generator for Koinly-formatted CSV reports.

    Note: This is a placeholder implementation. The Koinly export feature
    is controlled by the enable_koinly_csv_export setting.
    """

    def generate(self, records: Iterable[object]) -> list[dict]:
        """Generate Koinly-formatted records.

        Args:
            records: Purchase records to convert to Koinly format

        Returns:
            List of dictionaries in Koinly universal CSV format

        Note: This is a placeholder that returns an empty list.
        Actual implementation would convert purchase records to Koinly format.
        """
        return []


def write_purchase_data_to_koinly_csv(records: Iterable[object], filepath: str) -> None:
    """Write purchase records to a Koinly-compatible CSV file.

    This is a placeholder implementation for the Koinly CSV export feature.
    """
    records_list = list(records)
    if not records_list:
        return

    # Koinly universal format headers
    header = [
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

    with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        # Placeholder - would need actual conversion logic
