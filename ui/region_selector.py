"""Screen region selector widget built with PyQt6."""

from __future__ import annotations

from typing import Optional, Tuple

from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QApplication, QWidget


class RegionSelector(QWidget):
    """Full-screen translucent widget that lets the user drag-select a region.

    Once the user releases the mouse, ``region_selected`` is emitted with
    ``(x, y, width, height)`` and the widget closes itself.

    If the user presses Escape the widget closes and emits ``region_cleared``
    so the app can reset to full-screen capture.

    Right-click also clears the region and closes.
    """

    region_selected = pyqtSignal(int, int, int, int)
    region_cleared = pyqtSignal()

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
        self._origin = None
        self._current = None
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Semi-transparent dark overlay
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        if self._origin is not None and self._current is not None:
            rect = self._selection_rect()
            # Clear (bright) selection area
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_Clear
            )
            painter.fillRect(rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            # Light overlay inside selection so it's not fully transparent
            painter.fillRect(rect, QColor(97, 218, 251, 15))
            # Blue border
            pen = QPen(QColor(97, 218, 251), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
            # Dimension label
            self._draw_size_label(painter, rect)
        else:
            # Instruction text in center
            self._draw_instructions(painter)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.pos()
            self._current = event.pos()
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self.close()
            self.region_cleared.emit()

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
            self.region_cleared.emit()

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

    def _draw_instructions(self, painter: QPainter) -> None:
        """Draw centered instruction text."""
        font = QFont("Segoe UI", 16)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255, 200))
        painter.drawText(
            self.rect(), Qt.AlignmentFlag.AlignCenter,
            "Kéo chuột để chọn vùng chụp\n\n"
            "ESC / Right-click = Quay lại chụp toàn màn hình",
        )

    def _draw_size_label(self, painter: QPainter, rect: QRect) -> None:
        """Draw a small label showing selection dimensions."""
        text = f"{rect.width()} × {rect.height()}"
        font = QFont("Segoe UI", 10)
        font.setBold(True)
        painter.setFont(font)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text) + 12
        th = fm.height() + 6

        # Position label just below the selection rectangle
        lx = rect.center().x() - tw // 2
        ly = rect.bottom() + 6
        # Keep inside screen
        if ly + th > self.height():
            ly = rect.top() - th - 4

        bg_rect = QRect(lx, ly, tw, th)
        painter.fillRect(bg_rect, QColor(0, 0, 0, 180))
        painter.setPen(QColor(97, 218, 251))
        painter.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, text)
