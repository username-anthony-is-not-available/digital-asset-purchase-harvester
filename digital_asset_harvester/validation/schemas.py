"""Data schemas for validation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional


@dataclass(frozen=True)
class PurchaseRecord:
    total_spent: Optional[Decimal]
    currency: str
    amount: Decimal
    item_name: str
    vendor: str
    purchase_date: str
    transaction_type: str = "buy"
    transaction_id: Optional[str] = None
    fee_amount: Optional[Decimal] = None
    fee_currency: Optional[str] = None
    extraction_notes: Optional[str] = None
    confidence: Optional[float] = None
    extraction_method: Optional[str] = None
    asset_id: Optional[str] = None

    @classmethod
    def from_raw(cls, data):
        try:
            total_spent_raw = data.get("total_spent")
            total_spent = (
                Decimal(str(total_spent_raw))
                if total_spent_raw is not None
                and str(total_spent_raw).strip() != ""
                and str(total_spent_raw).lower() != "none"
                and str(total_spent_raw).lower() != "null"
                else None
            )

            amount_raw = data.get("amount")
            amount = (
                Decimal(str(amount_raw))
                if amount_raw is not None
                and str(amount_raw).strip() != ""
                and str(amount_raw).lower() != "none"
                and str(amount_raw).lower() != "null"
                else None
            )

            fee_amount_raw = data.get("fee_amount")
            fee_amount = (
                Decimal(str(fee_amount_raw))
                if fee_amount_raw is not None
                and str(fee_amount_raw).strip() != ""
                and str(fee_amount_raw).lower() != "none"
                and str(fee_amount_raw).lower() != "null"
                else None
            )
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError("Invalid numeric value")

        confidence_val = data.get("confidence")
        if confidence_val is not None:
            try:
                confidence = float(confidence_val)
            except (ValueError, TypeError):
                confidence = None
        else:
            confidence = None

        currency_val = data.get("currency")
        return cls(
            total_spent=total_spent,
            currency=(
                str(currency_val)
                if currency_val is not None
                and str(currency_val).lower() != "none"
                and str(currency_val).lower() != "null"
                else ""
            ),
            amount=amount,
            item_name=str(data.get("item_name", "")),
            vendor=str(data.get("vendor", "")),
            purchase_date=str(data.get("purchase_date", "")),
            transaction_type=str(data.get("transaction_type", "buy")),
            transaction_id=str(data.get("transaction_id", "")) or None,
            fee_amount=fee_amount,
            fee_currency=str(data.get("fee_currency", "")) or None,
            extraction_notes=str(data.get("extraction_notes", "")) or None,
            confidence=confidence,
            extraction_method=data.get("extraction_method"),
            asset_id=str(data.get("asset_id", "")) or None,
        )
