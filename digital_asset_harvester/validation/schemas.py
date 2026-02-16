"""Data schemas for validation using Pydantic V2."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, ValidationInfo, field_validator

ISO_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3,5}$")
CRYPTO_SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{2,10}$")

KNOWN_CRYPTO_NAMES = {
    "bitcoin",
    "btc",
    "ethereum",
    "eth",
    "litecoin",
    "ltc",
    "solana",
    "sol",
    "dogecoin",
    "doge",
    "cardano",
    "ada",
    "polkadot",
    "dot",
    "ripple",
    "xrp",
    "binance coin",
    "bnb",
    "tether",
    "usdt",
    "usd coin",
    "usdc",
}


class PurchaseRecord(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        coerce_numbers_to_str=True,
        validate_default=True,
    )

    total_spent: Optional[Decimal] = None
    currency: str = ""
    amount: Decimal
    item_name: str = ""
    vendor: str = ""
    purchase_date: str = ""
    transaction_type: str = "buy"
    transaction_id: Optional[str] = None
    fee_amount: Optional[Decimal] = None
    fee_currency: Optional[str] = None
    extraction_notes: Optional[str] = None
    confidence: Optional[float] = None
    extraction_method: Optional[str] = None
    asset_id: Optional[str] = None
    fiat_amount_cad: Optional[Decimal] = None

    @field_validator("total_spent", "amount", "fee_amount", "fiat_amount_cad", mode="before")
    @classmethod
    def parse_decimal_fields(cls, v: Any) -> Any:
        if v is None:
            return None
        s = str(v).strip().lower()
        if s == "" or s == "none" or s == "null":
            return None
        return v

    @field_validator(
        "currency",
        "item_name",
        "vendor",
        "purchase_date",
        "transaction_type",
        "transaction_id",
        "fee_currency",
        "extraction_notes",
        "asset_id",
        mode="before",
    )
    @classmethod
    def parse_string_fields(cls, v: Any) -> str:
        if v is None:
            return ""
        s = str(v).strip()
        if s.lower() == "none" or s.lower() == "null":
            return ""
        return s

    @field_validator("confidence", mode="before")
    @classmethod
    def parse_confidence(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        s = str(v).strip().lower()
        if s == "" or s == "none" or s == "null":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator("total_spent", "fiat_amount_cad")
    @classmethod
    def validate_non_negative_fiat(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < Decimal("0"):
            raise ValueError("must be non-negative")
        return v

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("must be greater than zero")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        if v and not ISO_CURRENCY_PATTERN.match(v.upper()):
            raise ValueError("must be ISO 4217 uppercase code")
        return v

    @field_validator("item_name")
    @classmethod
    def validate_item_name(cls, v: str, info: ValidationInfo) -> str:
        if not v.strip():
            raise ValueError("is required")

        # Optional check for known cryptos via context
        if info.context:
            allow_unknown = info.context.get("allow_unknown_crypto", True)
            if not allow_unknown and v.lower() not in KNOWN_CRYPTO_NAMES:
                raise ValueError("unknown cryptocurrency")

        return v

    @field_validator("vendor")
    @classmethod
    def validate_vendor(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("is required")
        return v

    @field_validator("purchase_date")
    @classmethod
    def validate_purchase_date(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("is required")
        return v

    @field_validator("fee_amount")
    @classmethod
    def validate_fee_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None and v < Decimal("0"):
            raise ValueError("must be non-negative")
        return v

    @field_validator("fee_currency")
    @classmethod
    def validate_fee_currency(cls, v: Optional[str]) -> Optional[str]:
        if v:
            if not ISO_CURRENCY_PATTERN.match(v.upper()) and not CRYPTO_SYMBOL_PATTERN.match(v.upper()):
                raise ValueError("must be valid currency code or symbol")
        return v
