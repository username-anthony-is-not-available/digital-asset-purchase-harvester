"""Centralized configuration handling for the harvester package."""

from __future__ import annotations

import importlib
import logging
import os
from dataclasses import asdict, dataclass, fields
from functools import lru_cache
from typing import Any, Dict, Type

logger = logging.getLogger(__name__)


DEFAULT_CONFIG_FILE = "config/config.toml"
_ENV_PREFIX = "DAP_"


@dataclass(frozen=True)
class HarvesterSettings:
    """Typed configuration container for the application."""

    llm_model_name: str = "llama3.2:3b"
    llm_max_retries: int = 3
    llm_timeout_seconds: int = 30

    enable_cloud_llm: bool = False
    llm_provider: str = "ollama"
    enable_ollama_fallback: bool = False
    ollama_fallback_threshold_seconds: int = 10
    fallback_cloud_provider: str = "openai"

    openai_api_key: str = ""
    openai_model_name: str = "gpt-4-turbo-preview"

    anthropic_api_key: str = ""
    anthropic_model_name: str = "claude-3-sonnet-20240229"

    enable_preprocessing: bool = True
    enable_pii_scrubbing: bool = False
    enable_regex_extractors: bool = True
    enable_validation: bool = True
    min_confidence_threshold: float = 0.6

    log_level: str = "INFO"
    enable_debug_output: bool = False
    log_json_output: bool = False

    batch_size: int = 10
    enable_parallel_processing: bool = False
    max_workers: int = 5

    strict_validation: bool = True
    allow_unknown_cryptos: bool = True
    require_numeric_validation: bool = True

    include_processing_metadata: bool = False
    include_confidence_scores: bool = False

    enable_imap: bool = False
    enable_koinly_csv_export: bool = False
    enable_ctc_csv_export: bool = False
    enable_cra_csv_export: bool = False
    enable_cra_pdf_export: bool = False
    enable_koinly_api: bool = False

    koinly_api_key: str = ""
    koinly_portfolio_id: str = ""
    koinly_api_base_url: str = "https://api.koinly.io/v1"


def _coerce_value(value: str, expected_type: Type[Any], *, field_name: str) -> Any:
    """Convert string environment values to the expected type."""

    if expected_type is bool:
        return value.strip().lower() in {"1", "true", "yes", "on"}
    if expected_type is int:
        try:
            return int(value)
        except ValueError as exc:
            raise ValueError(f"Invalid integer for {field_name}: {value!r}") from exc
    if expected_type is float:
        try:
            return float(value)
        except ValueError as exc:
            raise ValueError(f"Invalid float for {field_name}: {value!r}") from exc
    return value


def _load_env_overrides() -> Dict[str, Any]:
    """Read overrides from environment variables using the ``DAP_`` prefix."""

    overrides: Dict[str, Any] = {}
    for field in fields(HarvesterSettings):
        expected_type: Type[Any] = field.type  # type: ignore[assignment]
        env_name = f"{_ENV_PREFIX}{field.name.upper()}"
        raw_value = os.getenv(env_name)
        if raw_value is None:
            continue
        overrides[field.name] = _coerce_value(raw_value, expected_type, field_name=env_name)
    return overrides


def _load_file_overrides() -> Dict[str, Any]:
    """Read overrides from optional TOML configuration file."""
    import toml

    config_file = os.getenv("HARVESTER_CONFIG_FILE", DEFAULT_CONFIG_FILE)
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                config = toml.load(f)
                return config.get("harvester", {})
        except Exception as exc:
            logger.warning("Failed to load configuration from %s: %s", config_file, exc)
    return {}


def _compose_settings(**direct_overrides: Any) -> HarvesterSettings:
    """Build settings from defaults, file, environment, and direct overrides."""

    merged: Dict[str, Any] = asdict(HarvesterSettings())
    merged.update(_load_file_overrides())
    merged.update(_load_env_overrides())
    merged.update({k: v for k, v in direct_overrides.items() if v is not None})
    return HarvesterSettings(**merged)


@lru_cache(maxsize=1)
def get_settings() -> HarvesterSettings:
    """Retrieve cached application settings."""

    settings = _compose_settings()
    logger.debug("Loaded harvester settings: %s", settings)
    return settings


def reload_settings() -> HarvesterSettings:
    """Force settings reload and update the cache."""

    get_settings.cache_clear()  # type: ignore[attr-defined]
    return get_settings()


def get_settings_with_overrides(**overrides: Any) -> HarvesterSettings:
    """Return settings merged with explicit overrides (without caching)."""

    return _compose_settings(**overrides)


def setup_logging(log_level: str) -> logging.Logger:
    """Set up logging for the application."""
    logger = logging.getLogger()
    logger.setLevel(log_level)
    return logger
