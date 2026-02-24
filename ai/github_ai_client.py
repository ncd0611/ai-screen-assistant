"""Async GitHub Models API client."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

import config
from ai.prompt_builder import PromptBuilder


class GitHubAIClient:
    """Client for the GitHub Models chat completions endpoint.

    Supports two modes:

    * **Vision** (primary): sends a base64-encoded screenshot directly to a
      vision-capable model such as ``openai/gpt-4o``.
    * **Text** (fallback): sends OCR-extracted text when a vision model is
      unavailable or when the caller explicitly requests text mode.
    """

    _ENDPOINT = config.API_ENDPOINT

    def __init__(
        self,
        token: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = config.TEMPERATURE,
        max_tokens: int = config.MAX_TOKENS,
        timeout: float = 60.0,
    ) -> None:
        """Initialise the client.

        Args:
            token: GitHub Personal Access Token.  Defaults to
                ``config.GITHUB_TOKEN``.
            model: Model identifier.  Defaults to ``config.AI_MODEL``.
            temperature: Sampling temperature (lower = more deterministic).
            max_tokens: Maximum tokens in the model response.
            timeout: HTTP request timeout in seconds.
        """
        self._token: str = token or config.GITHUB_TOKEN
        self._model: str = model or config.AI_MODEL
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout

        if not self._token:
            raise ValueError(
                "GITHUB_TOKEN is not set. "
                "Add it to your .env file or set it as an environment variable."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def answer_from_screenshot(self, base64_image: str) -> str:
        """Send a screenshot to the vision model and return the answer.

        Args:
            base64_image: Base64-encoded PNG string (no data-URI prefix).

        Returns:
            The AI-generated answer as a plain string.

        Raises:
            httpx.HTTPStatusError: On a non-2xx response.
            httpx.RequestError: On network-level failures.
        """
        messages = PromptBuilder.build_vision_messages(base64_image)
        return await self._call(messages)

    async def answer_from_text(self, extracted_text: str) -> str:
        """Send OCR-extracted text to the model and return the answer.

        Args:
            extracted_text: Text extracted from the screen via OCR.

        Returns:
            The AI-generated answer as a plain string.

        Raises:
            httpx.HTTPStatusError: On a non-2xx response.
            httpx.RequestError: On network-level failures.
        """
        messages = PromptBuilder.build_text_messages(extracted_text)
        return await self._call(messages)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_payload(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "model": self._model,
            "messages": messages,
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }

    def _build_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def _call(self, messages: List[Dict[str, Any]]) -> str:
        """POST *messages* to the API and return the reply text."""
        payload = self._build_payload(messages)
        headers = self._build_headers()

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self._ENDPOINT, json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ValueError(
                f"Unexpected API response format: {data}"
            ) from exc
