from decimal import Decimal
import pytest
from digital_asset_harvester.validation.schemas import PurchaseRecord


def test_purchase_record_from_raw_handles_invalid_numeric():
    with pytest.raises(ValueError):
        PurchaseRecord.from_raw(
            {
                "total_spent": "invalid",
                "currency": "USD",
                "amount": "0.01",
                "item_name": "BTC",
                "vendor": "Coinbase",
                "purchase_date": "2024-01-01 00:00:00 UTC",
            }
        )
