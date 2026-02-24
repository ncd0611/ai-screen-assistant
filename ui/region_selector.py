"""Screen region selector widget built with PyQt6."""

from __future__ import annotations

from typing import Optional, Tuple

from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget


class RegionSelector(QWidget):
    """Full-screen translucent widget that lets the user drag-select a region.

    Once the user releases the mouse, ``region_selected`` is emitted with
    ``(x, y, width, height)`` and the widget closes itself.

    If the user presses Escape the widget closes without emitting a signal.
    """

    region_selected = pyqtSignal(int, int, int, int)

    def __init__(self) -> None:
        super().__init__()
        self._origin: Optional[QPoint] = None
        self._current: Optional[QPoint] = None
        self._setup()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Show the region selector over the entire screen."""
        screen = QApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.geometry())
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------------------
    # Qt overrides
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        # Semi-transparent dark overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        if self._origin is not None and self._current is not None:
            rect = self._selection_rect()
            # Clear (bright) selection area
            painter.fillRect(rect, QColor(0, 0, 0, 0))
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Clear
            )
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            # Blue border
            pen = QPen(QColor(97, 218, 251), 2)
            painter.setPen(pen)
            painter.drawRect(rect)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.pos()
            self._current = event.pos()
            self.update()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._origin is not None:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton and self._origin is not None:
            rect = self._selection_rect()
            self.close()
            if rect.width() > 5 and rect.height() > 5:
                self.region_selected.emit(
                    rect.x(), rect.y(), rect.width(), rect.height()
                )

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _setup(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def _selection_rect(self) -> QRect:
        """Return a normalised QRect from the drag origin to the current point."""
        assert self._origin is not None and self._current is not None
        return QRect(self._origin, self._current).normalized()
