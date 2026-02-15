"""Validation utilities for purchase data using Pydantic V2."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from pydantic import ValidationError

from .schemas import KNOWN_CRYPTO_NAMES, PurchaseRecord

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str


class PurchaseValidator:
    def __init__(self, *, allow_unknown_crypto: bool = True) -> None:
        self.allow_unknown_crypto = allow_unknown_crypto

    def validate(self, record: PurchaseRecord) -> List[ValidationIssue]:
        """
        Validate a PurchaseRecord.
        Note: PurchaseRecord already performs most validations on instantiation/validation.
        This method captures those and adds any extra checks (like known cryptos).
        """
        issues: List[ValidationIssue] = []

        # If we have a record, it might have been created without context.
        # So we re-check known cryptos here if needed.
        if record.item_name:
            lower_item = record.item_name.lower()
            if lower_item not in KNOWN_CRYPTO_NAMES and not self.allow_unknown_crypto:
                issues.append(ValidationIssue("item_name", "unknown cryptocurrency"))

        return issues

    @classmethod
    def validate_raw(cls, data: dict, allow_unknown_crypto: bool = True) -> List[ValidationIssue]:
        """Validate raw data and return a list of issues."""
        issues: List[ValidationIssue] = []
        try:
            # Use Pydantic to validate, passing allow_unknown_crypto in context
            PurchaseRecord.model_validate(
                data, context={"allow_unknown_crypto": allow_unknown_crypto}
            )
            # We don't need to call validator.validate() here because Pydantic
            # now handles the unknown crypto check if context is provided.
        except ValidationError as e:
            for error in e.errors():
                # Get the field name from loc
                field = str(error["loc"][0]) if error["loc"] else "unknown"
                message = error["msg"]
                # Clean up "Value error, " prefix from Pydantic custom validators
                if message.startswith("Value error, "):
                    message = message[len("Value error, ") :]
                issues.append(ValidationIssue(field, message))

        return issues
