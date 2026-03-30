"""Async GitHub Models API client with automatic token rotation."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import httpx

import config
from ai.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


class GitHubAIClient:
    """Client for the GitHub Models chat completions endpoint.

    Supports two modes:

    * **Vision** (primary): sends a base64-encoded screenshot directly to a
      vision-capable model such as ``openai/gpt-4o``.
    * **Text** (fallback): sends OCR-extracted text when a vision model is
      unavailable or when the caller explicitly requests text mode.

    When multiple tokens are configured (comma-separated in ``GITHUB_TOKEN``),
    the client automatically rotates to the next token on rate-limit (429) or
    auth failure (401).
    """

    _ENDPOINT = config.API_ENDPOINT
    # HTTP status codes that trigger a token rotation
    _ROTATE_STATUS_CODES = {429, 401, 403}

    def __init__(
        self,
        tokens: Optional[List[str]] = None,
        model: Optional[str] = None,
        temperature: float = config.TEMPERATURE,
        max_tokens: int = config.MAX_TOKENS,
        timeout: float = 60.0,
    ) -> None:
        self._tokens: List[str] = tokens or list(config.GITHUB_TOKENS)
        self._model: str = model or config.AI_MODEL
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._token_index: int = 0

        if not self._tokens:
            raise ValueError(
                "GITHUB_TOKEN is not set. "
                "Add it to your .env file or set it as an environment variable."
            )

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------

    @property
    def _current_token(self) -> str:
        return self._tokens[self._token_index]

    @property
    def token_count(self) -> int:
        return len(self._tokens)

    @property
    def current_token_label(self) -> str:
        """Return a safe label like 'Token 1/3' for UI display."""
        return f"Token {self._token_index + 1}/{len(self._tokens)}"

    def _rotate_token(self) -> bool:
        """Advance to the next token. Returns True if a new token is available."""
        next_idx = self._token_index + 1
        if next_idx < len(self._tokens):
            self._token_index = next_idx
            logger.info("Rotated to %s", self.current_token_label)
            return True
        return False

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
            "Authorization": f"Bearer {self._current_token}",
            "Content-Type": "application/json",
        }

    async def _call(self, messages: List[Dict[str, Any]]) -> str:
        """POST *messages* to the API, rotating tokens on rate-limit errors."""
        payload = self._build_payload(messages)
        last_error: Optional[Exception] = None
        start_index = self._token_index

        while True:
            headers = self._build_headers()
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        self._ENDPOINT, json=payload, headers=headers
                    )
                    response.raise_for_status()
                    data = response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code
                if status in self._ROTATE_STATUS_CODES and self._rotate_token():
                    logger.warning(
                        "%s on %s — rotating to %s",
                        status, f"Token {self._token_index}/{len(self._tokens)}",
                        self.current_token_label,
                    )
                    continue
                # All tokens exhausted or non-rotatable error
                raise
            else:
                break

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise ValueError(
                f"Unexpected API response format: {data}"
            ) from exc
