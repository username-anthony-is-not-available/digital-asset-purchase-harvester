import pytest

from digital_asset_harvester.processing.extractors.coinspot import CoinSpotExtractor
from tests.fixtures.emails import EMAIL_FIXTURES


def test_coinspot_extractor():
    extractor = CoinSpotExtractor()
    email = EMAIL_FIXTURES["coinspot_purchase"]
    subject = "Purchase Confirmation"
    sender = "CoinSpot <support@coinspot.com.au>"
    body = email

    assert extractor.can_handle(subject, sender, body) is True
    results = extractor.extract(subject, sender, body)
    assert len(results) == 1
    assert results[0]["amount"] == "50"
    assert results[0]["item_name"] == "ADA"
    assert results[0]["total_spent"] == "25.00"
    assert results[0]["currency"] == "AUD"
    assert results[0]["vendor"] == "CoinSpot"
    assert results[0]["transaction_id"] == "CS-20240115-001"
