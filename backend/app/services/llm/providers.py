"""
Concrete LLM providers.

All providers use plain HTTP via ``httpx`` (already in requirements.txt), so no
vendor SDK is needed.

- ``OllamaProvider``          – local models via Ollama (default, no API key)
- ``OpenAICompatibleProvider`` – OpenAI API and every server that speaks the
                                 same protocol (LM Studio, vLLM, LocalAI, ...)
- ``AnthropicProvider``       – Claude models via the Anthropic Messages API
"""

from __future__ import annotations

from typing import Any, Dict

from .base import LLMProvider, LLMResult, LLMUnavailableError, LLMResponseError


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


class OllamaProvider(LLMProvider):
    """Local models through the Ollama REST API (``ollama serve``)."""

    name = "ollama"

    def __init__(self, model: str, base_url: str = "http://localhost:11434", **kwargs: Any):
        super().__init__(model, **kwargs)
        self.base_url = base_url.rstrip("/")

    async def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        data = await _post_json(
            f"{self.base_url}/api/chat",
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "format": "json",
                "stream": False,
                "options": {"temperature": self.temperature},
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


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI Chat Completions API or any compatible server."""

    name = "openai"

    def __init__(
        self,
        model: str,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        json_mode: bool = True,
        **kwargs: Any,
    ):
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.json_mode = json_mode

    async def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
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

    async def complete_json(self, system_prompt: str, user_prompt: str) -> LLMResult:
        data = await _post_json(
            f"{self.base_url}/v1/messages",
            {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
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
