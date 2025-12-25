"""This module provides abstractions for interacting with Language Learning Models (LLMs).

It defines a common interface for different LLM providers and offers a factory
function to instantiate the currently configured provider.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from digital_asset_harvester.config import get_settings

if TYPE_CHECKING:
    from .provider import LLMProvider


def get_llm_client(provider: str | None = None) -> LLMProvider:
    """Get the configured LLM client.

    This factory function reads the application settings to determine which
    LLM provider to instantiate.

    Args:
        provider: The name of the LLM provider to use. If not specified,
            the value from the application settings will be used.

    Returns:
        An instance of the configured LLM provider client.
    """
    settings = get_settings()
    provider_name = (provider or settings.llm_provider).lower()

    if not settings.enable_cloud_llm and provider_name != "ollama":
        raise ValueError(
            "Cloud LLM providers are not enabled. "
            "Set `enable_cloud_llm` to True in settings to use them."
        )

    if provider_name == "ollama":
        from .ollama_client import OllamaLLMClient

        return OllamaLLMClient(settings=settings)
    if provider_name == "openai":
        from .openai_client import OpenAILLMClient

        return OpenAILLMClient(settings=settings)
    if provider_name == "anthropic":
        from .anthropic_client import AnthropicLLMClient

        return AnthropicLLMClient(settings=settings)
    raise ValueError(f"Unknown LLM provider: {provider_name}")
