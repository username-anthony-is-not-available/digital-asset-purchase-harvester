"""Tests for the OllamaLLMClient wrapper."""

import json

import pytest

from digital_asset_harvester.llm import LLMError, LLMResponseFormatError, OllamaLLMClient
from digital_asset_harvester import get_settings_with_overrides


class DummyResponse:
    def __init__(self, payload):
        self.response = payload


class DummyClient:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        if not self.payloads:
            raise RuntimeError("No payloads configured")
        return DummyResponse(self.payloads.pop(0))


def test_generate_json_success():
    dummy_payload = json.dumps({"value": 42})
    client = DummyClient([dummy_payload])
    settings = get_settings_with_overrides()
    llm_client = OllamaLLMClient(settings=settings, client=client)

    result = llm_client.generate_json("prompt")

    assert result.data == {"value": 42}
    assert client.calls[0]["model"] == settings.llm_model_name


def test_generate_json_malformed():
    client = DummyClient(["not-json"])
    settings = get_settings_with_overrides()
    llm_client = OllamaLLMClient(settings=settings, client=client, default_retries=1)

    with pytest.raises(LLMResponseFormatError):
        llm_client.generate_json("prompt")


def test_generate_json_exhausts_retries():
    class ErrorClient(DummyClient):
        def generate(self, **kwargs):  # type: ignore[override]
            raise ConnectionError("boom")

    settings = get_settings_with_overrides()
    llm_client = OllamaLLMClient(settings=settings, client=ErrorClient([]), default_retries=2)

    with pytest.raises(LLMError):
        llm_client.generate_json("prompt")
