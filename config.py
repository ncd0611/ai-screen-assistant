"""Configuration module for AI Screen Assistant."""

import os
from typing import Optional, Tuple

from dotenv import load_dotenv

load_dotenv()


# ── GitHub Models API ────────────────────────────────────────────────────────

def _collect_tokens() -> list[str]:
    """Collect GitHub tokens from environment variables.

    Supports two formats (can be combined):
      - Numbered: GITHUB_TOKEN_1, GITHUB_TOKEN_2, … (recommended)
      - Legacy:   GITHUB_TOKEN (single value or comma-separated)

    Numbered tokens are added first (in order), then any legacy tokens
    that are not already present.
    """
    tokens: list[str] = []
    seen: set[str] = set()

    # 1. Numbered tokens: GITHUB_TOKEN_1, GITHUB_TOKEN_2, …
    idx = 1
    while True:
        val = os.getenv(f"GITHUB_TOKEN_{idx}", "").strip()
        if not val:
            break
        if val not in seen:
            tokens.append(val)
            seen.add(val)
        idx += 1

    # 2. Legacy fallback: single GITHUB_TOKEN (also supports commas)
    legacy = os.getenv("GITHUB_TOKEN", "")
    for t in legacy.split(","):
        t = t.strip()
        if t and t not in seen:
            tokens.append(t)
            seen.add(t)

    return tokens


GITHUB_TOKENS: list[str] = _collect_tokens()

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
