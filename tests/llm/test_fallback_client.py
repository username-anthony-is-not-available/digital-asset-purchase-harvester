
import pytest
from unittest.mock import MagicMock, patch
from digital_asset_harvester.llm.fallback_client import FallbackLLMClient
from digital_asset_harvester.llm.provider import LLMResult
from digital_asset_harvester.llm.ollama_client import LLMError
from digital_asset_harvester.llm import get_llm_client
from digital_asset_harvester.config import HarvesterSettings

def test_fallback_client_success_primary():
    primary = MagicMock()
    secondary = MagicMock()
    client = FallbackLLMClient(primary, secondary)

    expected_result = LLMResult(data={"key": "value"}, raw_text='{"key": "value"}')
    primary.generate_json.return_value = expected_result

    result = client.generate_json("test prompt")

    assert result.data == expected_result.data
    assert result.metadata["provider_used"] == "primary"
    primary.generate_json.assert_called_once()
    secondary.generate_json.assert_not_called()

def test_fallback_client_fallback_on_llmerror():
    primary = MagicMock()
    secondary = MagicMock()
    client = FallbackLLMClient(primary, secondary)

    primary.generate_json.side_effect = LLMError("Primary failed")
    expected_result = LLMResult(data={"key": "fallback"}, raw_text='{"key": "fallback"}')
    secondary.generate_json.return_value = expected_result

    result = client.generate_json("test prompt")

    assert result.data == expected_result.data
    assert result.metadata["provider_used"] == "secondary"
    primary.generate_json.assert_called_once()
    secondary.generate_json.assert_called_once()

def test_fallback_client_fallback_on_exception():
    primary = MagicMock()
    secondary = MagicMock()
    client = FallbackLLMClient(primary, secondary)

    primary.generate_json.side_effect = Exception("Unexpected error")
    expected_result = LLMResult(data={"key": "fallback"}, raw_text='{"key": "fallback"}')
    secondary.generate_json.return_value = expected_result

    result = client.generate_json("test prompt")

    assert result.data == expected_result.data
    assert result.metadata["provider_used"] == "secondary"
    primary.generate_json.assert_called_once()
    secondary.generate_json.assert_called_once()

@patch("digital_asset_harvester.llm.get_settings")
@patch("digital_asset_harvester.llm.ollama_client.OllamaLLMClient")
@patch("digital_asset_harvester.llm.openai_client.OpenAILLMClient")
@patch("digital_asset_harvester.llm.fallback_client.FallbackLLMClient")
def test_get_llm_client_returns_fallback(mock_fallback, mock_openai, mock_ollama, mock_get_settings):
    # Setup settings
    settings = HarvesterSettings(
        llm_provider="ollama",
        enable_ollama_fallback=True,
        enable_cloud_llm=True,
        ollama_fallback_threshold_seconds=5,
        fallback_cloud_provider="openai",
        enable_llm_cache=False
    )
    mock_get_settings.return_value = settings

    # Mocking Ollama and OpenAI instances
    mock_ollama_instance = MagicMock()
    mock_ollama.return_value = mock_ollama_instance

    mock_openai_instance = MagicMock()
    mock_openai.return_value = mock_openai_instance

    # Call get_llm_client
    client = get_llm_client()

    # Check that FallbackLLMClient was instantiated with correct arguments
    assert mock_fallback.called
    args, kwargs = mock_fallback.call_args
    assert args[0] == mock_ollama_instance
    assert args[1] == mock_openai_instance

    # Check that primary (Ollama) was created with correct settings (timeout=5)
    assert mock_ollama.called
    ollama_settings = mock_ollama.call_args.kwargs.get('settings')
    assert ollama_settings is not None
    assert ollama_settings.llm_timeout_seconds == 5
    assert ollama_settings.llm_max_retries == 1
