"""Utilities for deduplicating purchase records."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional


def generate_record_hash(record: Dict[str, Any]) -> str:
    """
    Generate a unique hash for a purchase record to help detect duplicates.

    Uses transaction_id if available, otherwise falls back to a hash of
    vendor, item_name, amount, and purchase_date.
    """
    if record.get("transaction_id"):
        return hashlib.sha256(str(record["transaction_id"]).strip().encode()).hexdigest()

    # Fallback to combination of fields
    # We normalize strings to lowercase and strip whitespace for better matching
    vendor = str(record.get("vendor", "")).lower().strip()
    item_name = str(record.get("item_name", "")).lower().strip()
    amount = str(record.get("amount", "")).strip()
    date = str(record.get("purchase_date", "")).strip()

    # Some dates might have different formats but represent the same time.
    # We rely on the extractor's date normalization if it has been run.

    components = f"{vendor}|{item_name}|{amount}|{date}"
    return hashlib.sha256(components.encode()).hexdigest()


class DuplicateDetector:
    """Helper class to track seen records and identify duplicates."""

    def __init__(self) -> None:
        self.seen_hashes: set[str] = set()

    def is_duplicate(self, record: Dict[str, Any]) -> bool:
        """Check if a record is a duplicate and mark it as seen."""
        record_hash = generate_record_hash(record)
        if record_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(record_hash)
        return False

    def reset(self) -> None:
        """Clear the set of seen hashes."""
        self.seen_hashes.clear()
