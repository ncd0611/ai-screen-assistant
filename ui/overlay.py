"""Transparent always-on-top overlay window built with PyQt6."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QPainter, QPainterPath
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class OverlayWindow(QWidget):
    """Semi-transparent overlay that displays AI answers.

    The window:
    * stays on top of all other windows,
    * has no frame / title bar,
    * is draggable via click-and-drag,
    * shows a loading spinner message while the AI is working, and
    * displays formatted results in a scrollable area.
    """

    _BACKGROUND_COLOR = QColor(20, 20, 20, 210)
    _BORDER_RADIUS = 12
    _MIN_WIDTH = 420
    _MIN_HEIGHT = 80
    _DEFAULT_WIDTH = 520
    _DEFAULT_HEIGHT = 400

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._drag_pos: QPoint | None = None
        self._setup_window_flags()
        self._setup_ui()
        self.resize(self._DEFAULT_WIDTH, self._DEFAULT_HEIGHT)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def show_loading(self) -> None:
        """Show a loading indicator while waiting for the AI response."""
        self._result_label.setText("⏳ Analyzing screen…")
        self._result_label.setStyleSheet("color: #aaaaaa; font-style: italic;")
        if not self.isVisible():
            self.show()

    def show_result(self, text: str) -> None:
        """Display the AI answer in the overlay.

        Args:
            text: Plain-text or markdown-ish response from the AI model.
        """
        self._result_label.setText(text)
        self._result_label.setStyleSheet("color: #ffffff;")
        if not self.isVisible():
            self.show()

    def show_error(self, message: str) -> None:
        """Display an error message in the overlay.

        Args:
            message: Human-readable error description.
        """
        self._result_label.setText(f"❌ Error: {message}")
        self._result_label.setStyleSheet("color: #ff6b6b;")
        if not self.isVisible():
            self.show()

    def toggle_visibility(self) -> None:
        """Toggle between visible and hidden states."""
        if self.isVisible():
            self.hide()
        else:
            self.show()

    # ------------------------------------------------------------------
    # Qt overrides — window chrome
    # ------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # type: ignore[override]
        """Paint the dark semi-transparent rounded rectangle background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(
            0, 0, self.width(), self.height(),
            self._BORDER_RADIUS, self._BORDER_RADIUS,
        )
        painter.fillPath(path, self._BACKGROUND_COLOR)

    # ------------------------------------------------------------------
    # Qt overrides — dragging
    # ------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        self._drag_pos = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _setup_window_flags(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(self._MIN_WIDTH, self._MIN_HEIGHT)

    def _setup_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(16, 16, 16, 16)
        outer_layout.setSpacing(8)

        # Title bar
        title = QLabel("🤖 AI Screen Assistant")
        title.setStyleSheet(
            "color: #61dafb; font-size: 14px; font-weight: bold;"
        )
        outer_layout.addWidget(title)

        # Scrollable result area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollBar:vertical { background: #333; width: 8px; border-radius: 4px; }"
            "QScrollBar::handle:vertical { background: #666; border-radius: 4px; }"
        )

        self._result_label = QLabel("Ready. Press Ctrl+Shift+S to scan screen.")
        self._result_label.setWordWrap(True)
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._result_label.setStyleSheet("color: #cccccc; font-size: 13px;")
        self._result_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._result_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        scroll.setWidget(self._result_label)
        outer_layout.addWidget(scroll)

        # Hotkey hint
        hint = QLabel(
            "Ctrl+Shift+S scan  |  Ctrl+Shift+H hide  |  Ctrl+Shift+R region  |  Ctrl+Shift+Q quit"
        )
        hint.setStyleSheet("color: #555555; font-size: 10px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(hint)
