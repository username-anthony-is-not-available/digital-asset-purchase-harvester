import json
import time
from unittest.mock import MagicMock, patch

import pytest

from digital_asset_harvester.llm.ollama_client import LLMError, LLMResponseFormatError, OllamaLLMClient


@patch("time.sleep", return_value=None)
@patch("digital_asset_harvester.llm.ollama_client.Client")
def test_generate_json_retry_logic(mock_client_constructor, mock_sleep):
    mock_client = MagicMock()
    mock_client_constructor.return_value = mock_client

    # Simulate a network error, then a JSON format error, then success
    mock_client.generate.side_effect = [
        ConnectionError("Network error"),
        json.JSONDecodeError("Invalid JSON", "", 0),
        {"response": '{"key": "value"}'},
    ]

    client = OllamaLLMClient(default_retries=3)
    result = client.generate_json("test prompt")

    assert result.data == {"key": "value"}
    assert mock_client.generate.call_count == 3
    assert mock_sleep.call_count == 2

    # Check that the sleep duration increases exponentially
    assert mock_sleep.call_args_list[0][0][0] > 2.0  # 2**1 + jitter
    assert mock_sleep.call_args_list[1][0][0] > 4.0  # 2**2 + jitter


@patch("time.sleep", return_value=None)
@patch("digital_asset_harvester.llm.ollama_client.Client")
def test_generate_json_retry_on_httpx_and_ollama_errors(mock_client_constructor, mock_sleep):
    import httpx
    from ollama import RequestError, ResponseError

    mock_client = MagicMock()
    mock_client_constructor.return_value = mock_client

    # Simulate httpx network error, ollama RequestError, 503 ResponseError, then success
    server_error_response = ResponseError("Service Unavailable", status_code=503)
    mock_client.generate.side_effect = [
        httpx.ConnectError("Connection refused"),
        RequestError("Ollama request failed"),
        server_error_response,
        {"response": '{"status": "ok"}'},
    ]

    client = OllamaLLMClient(default_retries=4)
    result = client.generate_json("test prompt")

    assert result.data == {"status": "ok"}
    assert mock_client.generate.call_count == 4
    assert mock_sleep.call_count == 3
    assert mock_sleep.call_args_list[0][0][0] > 2.0
    assert mock_sleep.call_args_list[1][0][0] > 4.0
    assert mock_sleep.call_args_list[2][0][0] > 8.0


@patch("digital_asset_harvester.llm.ollama_client.Client")
def test_generate_json_non_recoverable_response_error(mock_client_constructor):
    from ollama import ResponseError

    mock_client = MagicMock()
    mock_client_constructor.return_value = mock_client

    # 404 Model Not Found should fail fast
    client_error_response = ResponseError("model 'unknown' not found", status_code=404)
    mock_client.generate.side_effect = client_error_response

    client = OllamaLLMClient(default_retries=3)
    with pytest.raises(LLMError, match="not found"):
        client.generate_json("test prompt")

    assert mock_client.generate.call_count == 1


@patch("digital_asset_harvester.llm.ollama_client.Client")
def test_generate_json_non_recoverable_error(mock_client_constructor):
    mock_client = MagicMock()
    mock_client_constructor.return_value = mock_client

    # Simulate a non-recoverable runtime error
    mock_client.generate.side_effect = RuntimeError("Non-recoverable error")

    client = OllamaLLMClient(default_retries=3)
    with pytest.raises(LLMError, match="Non-recoverable error"):
        client.generate_json("test prompt")

    assert mock_client.generate.call_count == 1
