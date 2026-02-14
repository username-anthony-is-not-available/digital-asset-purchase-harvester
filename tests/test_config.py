"""Tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from digital_asset_harvester.config import (
    DEFAULT_CONFIG_FILE,
    HarvesterSettings,
    get_settings_with_overrides,
    reload_settings,
    setup_logging,
)


def test_load_default_settings():
    """Verify that default settings are loaded correctly."""
    settings = HarvesterSettings()
    assert settings.llm_model_name == "llama3.2:3b"
    assert settings.min_confidence_threshold == 0.6
    assert settings.allow_unknown_cryptos


def test_get_settings_with_overrides():
    """Verify that settings can be overridden at runtime."""
    overrides = {"llm_model_name": "test-model", "min_confidence_threshold": 0.9}
    settings = get_settings_with_overrides(**overrides)
    assert settings.llm_model_name == "test-model"
    assert settings.min_confidence_threshold == 0.9


def test_load_config_from_file(tmp_path):
    """Verify that settings are loaded from a TOML file."""
    config_content = """
    [harvester]
    llm_model_name = "file-model"
    min_confidence_threshold = 0.8
    """
    config_file = str(tmp_path / "config.toml")
    with open(config_file, "w") as f:
        f.write(config_content)

    with patch.dict(os.environ, {"HARVESTER_CONFIG_FILE": config_file}):
        settings = reload_settings()
        assert settings.llm_model_name == "file-model"
        assert settings.min_confidence_threshold == 0.8


def test_environment_variable_overrides(tmp_path):
    """Verify that environment variables override file settings."""
    config_content = """
    [harvester]
    llm_model_name = "file-model"
    """
    config_file = str(tmp_path / "config.toml")
    with open(config_file, "w") as f:
        f.write(config_content)

    env_vars = {
        "HARVESTER_CONFIG_FILE": config_file,
        "DAP_LLM_MODEL_NAME": "env-model",
    }
    with patch.dict(os.environ, env_vars):
        settings = reload_settings()
        assert settings.llm_model_name == "env-model"


def test_setup_logging_debug(caplog):
    """Verify that logging is set to DEBUG level."""
    logger = setup_logging(log_level="DEBUG")
    logger.debug("test message")
    assert "test message" in caplog.text
    assert "DEBUG" in caplog.text


def test_default_config_file_constant():
    """Verify the default config file path is correct."""
    assert DEFAULT_CONFIG_FILE == "config/config.toml"


def test_harvester_settings_allow_unknown_cryptos():
    """Verify that allow_unknown_cryptos can be set."""
    settings = HarvesterSettings(allow_unknown_cryptos=True)
    assert settings.allow_unknown_cryptos is True
