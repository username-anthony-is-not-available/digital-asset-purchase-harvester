"""This module provides abstractions for interacting with Language Learning Models (LLMs).

It defines a common interface for different LLM providers and offers a factory
function to instantiate the currently configured provider.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from digital_asset_harvester.config import get_settings

if TYPE_CHECKING:
    from .provider import LLMProvider


def get_llm_client(provider: str | None = None, settings: HarvesterSettings | None = None) -> LLMProvider:
    """Get the configured LLM client.

    This factory function is the single point of entry for creating LLM clients.
    It reads the application settings to determine which LLM provider to
    instantiate.

    Args:
        provider: The name of the LLM provider to use. If not specified,
            the value from the application settings will be used.
        settings: Optional settings object to use. If not specified, the
            global settings will be used.

    Returns:
        An instance of the configured LLM provider client.
    """
    settings = settings or get_settings()
    provider_name = (provider or settings.llm_provider).lower()

    if not settings.enable_cloud_llm and provider_name != "ollama":
        raise ValueError(
            "Cloud LLM providers are not enabled. " "Set `enable_cloud_llm` to True in settings to use them."
        )

    if provider_name == "ollama":
        from .ollama_client import OllamaLLMClient

        if settings.enable_ollama_fallback and not provider:
            from digital_asset_harvester.config import get_settings_with_overrides
            from .fallback_client import FallbackLLMClient

            # Primary client with threshold as timeout
            primary_settings = get_settings_with_overrides(
                llm_timeout_seconds=settings.ollama_fallback_threshold_seconds,
                llm_max_retries=1,  # Fast fallback
            )
            primary = OllamaLLMClient(settings=primary_settings)

            # Secondary client using configured fallback provider
            secondary = get_llm_client(provider=settings.fallback_cloud_provider, settings=settings)
            return FallbackLLMClient(primary, secondary)

        return OllamaLLMClient(settings=settings)
    if provider_name == "openai":
        from .openai_client import OpenAILLMClient

        return OpenAILLMClient(settings=settings)
    if provider_name == "anthropic":
        from .anthropic_client import AnthropicLLMClient

        return AnthropicLLMClient(settings=settings)
    raise ValueError(f"Unknown LLM provider: {provider_name}")
