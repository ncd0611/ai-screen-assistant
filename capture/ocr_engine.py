"""OCR engine module — fallback text extraction using EasyOCR."""

from __future__ import annotations

from typing import List, Optional

from PIL import Image


class OCREngine:
    """Extracts text from images using EasyOCR.

    EasyOCR is imported lazily so the application starts quickly even when
    the optional CUDA / torch setup takes time.

    Supported languages default to English + Vietnamese, but any languages
    supported by EasyOCR can be passed at construction time.
    """

    def __init__(self, languages: Optional[List[str]] = None) -> None:
        """Initialise the OCR engine.

        Args:
            languages: List of language codes (e.g. ``["en", "vi"]``).
                Defaults to English and Vietnamese.
        """
        self._languages: List[str] = languages or ["en", "vi"]
        self._reader = None  # Lazy initialisation

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_text(self, image: Image.Image) -> str:
        """Extract all text from *image* and return it as a single string.

        Args:
            image: A PIL ``Image`` object.

        Returns:
            Extracted text joined by newlines.
        """
        reader = self._get_reader()
        import numpy as np  # noqa: PLC0415

        img_array = np.array(image)
        results = reader.readtext(img_array, detail=0, paragraph=True)
        return "\n".join(str(line) for line in results)

    def extract_text_from_bytes(self, image_bytes: bytes) -> str:
        """Extract text from raw image bytes.

        Args:
            image_bytes: PNG (or other format) encoded image bytes.

        Returns:
            Extracted text joined by newlines.
        """
        import io  # noqa: PLC0415

        image = Image.open(io.BytesIO(image_bytes))
        return self.extract_text(image)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_reader(self):
        """Return (and lazily initialise) the EasyOCR reader."""
        if self._reader is None:
            try:
                import easyocr  # noqa: PLC0415

                self._reader = easyocr.Reader(
                    self._languages, gpu=False, verbose=False
                )
            except ImportError as exc:
                raise ImportError(
                    "easyocr is required for OCR support. "
                    "Install it with: pip install easyocr"
                ) from exc
        return self._reader
