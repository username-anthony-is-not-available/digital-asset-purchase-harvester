"""Tests for the AnthropicLLMClient wrapper."""

import json

import pytest
from anthropic import AnthropicError

from digital_asset_harvester.config import get_settings_with_overrides
from digital_asset_harvester.llm.anthropic_client import AnthropicLLMClient
from digital_asset_harvester.llm.ollama_client import (
    LLMError,
    LLMResponseFormatError,
)


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
    client = AnthropicLLMClient(
        settings=settings, client=mock_client, default_retries=1
    )

    with pytest.raises(LLMResponseFormatError):
        client.generate_json("prompt")


def test_generate_json_exhausts_retries():
    """Test that the client gives up after exhausting retries."""
    mock_client = MockAnthropicClient([])
    settings = get_settings_with_overrides(anthropic_api_key="test")
    client = AnthropicLLMClient(
        settings=settings, client=mock_client, default_retries=2
    )

    with pytest.raises(LLMError):
        client.generate_json("prompt")
