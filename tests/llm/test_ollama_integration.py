"""Integration tests for Ollama-based parsing in EmailPurchaseExtractor."""

import json
from unittest.mock import MagicMock, patch

import pytest

from digital_asset_harvester.config import HarvesterSettings
from digital_asset_harvester.llm.ollama_client import OllamaLLMClient
from digital_asset_harvester.processing.email_purchase_extractor import EmailPurchaseExtractor


@pytest.fixture
def mock_ollama_client():
    """Mock the Ollama library Client."""
    with patch("digital_asset_harvester.llm.ollama_client.Client") as mock_client_class:
        mock_instance = MagicMock()
        mock_client_class.return_value = mock_instance
        yield mock_instance


def test_ollama_end_to_end_parsing(mock_ollama_client):
    """Verify that EmailPurchaseExtractor correctly uses Ollama for classification and extraction."""
    settings = HarvesterSettings(
        llm_provider="ollama",
        enable_preprocessing=False,  # Force LLM calls
        enable_regex_extractors=False,  # Force LLM extraction
        min_confidence_threshold=0.1,
    )

    # Setup mock responses for classification then extraction
    mock_ollama_client.generate.side_effect = [
        # Classification response
        {
            "response": json.dumps(
                {"is_crypto_purchase": True, "confidence": 0.95, "reasoning": "Standard purchase confirmation"}
            )
        },
        # Extraction response
        {
            "response": json.dumps(
                {
                    "transactions": [
                        {
                            "transaction_type": "buy",
                            "total_spent": 100.0,
                            "currency": "USD",
                            "amount": 0.005,
                            "item_name": "BTC",
                            "vendor": "Coinbase",
                            "purchase_date": "2024-01-01 12:00:00 UTC",
                            "confidence": 0.98,
                            "extraction_notes": "Perfect match",
                        }
                    ]
                }
            )
        },
    ]

    llm_client = OllamaLLMClient(settings=settings)
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=llm_client)

    email_content = "Subject: Coinbase Order\n\nYou bought 0.005 BTC for $100.00 USD."
    result = extractor.process_email(email_content)

    assert result["has_purchase"] is True
    assert len(result["purchases"]) == 1
    purchase = result["purchases"][0]
    assert purchase["vendor"] == "Coinbase"
    assert purchase["amount"] == 0.005
    assert purchase["total_spent"] == 100.0
    assert purchase["currency"] == "USD"
    assert purchase["item_name"] == "BTC"

    # Verify that num_ctx was passed to Ollama
    assert mock_ollama_client.generate.call_count == 2
    for call in mock_ollama_client.generate.call_args_list:
        _, kwargs = call
        assert "options" in kwargs
        assert kwargs["options"]["num_ctx"] == 4096


def test_ollama_parsing_with_custom_context_window(mock_ollama_client):
    """Verify that a custom context window size is correctly passed to Ollama."""
    custom_ctx = 8192
    settings = HarvesterSettings(llm_provider="ollama", llm_context_window=custom_ctx, enable_preprocessing=False)

    mock_ollama_client.generate.return_value = {
        "response": json.dumps({"is_crypto_purchase": False, "confidence": 0.0, "reasoning": "N/A"})
    }

    llm_client = OllamaLLMClient(settings=settings)
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=llm_client)

    extractor.is_crypto_purchase_email("Some content")

    args, kwargs = mock_ollama_client.generate.call_args
    assert kwargs["options"]["num_ctx"] == custom_ctx
