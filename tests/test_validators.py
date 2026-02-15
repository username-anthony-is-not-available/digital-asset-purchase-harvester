from decimal import Decimal

from digital_asset_harvester.validation import PurchaseRecord, PurchaseValidator


def test_purchase_validator_handles_known_crypto():
    validator = PurchaseValidator(allow_unknown_crypto=False)
    record = PurchaseRecord(
        total_spent=Decimal("100.00"),
        currency="USD",
        amount=Decimal("1.0"),
        item_name="BTC",
        vendor="TestVendor",
        purchase_date="2023-01-01",
    )
    issues = validator.validate(record)
    assert not issues


def test_purchase_validator_handles_unknown_crypto():
    validator = PurchaseValidator(allow_unknown_crypto=False)
    record = PurchaseRecord(
        total_spent=Decimal("100.00"),
        currency="USD",
        amount=Decimal("1.0"),
        item_name="MagicToken",
        vendor="TestVendor",
        purchase_date="2023-01-01",
    )
    issues = validator.validate(record)
    assert len(issues) == 1
    assert issues[0].field == "item_name"
    assert issues[0].message == "unknown cryptocurrency"
