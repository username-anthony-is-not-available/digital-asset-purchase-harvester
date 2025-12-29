from tests.fixtures.emails import EMAIL_FIXTURES
from digital_asset_harvester.processing.email_purchase_extractor import (
    EmailPurchaseExtractor,
)


def test_process_email_non_purchase(mocker):
    """
    Tests that a non-purchase email is correctly classified.
    """
    email_content = EMAIL_FIXTURES["non_purchase"]
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.return_value = mocker.Mock(
        data={
            "is_crypto_purchase": False,
            "confidence": 0.9,
            "reasoning": "Price alert",
        }
    )
    mocker.patch(
        "digital_asset_harvester.processing.email_purchase_extractor.get_llm_client",
        return_value=mock_llm_client,
    )

    extractor = EmailPurchaseExtractor()
    result = extractor.process_email(email_content)
    assert not result["has_purchase"]
