"""Abstractions for interacting with OpenAI in a consistent way."""

from __future__ import annotations

import json
import logging
import random
import time
from typing import Any, Dict, Optional

from openai import OpenAI, OpenAIError

from digital_asset_harvester.config import HarvesterSettings, get_settings

from .ollama_client import LLMError, LLMResponseFormatError
from .provider import LLMProvider, LLMResult

logger = logging.getLogger(__name__)


class OpenAILLMClient(LLMProvider):
    """Thin wrapper around :class:`openai.OpenAI` with retries and JSON parsing."""

    def __init__(
        self,
        *,
        settings: Optional[HarvesterSettings] = None,
        client: Optional[OpenAI] = None,
        default_retries: Optional[int] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._client = client or OpenAI(
            api_key=self.settings.openai_api_key,
            timeout=self.settings.llm_timeout_seconds,
        )
        self.default_retries = default_retries or self.settings.llm_max_retries

    def generate_json(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        retries: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> LLMResult:
        """Execute a prompt expecting JSON output.

        Retries transient errors such as connection problems or malformed JSON.
        """
        attempts = retries or self.default_retries
        chosen_model = model or self.settings.openai_model_name
        last_error: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                logger.debug(
                    "LLM generate_json attempt %d/%d with model %s",
                    attempt,
                    attempts,
                    chosen_model,
                )
                response = self._client.chat.completions.create(
                    model=chosen_model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                )

                raw_text = response.choices[0].message.content
                if not raw_text:
                    raise LLMResponseFormatError("Empty response from LLM")

                payload = json.loads(raw_text)
                if not isinstance(payload, dict):
                    raise LLMResponseFormatError(f"Expected JSON object from LLM, received {type(payload).__name__}")
                return LLMResult(data=payload, raw_text=raw_text)

            except LLMResponseFormatError as exc:
                logger.warning("LLM response format error on attempt %d: %s", attempt, exc)
                last_error = exc
            except (json.JSONDecodeError, TypeError, AttributeError) as exc:
                logger.warning("Could not parse LLM response on attempt %d: %s", attempt, exc)
                last_error = LLMResponseFormatError(str(exc))
            except OpenAIError as exc:
                logger.warning("OpenAI API error on attempt %d: %s", attempt, exc)
                last_error = LLMError(str(exc))
            except Exception as exc:  # pragma: no cover - defensive guard
                logger.error("Unexpected LLM error on attempt %d: %s", attempt, exc)
                last_error = LLMError(str(exc))

            if attempt < attempts:
                sleep_duration = (2**attempt) + random.uniform(0, 1)
                logger.info("Retrying LLM call in %.2f seconds...", sleep_duration)
                time.sleep(sleep_duration)

        if last_error is None:
            last_error = LLMError("Unknown LLM failure")
        raise last_error
