"""
Provider-neutral interface for large language models.

Every concrete provider (Ollama, OpenAI-compatible, Anthropic, ...) implements
``LLMProvider.complete_json``. The rest of the application only talks to this
interface, so the model can be switched via environment variables without
touching the plan-generation logic.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


class LLMError(Exception):
    """Base error for all LLM related failures."""


class LLMUnavailableError(LLMError):
    """The provider could not be reached or rejected the request (network, auth, ...)."""


class LLMResponseError(LLMError):
    """The provider answered, but the answer could not be used (e.g. no valid JSON)."""


@dataclass
class LLMResult:
    """Raw result of a single LLM call."""

    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(ABC):
    """Abstract base class for a chat-style LLM that is asked to return JSON."""

    name: str = "base"

    def __init__(self, model: str, temperature: float = 0.4, timeout: float = 120.0):
        self.model = model
        self.temperature = temperature
        self.timeout = timeout

    @abstractmethod
    async def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        """Send the prompts to the model and return its (JSON) answer as text."""

    def describe(self) -> Dict[str, Any]:
        return {"provider": self.name, "model": self.model}


_CODE_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def extract_json(text: str) -> Dict[str, Any]:
    """
    Parse a JSON object from a model answer.

    Models sometimes wrap JSON in Markdown code fences or add a sentence before
    or after it. This strips fences and falls back to the outermost ``{...}``.
    """
    cleaned = _CODE_FENCE.sub("", text.strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start == -1 or end <= start:
            raise LLMResponseError("Die Modellantwort enthält kein JSON-Objekt.")
        try:
            data = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMResponseError(f"Die Modellantwort ist kein gültiges JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise LLMResponseError("Die Modellantwort ist kein JSON-Objekt.")
    return data
