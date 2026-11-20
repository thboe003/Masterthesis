"""
Provider-neutral interface for large language models.

Every concrete provider (Ollama, OpenAI-compatible, Anthropic, ...) implements
``LLMProvider.complete_json``. The rest of the application only talks to this
interface, so the model can be switched via environment variables without
touching the plan-generation logic.
"""

from __future__ import annotations

import base64
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class LLMError(Exception):
    """Base error for all LLM related failures."""


class LLMUnavailableError(LLMError):
    """The provider could not be reached or rejected the request (network, auth, ...)."""


class LLMResponseError(LLMError):
    """The provider answered, but the answer could not be used (e.g. no valid JSON)."""


@dataclass
class ImageInput:
    """
    One image sent to a multimodal (vision) model.

    ``data`` holds the encoded image bytes (JPEG/PNG). Providers transmit them
    base64-encoded – base64 is only the transport format of the API, the model
    itself receives the decoded image, not the "binary code".
    """

    data: bytes
    media_type: str = "image/jpeg"
    label: Optional[str] = None  # e.g. "Frame 3 (t=2.40s)", placed as text before the image

    def b64(self) -> str:
        return base64.b64encode(self.data).decode("ascii")

    def data_url(self) -> str:
        return f"data:{self.media_type};base64,{self.b64()}"


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

    async def complete_json_with_images(
        self, system_prompt: str, user_prompt: str, images: List[ImageInput]
    ) -> LLMResult:
        """
        Like ``complete_json`` but with images attached to the user message.

        Used by the video analysis: a video is reduced to a few key frames
        which are sent as images. The selected model must be vision-capable
        (e.g. qwen2.5vl / llama3.2-vision in Ollama, gpt-4o, Claude).
        """
        raise LLMUnavailableError(f"Provider '{self.name}' unterstützt keine Bildeingaben.")

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
