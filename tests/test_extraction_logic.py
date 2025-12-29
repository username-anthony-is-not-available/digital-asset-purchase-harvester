from tests.fixtures.emails import EMAIL_FIXTURES
from digital_asset_harvester.processing.email_purchase_extractor import (
    EmailPurchaseExtractor,
)
from digital_asset_harvester.llm.provider import LLMResult


def test_extract_purchase_info(mocker):
    """
    Tests that purchase info is correctly extracted from an email.
    """
    email_content = EMAIL_FIXTURES["coinbase_purchase"]
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.return_value = LLMResult(
        data={
            "total_spent": 100.0,
            "currency": "USD",
            "amount": 0.001,
            "item_name": "BTC",
            "vendor": "Coinbase",
            "purchase_date": "2024-01-01 12:00:00",
            "confidence": 0.9,
            "extraction_notes": "",
        },
        raw_text="",
    )

    extractor = EmailPurchaseExtractor(llm_client=mock_llm_client)
    result = extractor.extract_purchase_info(email_content)

    assert result["total_spent"] == 100.0
    assert result["currency"] == "USD"
    assert result["amount"] == 0.001
    assert result["item_name"] == "BTC"
    assert result["vendor"] == "Coinbase"
    assert result["purchase_date"] == "2024-01-01 12:00:00 UTC"
