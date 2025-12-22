"""Shared pytest fixtures for the harvester project."""

from __future__ import annotations

import json
from typing import Any, Dict, List

import pytest

from digital_asset_harvester import (
    StructuredLoggerFactory,
    EmailPurchaseExtractor,
    HarvesterSettings,
    LLMResult,
    get_settings_with_overrides,
)
from digital_asset_harvester.prompts import PromptManager


class StubLLMClient:
    """Test double that returns predefined responses in FIFO order."""

    def __init__(self, responses: List[Dict[str, Any]]) -> None:
        self._responses = list(responses)

    def generate_json(self, _prompt: str, **_kwargs):
        if not self._responses:
            raise AssertionError("No more responses configured for StubLLMClient")
        payload = self._responses.pop(0)
        return LLMResult(data=payload, raw_text=json.dumps(payload))


@pytest.fixture
def default_settings() -> HarvesterSettings:
    return get_settings_with_overrides(
        llm_model_name="llama3.2:3b",
        min_confidence_threshold=0.5,
        enable_preprocessing=True,
        strict_validation=True,
    )


@pytest.fixture
def extractor_factory(default_settings):
    def _factory(responses: List[Dict[str, Any]]):
        stub_client = StubLLMClient(responses)
        prompt_manager = PromptManager()
        prompt_manager.register("classification", "${email_content}")
        prompt_manager.register("extraction", "${email_content}")
        logger_factory = StructuredLoggerFactory(json_output=False)
        return EmailPurchaseExtractor(
            settings=default_settings,
            llm_client=stub_client,
            logger_factory=logger_factory,
            prompts=prompt_manager,
        )

    return _factory
