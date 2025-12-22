"""Abstractions for interacting with Ollama in a consistent way."""

from __future__ import annotations

import json
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ollama import Client

from digital_asset_harvester.config import HarvesterSettings, get_settings

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Base exception for LLM-related failures."""


class LLMResponseFormatError(LLMError):
    """Raised when the LLM response cannot be parsed as expected."""


@dataclass
class LLMResult:
    """Container for structured LLM responses."""

    data: Dict[str, Any]
    raw_text: str


class OllamaLLMClient:
    """Thin wrapper around :class:`ollama.Client` with retries and JSON parsing."""

    def __init__(
        self,
        *,
        settings: Optional[HarvesterSettings] = None,
        client: Optional[Client] = None,
        default_retries: Optional[int] = None,
    ) -> None:
        self.settings = settings or get_settings()
        timeout = float(self.settings.llm_timeout_seconds)
        self._client = client or Client(timeout=timeout)
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
        chosen_model = model or self.settings.llm_model_name
        options: Dict[str, Any] = {}
        if temperature is not None:
            options["temperature"] = temperature

        last_error: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            try:
                logger.debug(
                    "LLM generate_json attempt %d/%d with model %s", attempt, attempts, chosen_model
                )
                response = self._client.generate(
                    model=chosen_model,
                    prompt=prompt,
                    format="json",
                    options=options or None,
                )

                raw_text = getattr(response, "response", None)
                if raw_text is None:
                    # Some versions of the Ollama client return dicts
                    raw_text = response["response"] if isinstance(response, dict) else str(response)

                payload = json.loads(raw_text)
                if not isinstance(payload, dict):
                    raise LLMResponseFormatError(
                        f"Expected JSON object from LLM, received {type(payload).__name__}"
                    )
                return LLMResult(data=payload, raw_text=raw_text)

            except LLMResponseFormatError as exc:
                logger.warning("LLM response format error on attempt %d: %s", attempt, exc)
                last_error = exc
            except json.JSONDecodeError as exc:
                logger.warning("Failed to decode LLM response JSON on attempt %d: %s", attempt, exc)
                last_error = LLMResponseFormatError(str(exc))
            except (ConnectionError, TimeoutError) as exc:
                logger.warning("LLM network error on attempt %d: %s", attempt, exc)
                last_error = LLMError(str(exc))
            except RuntimeError as exc:
                logger.error("LLM runtime error on attempt %d: %s", attempt, exc)
                last_error = LLMError(str(exc))
                raise last_error from exc  # Non-recoverable
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
