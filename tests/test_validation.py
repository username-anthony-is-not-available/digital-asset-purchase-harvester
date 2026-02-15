"""Tests for purchase validation utilities."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from digital_asset_harvester.validation import PurchaseRecord, PurchaseValidator


def test_purchase_record_validate_converts_values():
    record = PurchaseRecord.model_validate(
        {
            "total_spent": "100.50",
            "currency": "USD",
            "amount": "0.01",
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-01 00:00:00 UTC",
        }
    )

    assert record.total_spent == Decimal("100.50")
    assert record.amount == Decimal("0.01")


def test_purchase_validator_detects_issues():
    data = {
        "total_spent": "-1",
        "currency": "invalid",
        "amount": "0",
        "item_name": "UnknownCoin",
        "vendor": "",
        "purchase_date": "",
    }

    # Use validate_raw to catch all issues including Pydantic ones
    issues = PurchaseValidator.validate_raw(data, allow_unknown_crypto=False)
    fields = {issue.field for issue in issues}

    assert {
        "total_spent",
        "currency",
        "amount",
        "item_name",
        "vendor",
        "purchase_date",
    } == fields


def test_purchase_record_validation_error():
    with pytest.raises(ValidationError):
        PurchaseRecord.model_validate(
            {
                "amount": "-1",  # Invalid
                "item_name": "BTC",
                "vendor": "Coinbase",
                "purchase_date": "2024-01-01",
            }
        )
