"""Tests for the AnthropicLLMClient wrapper."""

import json

import pytest
from unittest.mock import patch

import httpx
from anthropic import AnthropicError

from digital_asset_harvester.config import get_settings_with_overrides
from digital_asset_harvester.llm.anthropic_client import AnthropicLLMClient
from digital_asset_harvester.llm.ollama_client import LLMError, LLMResponseFormatError


class MockAnthropicClient:
    def __init__(self, responses):
        self.responses = responses
        self.messages = self

    def create(self, **kwargs):
        if not self.responses:
            raise AnthropicError("No mock responses provided")
        return self.responses.pop(0)


class MockContent:
    def __init__(self, text):
        self.text = text


class MockMessage:
    def __init__(self, content):
        self.content = content


def test_generate_json_success():
    """Test successful JSON generation."""
    dummy_payload = json.dumps({"value": 42})
    mock_response = MockMessage([MockContent(f"Here is the JSON: {dummy_payload}")])
    mock_client = MockAnthropicClient([mock_response])
    settings = get_settings_with_overrides(anthropic_api_key="test")
    client = AnthropicLLMClient(settings=settings, client=mock_client)

    result = client.generate_json("prompt")
    assert result.data == {"value": 42}


def test_generate_json_malformed():
    """Test that malformed JSON raises an error."""
    mock_response = MockMessage([MockContent("not-json")])
    mock_client = MockAnthropicClient([mock_response])
    settings = get_settings_with_overrides(anthropic_api_key="test")
    client = AnthropicLLMClient(settings=settings, client=mock_client, default_retries=1)

    with pytest.raises(LLMResponseFormatError):
        client.generate_json("prompt")


def test_generate_json_exhausts_retries():
    """Test that the client gives up after exhausting retries."""
    mock_client = MockAnthropicClient([])
    settings = get_settings_with_overrides(anthropic_api_key="test")
    client = AnthropicLLMClient(settings=settings, client=mock_client, default_retries=2)

    with pytest.raises(LLMError):
        client.generate_json("prompt")


@patch("time.sleep", return_value=None)
def test_generate_json_retry_on_network_error(mock_sleep):
    """Test that transient network errors are retried with exponential backoff."""
    dummy_payload = json.dumps({"value": 42})
    success_response = MockMessage([MockContent(f"Here is the JSON: {dummy_payload}")])

    class NetworkFailingAnthropicClient(MockAnthropicClient):
        def __init__(self):
            super().__init__([])
            self.attempt = 0

        def create(self, **kwargs):
            self.attempt += 1
            if self.attempt == 1:
                raise TimeoutError("Request timed out")
            if self.attempt == 2:
                raise httpx.ReadTimeout("Read timeout")
            return success_response

    mock_client = NetworkFailingAnthropicClient()
    settings = get_settings_with_overrides(anthropic_api_key="test")
    client = AnthropicLLMClient(settings=settings, client=mock_client, default_retries=3)

    result = client.generate_json("prompt")
    assert result.data == {"value": 42}
    assert mock_client.attempt == 3
    assert mock_sleep.call_count == 2
    assert mock_sleep.call_args_list[0][0][0] > 2.0
    assert mock_sleep.call_args_list[1][0][0] > 4.0
