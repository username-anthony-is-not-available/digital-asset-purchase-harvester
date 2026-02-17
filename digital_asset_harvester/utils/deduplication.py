"""Utilities for deduplicating purchase records."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Optional, Set, Union


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


def generate_email_hash(email_data: Dict[str, Any]) -> str:
    """
    Generate a unique hash for an email based on its content.
    Used as a fallback when Message-ID is missing.
    """
    subject = str(email_data.get("subject", "")).strip()
    sender = str(email_data.get("sender", "")).strip()
    date = str(email_data.get("date", "")).strip()
    body = str(email_data.get("body", "")).strip()

    components = f"{subject}|{sender}|{date}|{body}"
    return hashlib.sha256(components.encode(errors="ignore")).hexdigest()


class DuplicateDetector:
    """Helper class to track seen records and identify duplicates."""

    def __init__(self, persistence_path: Optional[str] = None) -> None:
        self.seen_hashes: Set[str] = set()
        self.seen_emails: Set[str] = set()
        self.persistence_path = persistence_path
        if self.persistence_path:
            self.load_history()

    def is_duplicate(self, record: Dict[str, Any], auto_save: bool = True) -> bool:
        """Check if a record is a duplicate and mark it as seen."""
        record_hash = generate_record_hash(record)
        if record_hash in self.seen_hashes:
            return True
        self.seen_hashes.add(record_hash)
        if self.persistence_path and auto_save:
            self.save_history()
        return False

    def is_email_duplicate(self, email_data: Union[str, Dict[str, Any]], auto_save: bool = True) -> bool:
        """
        Check if an email has already been processed and mark it as seen.

        Args:
            email_data: Either a Message-ID string or a dictionary containing email metadata.
            auto_save: Whether to immediately persist the update to disk.

        Returns:
            True if the email has already been seen, False otherwise.
        """
        if not email_data:
            return False

        if isinstance(email_data, str):
            lookup_id = email_data
        else:
            email_id = email_data.get("message_id")
            # If Message-ID is missing or empty, fallback to content hash
            lookup_id = email_id if email_id and email_id.strip() else generate_email_hash(email_data)

        if lookup_id in self.seen_emails:
            return True

        self.seen_emails.add(lookup_id)
        if self.persistence_path and auto_save:
            self.save_history()
        return False

    def load_history(self) -> None:
        """Load seen hashes from a JSON file."""
        if self.persistence_path and os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.seen_hashes.update(data)
                    elif isinstance(data, dict):
                        self.seen_hashes.update(data.get("hashes", []))
                        self.seen_emails.update(data.get("emails", []))
            except Exception:
                # Fallback if file is corrupted
                pass

    def save_history(self) -> None:
        """Save seen hashes to a JSON file."""
        if self.persistence_path:
            try:
                # Use a temporary file for atomic write to avoid corruption
                temp_path = f"{self.persistence_path}.tmp"
                with open(temp_path, "w") as f:
                    data = {"hashes": list(self.seen_hashes), "emails": list(self.seen_emails)}
                    json.dump(data, f, indent=2)
                os.replace(temp_path, self.persistence_path)
            except Exception:
                if "temp_path" in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
                pass

    def reset(self) -> None:
        """Clear the set of seen hashes."""
        self.seen_hashes.clear()
        self.seen_emails.clear()
        if self.persistence_path and os.path.exists(self.persistence_path):
            try:
                os.remove(self.persistence_path)
            except Exception:
                pass
