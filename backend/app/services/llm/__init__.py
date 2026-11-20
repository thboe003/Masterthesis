"""
LLM integration layer.

The active provider is chosen with the ``LLM_PROVIDER`` environment variable:

    LLM_PROVIDER=ollama      (default) local model via Ollama
    LLM_PROVIDER=openai      OpenAI or any OpenAI-compatible server
    LLM_PROVIDER=anthropic   Claude via the Anthropic API

The video analysis needs a vision-capable model. It uses its own settings
(``VISION_LLM_PROVIDER`` / ``VISION_LLM_MODEL``) and falls back to
``LLM_PROVIDER`` with a vision default model.

See ``backend/.env.example`` for all settings.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

from .base import ImageInput, LLMError, LLMProvider, LLMResponseError, LLMResult, LLMUnavailableError, extract_json
from .providers import AnthropicProvider, OllamaProvider, OpenAICompatibleProvider

load_dotenv()

DEFAULT_MODELS = {
    "ollama": "llama3.1:8b",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-5-5",
}

# Defaults for the video analysis – these models accept images.
DEFAULT_VISION_MODELS = {
    "ollama": "qwen2.5vl:7b",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-5-5",
}


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


def _int_env(name: str, default: int | None = None) -> int | None:
    value = (os.getenv(name) or "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _build_provider(provider: str, model: str, timeout: float, num_ctx: int | None = None) -> LLMProvider:
    common = {"temperature": _float_env("LLM_TEMPERATURE", 0.4), "timeout": timeout}

    if provider == "ollama":
        return OllamaProvider(
            model, base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"), num_ctx=num_ctx, **common
        )
    if provider == "openai":
        return OpenAICompatibleProvider(
            model,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            json_mode=os.getenv("OPENAI_JSON_MODE", "true").lower() != "false",
            image_detail=os.getenv("OPENAI_IMAGE_DETAIL", "auto"),
            **common,
        )
    if provider == "anthropic":
        return AnthropicProvider(model, api_key=os.getenv("ANTHROPIC_API_KEY"), **common)

    raise LLMUnavailableError(
        f"Unbekannter LLM-Provider '{provider}'. Erlaubt: ollama, openai, anthropic."
    )


def create_llm_provider(provider: str | None = None) -> LLMProvider:
    """Build the text provider (training plans) from environment variables."""
    provider = (provider or os.getenv("LLM_PROVIDER", "ollama")).strip().lower()
    model = os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(provider, "")
    return _build_provider(provider, model, _float_env("LLM_TIMEOUT_SECONDS", 120.0), _int_env("OLLAMA_NUM_CTX"))


def create_vision_provider(provider: str | None = None) -> LLMProvider:
    """
    Build the vision provider (video analysis) from environment variables.

    ``VISION_LLM_PROVIDER`` falls back to ``LLM_PROVIDER``. ``VISION_LLM_MODEL``
    falls back to a vision-capable default, never to ``LLM_MODEL`` (the text
    model, e.g. llama3.1:8b, usually cannot see images).
    """
    provider = (provider or os.getenv("VISION_LLM_PROVIDER") or os.getenv("LLM_PROVIDER", "ollama")).strip().lower()
    model = os.getenv("VISION_LLM_MODEL") or DEFAULT_VISION_MODELS.get(provider, "")
    # Images need a large context window: default 16384 tokens for Ollama.
    num_ctx = _int_env("VISION_OLLAMA_NUM_CTX", 16384)
    return _build_provider(provider, model, _float_env("VISION_LLM_TIMEOUT_SECONDS", 300.0), num_ctx)


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """Cached provider instance for use as a FastAPI dependency."""
    return create_llm_provider()


@lru_cache(maxsize=1)
def get_vision_provider() -> LLMProvider:
    """Cached vision provider instance for use as a FastAPI dependency."""
    return create_vision_provider()


__all__ = [
    "ImageInput",
    "LLMError",
    "LLMProvider",
    "LLMResponseError",
    "LLMResult",
    "LLMUnavailableError",
    "create_llm_provider",
    "create_vision_provider",
    "extract_json",
    "get_llm_provider",
    "get_vision_provider",
]
