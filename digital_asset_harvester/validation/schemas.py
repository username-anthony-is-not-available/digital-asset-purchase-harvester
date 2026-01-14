"""Data schemas for validation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional


@dataclass(frozen=True)
class PurchaseRecord:
    total_spent: Decimal
    currency: str
    amount: Decimal
    item_name: str
    vendor: str
    purchase_date: str
    confidence: Optional[float] = None
    extraction_method: Optional[str] = None

    @classmethod
    def from_raw(cls, data):
        try:
            total_spent = Decimal(str(data.get("total_spent")))
            amount = Decimal(str(data.get("amount")))
        except (InvalidOperation, TypeError):
            raise ValueError("Invalid numeric value")

        confidence_val = data.get("confidence")
        if confidence_val is not None:
            try:
                confidence = float(confidence_val)
            except (ValueError, TypeError):
                confidence = None
        else:
            confidence = None

        return cls(
            total_spent=total_spent,
            currency=str(data.get("currency", "")),
            amount=amount,
            item_name=str(data.get("item_name", "")),
            vendor=str(data.get("vendor", "")),
            purchase_date=str(data.get("purchase_date", "")),
            confidence=confidence,
            extraction_method=data.get("extraction_method"),
        )
