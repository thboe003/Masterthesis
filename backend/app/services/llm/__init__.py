"""
LLM integration layer.

The active provider is chosen with the ``LLM_PROVIDER`` environment variable:

    LLM_PROVIDER=ollama      (default) local model via Ollama
    LLM_PROVIDER=openai      OpenAI or any OpenAI-compatible server
    LLM_PROVIDER=anthropic   Claude via the Anthropic API

See ``backend/.env.example`` for all settings.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

from .base import LLMError, LLMProvider, LLMResponseError, LLMResult, LLMUnavailableError, extract_json
from .providers import AnthropicProvider, OllamaProvider, OpenAICompatibleProvider

load_dotenv()

DEFAULT_MODELS = {
    "ollama": "llama3.1:8b",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-5-5",
}


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def create_llm_provider(provider: str | None = None) -> LLMProvider:
    """Build a provider from environment variables."""
    provider = (provider or os.getenv("LLM_PROVIDER", "ollama")).strip().lower()
    model = os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(provider, "")
    common = {
        "temperature": _float_env("LLM_TEMPERATURE", 0.4),
        "timeout": _float_env("LLM_TIMEOUT_SECONDS", 120.0),
    }

    if provider == "ollama":
        return OllamaProvider(model, base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), **common)
    if provider == "openai":
        return OpenAICompatibleProvider(
            model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            json_mode=os.getenv("OPENAI_JSON_MODE", "true").lower() != "false",
            **common,
        )
    if provider == "anthropic":
        return AnthropicProvider(model, api_key=os.getenv("ANTHROPIC_API_KEY"), **common)

    raise LLMUnavailableError(
        f"Unbekannter LLM_PROVIDER '{provider}'. Erlaubt: ollama, openai, anthropic."
    )


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """Cached provider instance for use as a FastAPI dependency."""
    return create_llm_provider()


__all__ = [
    "LLMError",
    "LLMProvider",
    "LLMResponseError",
    "LLMResult",
    "LLMUnavailableError",
    "create_llm_provider",
    "extract_json",
    "get_llm_provider",
]
