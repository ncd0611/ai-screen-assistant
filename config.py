"""Configuration module for AI Screen Assistant."""

import os
from typing import Optional, Tuple

from dotenv import load_dotenv

load_dotenv()


# ── GitHub Models API ────────────────────────────────────────────────────────
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
AI_MODEL: str = os.getenv("AI_MODEL", "openai/gpt-4o")
API_BASE_URL: str = "https://models.github.ai/inference"
API_ENDPOINT: str = f"{API_BASE_URL}/chat/completions"

# ── AI Parameters ────────────────────────────────────────────────────────────
TEMPERATURE: float = 0.3
MAX_TOKENS: int = 2000

# ── Capture ──────────────────────────────────────────────────────────────────
def _parse_region(value: str) -> Optional[Tuple[int, int, int, int]]:
    """Parse a comma-separated region string into a 4-tuple."""
    if not value:
        return None
    parts = [p.strip() for p in value.split(",")]
    if len(parts) != 4:
        return None
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
    except ValueError:
        return None


CAPTURE_REGION: Optional[Tuple[int, int, int, int]] = _parse_region(
    os.getenv("CAPTURE_REGION", "")
)

# ── Hotkeys ──────────────────────────────────────────────────────────────────
HOTKEY_SCAN: str = os.getenv("HOTKEY_SCAN", "<ctrl>+<shift>+s")
HOTKEY_TOGGLE: str = os.getenv("HOTKEY_TOGGLE", "<ctrl>+<shift>+h")
HOTKEY_REGION: str = os.getenv("HOTKEY_REGION", "<ctrl>+<shift>+r")
HOTKEY_QUIT: str = os.getenv("HOTKEY_QUIT", "<ctrl>+<shift>+q")
