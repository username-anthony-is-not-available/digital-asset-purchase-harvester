"""Tests for purchase validation utilities."""

from decimal import Decimal

from digital_asset_harvester.validation import PurchaseRecord, PurchaseValidator


def test_purchase_record_from_raw_converts_values():
    record = PurchaseRecord.from_raw(
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
    validator = PurchaseValidator(allow_unknown_crypto=False)
    record = PurchaseRecord(
        total_spent=Decimal("-1"),
        currency="usd",
        amount=Decimal("0"),
        item_name="UnknownCoin",
        vendor="",
        purchase_date="",
    )

    issues = validator.validate(record)
    fields = {issue.field for issue in issues}

    assert fields == {"total_spent", "amount", "item_name", "vendor", "purchase_date"}
