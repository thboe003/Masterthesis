"""
Concrete LLM providers.

All providers use plain HTTP via ``httpx`` (already in requirements.txt), so no
vendor SDK is needed.

- ``OllamaProvider``          – local models via Ollama (default, no API key)
- ``OpenAICompatibleProvider`` – OpenAI API and every server that speaks the
                                 same protocol (LM Studio, vLLM, LocalAI, ...)
- ``AnthropicProvider``       – Claude models via the Anthropic Messages API

Every provider supports text-only prompts (``complete_json``) and prompts with
attached images (``complete_json_with_images``, used by the video analysis).
The message payloads are built by small pure functions (``*_messages``) so they
can be unit-tested without network access.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import ImageInput, LLMProvider, LLMResult, LLMUnavailableError, LLMResponseError


async def _post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str], timeout: float) -> Dict[str, Any]:
    import httpx  # imported lazily so the module can be imported without httpx (tests)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException as exc:
        raise LLMUnavailableError(f"Zeitüberschreitung nach {timeout:.0f}s bei {url}") from exc
    except httpx.HTTPError as exc:
        raise LLMUnavailableError(f"LLM-Server nicht erreichbar ({url}): {exc}") from exc

    if response.status_code >= 400:
        raise LLMUnavailableError(f"LLM-Server antwortete mit HTTP {response.status_code}: {response.text[:300]}")
    try:
        return response.json()
    except ValueError as exc:
        raise LLMResponseError("Antwort des LLM-Servers ist kein JSON.") from exc


# --------------------------------------------------------------------------- #
# Message builders (pure functions, tested in tests/test_video_analysis.py)
# --------------------------------------------------------------------------- #
def ollama_messages(system_prompt: str, user_prompt: str, images: Optional[List[ImageInput]] = None) -> List[Dict[str, Any]]:
    """Ollama takes a list of base64 images per message; labels go into the text."""
    user: Dict[str, Any] = {"role": "user", "content": user_prompt}
    if images:
        labels = [f"Bild {i}: {img.label}" for i, img in enumerate(images, 1) if img.label]
        if labels:
            user["content"] = user_prompt + "\n\nReihenfolge der angehängten Bilder:\n" + "\n".join(labels)
        user["images"] = [img.b64() for img in images]
    return [{"role": "system", "content": system_prompt}, user]


def openai_messages(
    system_prompt: str, user_prompt: str, images: Optional[List[ImageInput]] = None, detail: str = "auto"
) -> List[Dict[str, Any]]:
    """OpenAI chat format; each image is preceded by its label as a text part."""
    if not images:
        content: Any = user_prompt
    else:
        content = [{"type": "text", "text": user_prompt}]
        for img in images:
            if img.label:
                content.append({"type": "text", "text": img.label})
            content.append({"type": "image_url", "image_url": {"url": img.data_url(), "detail": detail}})
    return [{"role": "system", "content": system_prompt}, {"role": "user", "content": content}]


def anthropic_messages(user_prompt: str, images: Optional[List[ImageInput]] = None) -> List[Dict[str, Any]]:
    """Anthropic Messages format; images first (with labels), the instruction text last."""
    if not images:
        return [{"role": "user", "content": user_prompt}]
    content: List[Dict[str, Any]] = []
    for img in images:
        if img.label:
            content.append({"type": "text", "text": img.label})
        content.append(
            {"type": "image", "source": {"type": "base64", "media_type": img.media_type, "data": img.b64()}}
        )
    content.append({"type": "text", "text": user_prompt})
    return [{"role": "user", "content": content}]


# --------------------------------------------------------------------------- #
# Providers
# --------------------------------------------------------------------------- #
class OllamaProvider(LLMProvider):
    """Local models through the Ollama REST API (``ollama serve``)."""

    name = "ollama"

    def __init__(
        self, model: str, base_url: str = "http://localhost:11434", num_ctx: Optional[int] = None, **kwargs: Any
    ):
        super().__init__(model, **kwargs)
        self.base_url = base_url.rstrip("/")
        # Context window in tokens. Ollama's default (often 4096) is too small for
        # several images – each frame costs a few hundred tokens.
        self.num_ctx = num_ctx

    async def installed_models(self) -> List[str]:
        """Names of the models installed in Ollama (``ollama list``)."""
        import httpx

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/api/tags")
            return [m.get("name", "") for m in response.json().get("models", [])]
        except Exception:
            return []

    async def _chat(self, messages: List[Dict[str, Any]]) -> LLMResult:
        try:
            return await self._chat_once(messages)
        except LLMUnavailableError as exc:
            if "context size" in str(exc):
                raise LLMUnavailableError(
                    f"{exc} – Kontextfenster zu klein (aktuell num_ctx={self.num_ctx or 'Ollama-Standard'}). "
                    "In backend/.env VISION_OLLAMA_NUM_CTX (Videoanalyse) bzw. OLLAMA_NUM_CTX erhöhen, "
                    "oder weniger Frames / VIDEO_FRAME_MODE=grid / kleinere VIDEO_FRAME_MAX_SIDE verwenden."
                ) from exc
            if "HTTP 404" not in str(exc):
                raise
            installed = await self.installed_models()
            hint = ", ".join(installed) if installed else "keine"
            raise LLMUnavailableError(
                f"Modell '{self.model}' ist in Ollama nicht installiert. Installierte Modelle: {hint}. "
                f"Entweder `ollama pull {self.model}` ausführen oder den exakten Namen aus `ollama list` "
                "in backend/.env eintragen (VISION_LLM_MODEL für die Videoanalyse, LLM_MODEL für Trainingspläne)."
            ) from exc

    async def _chat_once(self, messages: List[Dict[str, Any]]) -> LLMResult:
        options: Dict[str, Any] = {"temperature": self.temperature}
        if self.num_ctx:
            options["num_ctx"] = self.num_ctx
        data = await _post_json(
            f"{self.base_url}/api/chat",
            {
                "model": self.model,
                "messages": messages,
                "format": "json",
                "stream": False,
                "options": options,
            },
            headers={},
            timeout=self.timeout,
        )
        try:
            text = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMResponseError(f"Unerwartete Ollama-Antwort: {str(data)[:300]}") from exc
        return LLMResult(
            text=text,
            provider=self.name,
            model=self.model,
            input_tokens=data.get("prompt_eval_count"),
            output_tokens=data.get("eval_count"),
        )

    async def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        return await self._chat(ollama_messages(system_prompt, user_prompt))

    async def complete_json_with_images(
        self, system_prompt: str, user_prompt: str, images: List[ImageInput]
    ) -> LLMResult:
        return await self._chat(ollama_messages(system_prompt, user_prompt, images))


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI Chat Completions API or any compatible server."""

    name = "openai"

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        json_mode: bool = True,
        image_detail: str = "auto",
        **kwargs: Any,
    ):
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.json_mode = json_mode
        self.image_detail = image_detail

    async def _chat(self, messages: List[Dict[str, Any]]) -> LLMResult:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }
        if self.json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        data = await _post_json(f"{self.base_url}/chat/completions", payload, headers, self.timeout)
        try:
            text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMResponseError(f"Unerwartete Antwort: {str(data)[:300]}") from exc
        usage = data.get("usage") or {}
        return LLMResult(
            text=text,
            provider=self.name,
            model=data.get("model", self.model),
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
        )

    async def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        return await self._chat(openai_messages(system_prompt, user_prompt))

    async def complete_json_with_images(
        self, system_prompt: str, user_prompt: str, images: List[ImageInput]
    ) -> LLMResult:
        return await self._chat(openai_messages(system_prompt, user_prompt, images, detail=self.image_detail))


