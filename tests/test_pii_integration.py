"""Integration tests for PII scrubbing in EmailPurchaseExtractor."""

import pytest

from digital_asset_harvester.config import get_settings_with_overrides
from digital_asset_harvester.processing.email_purchase_extractor import EmailPurchaseExtractor


def test_pii_scrubbing_integration(mocker):
    # Setup
    email_content = (
        "Subject: Your purchase from Coinbase\n"
        "From: no-reply@coinbase.com\n"
        "Body: Hi John Doe, you bought 0.1 BTC. "
        "It was shipped to 123 Main St. "
        "Contact us at support@coinbase.com or 555-555-1234."
    )

    mock_llm_client = mocker.Mock()
    # Mock return values for both classification and extraction
    mock_llm_client.generate_json.side_effect = [
        mocker.Mock(data={"is_crypto_purchase": True, "confidence": 0.9, "reasoning": "Test"}),
        mocker.Mock(
            data={
                "transactions": [
                    {
                        "item_name": "BTC",
                        "amount": 0.1,
                        "vendor": "Coinbase",
                        "total_spent": 100,
                        "currency": "USD",
                        "purchase_date": "2024-01-01",
                        "confidence": 0.9,
                    }
                ]
            }
        ),
    ]

    # Enable PII scrubbing
    settings = get_settings_with_overrides(
        enable_pii_scrubbing=True,
        enable_preprocessing=False,  # Skip preprocessing to focus on LLM call
        enable_regex_extractors=False,  # Force LLM fallback
    )

    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)

    # Execute
    extractor.process_email(email_content)

    # Verify
    # Check that generate_json was called twice (classification and extraction)
    assert mock_llm_client.generate_json.call_count == 2

    for call in mock_llm_client.generate_json.call_args_list:
        prompt = call.args[0]
        # Verify that PII is masked in the prompt
        assert "[NAME]" in prompt
        assert "[ADDRESS]" in prompt
        assert "[EMAIL]" in prompt
        assert "[PHONE]" in prompt

        # Verify that original PII is NOT in the prompt
        assert "John Doe" not in prompt
        assert "123 Main St" not in prompt
        assert "support@coinbase.com" not in prompt
        assert "555-555-1234" not in prompt

        # Verify that transaction data is STILL in the prompt
        assert "0.1" in prompt
        assert "BTC" in prompt
        assert "Coinbase" in prompt


def test_pii_scrubbing_disabled_by_default(mocker):
    # Setup
    email_content = "Body: Hi John Doe, you bought 0.1 BTC."
    mock_llm_client = mocker.Mock()
    mock_llm_client.generate_json.return_value = mocker.Mock(data={"is_crypto_purchase": True, "confidence": 0.9})

    # Default settings (PII scrubbing should be False)
    settings = get_settings_with_overrides(enable_preprocessing=False)
    assert settings.enable_pii_scrubbing is False

    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm_client)

    # Execute
    extractor.is_crypto_purchase_email(email_content)

    # Verify
    prompt = mock_llm_client.generate_json.call_args.args[0]
    assert "John Doe" in prompt
    assert "[NAME]" not in prompt
