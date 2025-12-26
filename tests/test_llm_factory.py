"""Tests for the LLM provider factory."""

import pytest

from digital_asset_harvester.config import get_settings_with_overrides
from digital_asset_harvester.llm import get_llm_client
from digital_asset_harvester.llm.anthropic_client import AnthropicLLMClient
from digital_asset_harvester.llm.ollama_client import OllamaLLMClient
from digital_asset_harvester.llm.openai_client import OpenAILLMClient


def test_get_llm_client_ollama(mocker):
    """Verify that the factory returns the correct client for Ollama."""
    mock_settings = get_settings_with_overrides(llm_provider="ollama")
    mocker.patch("digital_asset_harvester.llm.get_settings", return_value=mock_settings)
    client = get_llm_client()
    assert isinstance(client, OllamaLLMClient)


def test_get_llm_client_openai(mocker):
    """Verify that the factory returns the correct client for OpenAI."""
    mocker.patch("openai.OpenAI")
    mock_settings = get_settings_with_overrides(
        llm_provider="openai", enable_cloud_llm=True, openai_api_key="test"
    )
    mocker.patch("digital_asset_harvester.llm.get_settings", return_value=mock_settings)
    client = get_llm_client()
    assert isinstance(client, OpenAILLMClient)


def test_get_llm_client_anthropic(mocker):
    """Verify that the factory returns the correct client for Anthropic."""
    mocker.patch("anthropic.Anthropic")
    mock_settings = get_settings_with_overrides(
        llm_provider="anthropic", enable_cloud_llm=True, anthropic_api_key="test"
    )
    mocker.patch("digital_asset_harvester.llm.get_settings", return_value=mock_settings)
    client = get_llm_client()
    assert isinstance(client, AnthropicLLMClient)


def test_get_llm_client_cloud_disabled(mocker):
    """Verify that using cloud providers is blocked when disabled."""
    mock_settings = get_settings_with_overrides(enable_cloud_llm=False)
    mocker.patch("digital_asset_harvester.llm.get_settings", return_value=mock_settings)

    with pytest.raises(ValueError, match="Cloud LLM providers are not enabled"):
        get_llm_client(provider="openai")


def test_get_llm_client_unknown_provider(mocker):
    """Verify that an unknown provider raises an error."""
    mock_settings = get_settings_with_overrides(enable_cloud_llm=True)
    mocker.patch("digital_asset_harvester.llm.get_settings", return_value=mock_settings)

    with pytest.raises(ValueError, match="Unknown LLM provider: foobar"):
        get_llm_client(provider="foobar")
