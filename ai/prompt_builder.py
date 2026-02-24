"""Prompt builder for the GitHub Models API."""

from __future__ import annotations

from typing import Any, Dict, List


# ── System prompts ────────────────────────────────────────────────────────────

SYSTEM_PROMPT_VISION = (
    "You are an AI assistant. The user sends a screenshot containing questions. "
    "Read, analyze, and answer each question accurately and concisely."
)

SYSTEM_PROMPT_TEXT = (
    "You are an AI assistant. The user provides extracted text from their screen. "
    "Analyze and provide accurate answers."
)


class PromptBuilder:
    """Builds request message lists for the GitHub Models chat completions API."""

    # ------------------------------------------------------------------
    # Vision (primary)
    # ------------------------------------------------------------------

    @staticmethod
    def build_vision_messages(
        base64_image: str,
        user_instruction: str = "Please read and answer all questions in this image.",
    ) -> List[Dict[str, Any]]:
        """Build messages for a vision-based request.

        Args:
            base64_image: Base64-encoded PNG image string (without data-URI prefix).
            user_instruction: Text instruction appended alongside the image.

        Returns:
            A list of message dicts ready for the ``messages`` field of the
            chat completions request body.
        """
        return [
            {"role": "system", "content": SYSTEM_PROMPT_VISION},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        },
                    },
                    {"type": "text", "text": user_instruction},
                ],
            },
        ]

    # ------------------------------------------------------------------
    # Text (fallback)
    # ------------------------------------------------------------------

    @staticmethod
    def build_text_messages(
        extracted_text: str,
        user_instruction: str = "Please answer the questions above.",
    ) -> List[Dict[str, Any]]:
        """Build messages for a text-based (OCR fallback) request.

        Args:
            extracted_text: Text extracted from the screen via OCR.
            user_instruction: Instruction appended after the screen content.

        Returns:
            A list of message dicts.
        """
        user_content = (
            f"Screen content:\n\n{extracted_text}\n\n{user_instruction}"
        )
        return [
            {"role": "system", "content": SYSTEM_PROMPT_TEXT},
            {"role": "user", "content": user_content},
        ]
