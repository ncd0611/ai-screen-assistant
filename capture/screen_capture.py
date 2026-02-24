"""Screen capture module using the mss library."""

from __future__ import annotations

import base64
import io
from typing import Optional, Tuple

import mss
import mss.tools
from PIL import Image


class ScreenCapture:
    """Captures the screen (full or region) and returns a PIL Image or PNG bytes."""

    def __init__(self) -> None:
        self._sct = mss.mss()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def capture(
        self, region: Optional[Tuple[int, int, int, int]] = None
    ) -> Tuple[Image.Image, bytes]:
        """Capture the screen and return ``(PIL Image, PNG bytes)``.

        Args:
            region: Optional ``(x, y, width, height)`` tuple.  When *None*
                the primary monitor is captured.

        Returns:
            A tuple of ``(PIL.Image.Image, bytes)`` where *bytes* is the raw
            PNG-encoded image data.
        """
        monitor = self._build_monitor(region)
        raw = self._sct.grab(monitor)
        img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
        png_bytes = self._to_png_bytes(img)
        return img, png_bytes

    def capture_as_base64(
        self, region: Optional[Tuple[int, int, int, int]] = None
    ) -> str:
        """Capture the screen and return a base64-encoded PNG string.

        This is the format expected by vision-capable models in the
        GitHub Models API.

        Args:
            region: Optional ``(x, y, width, height)`` tuple.

        Returns:
            Base64-encoded PNG string (without the ``data:`` prefix).
        """
        _, png_bytes = self.capture(region)
        return base64.b64encode(png_bytes).decode("utf-8")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_monitor(
        self, region: Optional[Tuple[int, int, int, int]]
    ) -> dict:
        """Convert an optional region tuple into a mss monitor dict."""
        if region is None:
            # Primary monitor
            return self._sct.monitors[1]
        x, y, width, height = region
        return {"left": x, "top": y, "width": width, "height": height}

    @staticmethod
    def _to_png_bytes(img: Image.Image) -> bytes:
        """Encode a PIL image as PNG bytes."""
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def __del__(self) -> None:
        try:
            self._sct.close()
        except Exception:  # noqa: BLE001 — best-effort cleanup in destructor
            pass
