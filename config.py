"""Compatibility shim for legacy imports."""

from digital_asset_harvester.config import (
    HarvesterSettings,
    get_settings,
    get_settings_with_overrides,
    reload_settings,
)

LLM_MODEL_NAME = get_settings().llm_model_name

__all__ = [
    "HarvesterSettings",
    "LLM_MODEL_NAME",
    "get_settings",
    "get_settings_with_overrides",
    "reload_settings",
]