class AnthropicProvider(LLMProvider):
    """Claude models through the Anthropic Messages API."""

    name = "anthropic"
    API_VERSION = "2023-06-01"

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str = "https://api.anthropic.com",
        max_tokens: int = 4096,
        **kwargs: Any,
    ):
        super().__init__(model, **kwargs)
        if not api_key:
            raise LLMUnavailableError("ANTHROPIC_API_KEY ist nicht gesetzt.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_tokens = max_tokens

    async def _chat(self, system_prompt: str, messages: List[Dict[str, Any]]) -> LLMResult:
        data = await _post_json(
            f"{self.base_url}/v1/messages",
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": system_prompt,
                "messages": messages,
            },
            headers={"x-api-key": self.api_key, "anthropic-version": self.API_VERSION},
            timeout=self.timeout,
        )
        try:
            text = "".join(block.get("text", "") for block in data["content"] if block.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise LLMResponseError(f"Unerwartete Anthropic-Antwort: {str(data)[:300]}") from exc
        usage = data.get("usage") or {}
        return LLMResult(
            text=text,
            provider=self.name,
            model=data.get("model", self.model),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
        )

    async def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        return await self._chat(system_prompt, anthropic_messages(user_prompt))

    async def complete_json_with_images(
        self, system_prompt: str, user_prompt: str, images: List[ImageInput]
    ) -> LLMResult:
        return await self._chat(system_prompt, anthropic_messages(user_prompt, images))
