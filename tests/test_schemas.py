from decimal import Decimal

import pytest
from pydantic import ValidationError

from digital_asset_harvester.validation.schemas import PurchaseRecord


def test_purchase_record_validate_handles_invalid_numeric():
    with pytest.raises(ValidationError):
        PurchaseRecord.model_validate(
            {
                "total_spent": "invalid",
                "currency": "USD",
                "amount": "0.01",
                "item_name": "BTC",
                "vendor": "Coinbase",
                "purchase_date": "2024-01-01 00:00:00 UTC",
            }
        )


def test_purchase_record_handles_none_strings():
    record = PurchaseRecord.model_validate(
        {
            "total_spent": "none",
            "currency": "null",
            "amount": "1.0",
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-01",
        }
    )
    assert record.total_spent is None
    assert record.currency == ""
