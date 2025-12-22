import json
from unittest.mock import MagicMock, patch
from digital_asset_harvester.llm.client import (
    LLMError,
    LLMResponseFormatError,
    OllamaLLMClient,
)
import pytest

@patch("digital_asset_harvester.llm.client.get_settings")
def test_ollama_llm_client_generate_json_with_temperature(mock_get_settings):
    mock_get_settings.return_value.llm_model_name = "test-model"
    mock_client = MagicMock()
    mock_client.generate.return_value = {"response": '{"test": "test"}'}
    client = OllamaLLMClient(client=mock_client)
    result = client.generate_json("test prompt", temperature=0.5)
    assert result is not None
    mock_client.generate.assert_called_with(
        model="env-model",
        prompt="test prompt",
        format="json",
        options={"temperature": 0.5},
    )

def test_ollama_llm_client_generate_json_with_raw_text_none():
    mock_client = MagicMock()
    mock_client.generate.return_value = {"response": None}
    client = OllamaLLMClient(client=mock_client)
    with pytest.raises(LLMError):
        client.generate_json("test prompt")

def test_ollama_llm_client_generate_json_with_invalid_json():
    mock_client = MagicMock()
    mock_client.generate.return_value = {"response": "invalid json"}
    client = OllamaLLMClient(client=mock_client)
    with pytest.raises(LLMResponseFormatError):
        client.generate_json("test prompt")

def test_ollama_llm_client_generate_json_with_non_dict_json():
    mock_client = MagicMock()
    mock_client.generate.return_value = {"response": "[]"}
    client = OllamaLLMClient(client=mock_client)
    with pytest.raises(LLMResponseFormatError):
        client.generate_json("test prompt")

def test_ollama_llm_client_generate_json_with_unknown_error():
    mock_client = MagicMock()
    mock_client.generate.side_effect = Exception("test error")
    client = OllamaLLMClient(client=mock_client)
    with pytest.raises(LLMError):
        client.generate_json("test prompt")
