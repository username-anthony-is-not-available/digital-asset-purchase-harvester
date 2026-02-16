"""Tests for privacy hardening features."""

from unittest.mock import MagicMock, patch

import pytest

from digital_asset_harvester.config import HarvesterSettings
from digital_asset_harvester.llm import get_llm_client
from digital_asset_harvester.processing.email_purchase_extractor import EmailPurchaseExtractor


def test_privacy_mode_restricts_cloud_providers():
    """Verify that privacy mode prevents using cloud providers."""
    settings = HarvesterSettings(enable_privacy_mode=True, enable_cloud_llm=True, llm_provider="openai")

    with pytest.raises(ValueError, match="Privacy mode is enabled. LLM provider 'openai' is not allowed"):
        get_llm_client(settings=settings)


def test_privacy_mode_restricts_ollama_fallback():
    """Verify that privacy mode prevents Ollama fallback to cloud."""
    settings = HarvesterSettings(enable_privacy_mode=True, enable_ollama_fallback=True, llm_provider="ollama")

    with pytest.raises(ValueError, match="Privacy mode is enabled. Ollama fallback to cloud LLM is not allowed"):
        get_llm_client(settings=settings)


@patch("digital_asset_harvester.llm.ollama_client.Client")
def test_ollama_client_uses_configured_base_url(mock_client_class):
    """Verify that OllamaLLMClient uses the configured base URL."""
    custom_url = "http://secure-ollama:11434"
    settings = HarvesterSettings(ollama_base_url=custom_url, llm_provider="ollama")

    get_llm_client(settings=settings)

    # Check that Client was initialized with the custom host
    mock_client_class.assert_called_once()
    args, kwargs = mock_client_class.call_args
    assert kwargs["host"] == custom_url


def test_privacy_mode_enables_pii_scrubbing():
    """Verify that privacy mode automatically enables PII scrubbing in the extractor."""
    settings = HarvesterSettings(
        enable_privacy_mode=True, enable_pii_scrubbing=False, llm_provider="ollama"  # Explicitly disabled
    )

    # Mock LLM client to avoid initialization issues
    mock_llm = MagicMock()
    extractor = EmailPurchaseExtractor(settings=settings, llm_client=mock_llm)

    email_content = "From: alice@example.com\nSubject: Buy BTC\n\nHi Alice, you bought 1 BTC."

    with patch.object(extractor.pii_scrubber, "scrub", return_value="SCRUBBED") as mock_scrub:
        extractor._scrub_pii_if_enabled(email_content)
        mock_scrub.assert_called_once_with(email_content)


def test_no_privacy_mode_respects_pii_settings():
    """Verify that when privacy mode is off, PII scrubbing respects the setting."""
    # Case 1: Privacy mode OFF, PII scrubbing OFF
    settings_off = HarvesterSettings(enable_privacy_mode=False, enable_pii_scrubbing=False, llm_provider="ollama")
    mock_llm = MagicMock()
    extractor_off = EmailPurchaseExtractor(settings=settings_off, llm_client=mock_llm)

    with patch.object(extractor_off.pii_scrubber, "scrub") as mock_scrub:
        result = extractor_off._scrub_pii_if_enabled("content")
        mock_scrub.assert_not_called()
        assert result == "content"

    # Case 2: Privacy mode OFF, PII scrubbing ON
    settings_on = HarvesterSettings(enable_privacy_mode=False, enable_pii_scrubbing=True, llm_provider="ollama")
    extractor_on = EmailPurchaseExtractor(settings=settings_on, llm_client=mock_llm)

    with patch.object(extractor_on.pii_scrubber, "scrub", return_value="SCRUBBED") as mock_scrub:
        result = extractor_on._scrub_pii_if_enabled("content")
        mock_scrub.assert_called_once_with("content")
        assert result == "SCRUBBED"
