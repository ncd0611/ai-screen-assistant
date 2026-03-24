"""Prompt builder for the GitHub Models API."""

from __future__ import annotations

from typing import Any, Dict, List


# ── System prompts ────────────────────────────────────────────────────────────

SYSTEM_PROMPT_VISION = (
    "You are an AI assistant. The user sends a screenshot containing questions.\n"
    "Rules:\n"
    "1. Read and analyze every question visible in the image.\n"
    "2. If a question is NOT in Vietnamese, first translate it to Vietnamese "
    "(label: **Dịch:**), then answer.\n"
    "3. For multiple-choice questions: state the correct option letter/number "
    "clearly (e.g. **Đáp án: B**), then briefly explain why.\n"
    "4. For essay / open-ended / coding questions: provide a concise, "
    "well-reasoned answer in Vietnamese.\n"
    "5. Always respond in Vietnamese.\n"
    "6. Keep answers clear and concise — use bullet points or numbered steps "
    "when helpful."
)

SYSTEM_PROMPT_TEXT = (
    "You are an AI assistant. The user provides extracted text from their screen.\n"
    "Rules:\n"
    "1. If the text is NOT in Vietnamese, first translate it to Vietnamese "
    "(label: **Dịch:**), then answer.\n"
    "2. For multiple-choice questions: state the correct option clearly, "
    "then explain.\n"
    "3. For essay / open-ended questions: provide a concise, well-reasoned "
    "answer in Vietnamese.\n"
    "4. Always respond in Vietnamese."
)


class PromptBuilder:
    """Builds request message lists for the GitHub Models chat completions API."""

    # ------------------------------------------------------------------
    # Vision (primary)
    # ------------------------------------------------------------------

    @staticmethod
    def build_vision_messages(
        base64_image: str,
        user_instruction: str = "Hãy đọc và trả lời tất cả câu hỏi trong hình ảnh này. Nếu câu hỏi bằng tiếng nước ngoài, hãy dịch sang tiếng Việt trước khi trả lời.",
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
        user_instruction: str = "Hãy trả lời các câu hỏi ở trên. Nếu câu hỏi bằng tiếng nước ngoài, hãy dịch sang tiếng Việt trước khi trả lời.",
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
