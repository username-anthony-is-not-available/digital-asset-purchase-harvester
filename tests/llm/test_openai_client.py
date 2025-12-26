"""Tests for the OpenAILLMClient wrapper."""

import json

import pytest
from openai import OpenAIError

from digital_asset_harvester.config import get_settings_with_overrides
from digital_asset_harvester.llm.ollama_client import (
    LLMError,
    LLMResponseFormatError,
)
from digital_asset_harvester.llm.openai_client import OpenAILLMClient


class MockOpenAIClient:
    def __init__(self, responses):
        self.responses = responses
        self.chat = self
        self.completions = self

    def create(self, **kwargs):
        if not self.responses:
            raise OpenAIError("No mock responses provided")
        return self.responses.pop(0)


class MockChoice:
    def __init__(self, content):
        self.message = self
        self.content = content


class MockCompletion:
    def __init__(self, choices):
        self.choices = choices


def test_generate_json_success():
    """Test successful JSON generation."""
    dummy_payload = json.dumps({"value": 42})
    mock_response = MockCompletion([MockChoice(dummy_payload)])
    mock_client = MockOpenAIClient([mock_response])
    settings = get_settings_with_overrides(openai_api_key="test")
    client = OpenAILLMClient(settings=settings, client=mock_client)

    result = client.generate_json("prompt")
    assert result.data == {"value": 42}


def test_generate_json_malformed():
    """Test that malformed JSON raises an error."""
    mock_response = MockCompletion([MockChoice("not-json")])
    mock_client = MockOpenAIClient([mock_response])
    settings = get_settings_with_overrides(openai_api_key="test")
    client = OpenAILLMClient(
        settings=settings, client=mock_client, default_retries=1
    )

    with pytest.raises(LLMResponseFormatError):
        client.generate_json("prompt")


def test_generate_json_exhausts_retries():
    """Test that the client gives up after exhausting retries."""
    mock_client = MockOpenAIClient([])
    settings = get_settings_with_overrides(openai_api_key="test")
    client = OpenAILLMClient(
        settings=settings, client=mock_client, default_retries=2
    )

    with pytest.raises(LLMError):
        client.generate_json("prompt")
