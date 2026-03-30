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

    _LABEL_BASE_CSS = (
        "color: #e0e0e0; font-size: 13px; background: transparent;"
    )

    def show_loading(self) -> None:
        """Show a loading indicator while waiting for the AI response."""
        self._result_label.setTextFormat(Qt.TextFormat.PlainText)
        self._result_label.setText("⏳ Đang phân tích màn hình…")
        self._result_label.setStyleSheet(
            f"{self._LABEL_BASE_CSS} color: #aaaaaa; font-style: italic;"
        )
        if not self.isVisible():
            self.show()

    def show_result(self, text: str) -> None:
        """Display the AI answer in the overlay.

        Markdown-style text from the AI is converted to simple HTML
        so the QLabel renders headings, bold, lists, etc.

        Args:
            text: Plain-text or markdown-ish response from the AI model.
        """
        html = self._markdown_to_html(text)
        self._result_label.setTextFormat(Qt.TextFormat.RichText)
        self._result_label.setText(html)
        self._result_label.setStyleSheet(self._LABEL_BASE_CSS)
        if not self.isVisible():
            self.show()

    def show_error(self, message: str) -> None:
        """Display an error message in the overlay.

        Args:
            message: Human-readable error description.
        """
        self._result_label.setTextFormat(Qt.TextFormat.PlainText)
        self._result_label.setText(f"❌ Error: {message}")
        self._result_label.setStyleSheet(
            f"{self._LABEL_BASE_CSS} color: #ff6b6b;"
        )
        if not self.isVisible():
            self.show()

    def toggle_visibility(self) -> None:
        """Toggle between visible and hidden states."""
        if self.isVisible():
            self.hide()
        else:
            self.show()

    def update_capture_mode(self, region=None) -> None:
        """Update the status bar to show the current capture mode.

        Args:
            region: Optional (x, y, w, h) tuple. None = full screen.
        """
        if region is not None:
            x, y, w, h = region
            self._status_label.setText(
                f"📐 Vùng chụp: {w}×{h} tại ({x},{y})"
            )
            self._status_label.setStyleSheet(
                "color: #61dafb; font-size: 11px; background: transparent;"
            )
        else:
            self._status_label.setText("🖥️ Chụp toàn màn hình")
            self._status_label.setStyleSheet(
                "color: #888888; font-size: 11px; background: transparent;"
            )

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

        # Capture mode status
        self._status_label = QLabel("🖥️ Chụp toàn màn hình")
        self._status_label.setStyleSheet(
            "color: #888888; font-size: 11px; background: transparent;"
        )
        outer_layout.addWidget(self._status_label)

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
        self._result_label.setStyleSheet(self._LABEL_BASE_CSS)
        self._result_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._result_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._result_label.setOpenExternalLinks(False)

        scroll.setWidget(self._result_label)
        # Ensure the scroll viewport is also transparent
        scroll.viewport().setStyleSheet("background: transparent;")
        outer_layout.addWidget(scroll)

        # Hotkey hint
        hint = QLabel(
            "Ctrl+Shift+S scan  |  Ctrl+Shift+H hide  |  Ctrl+Shift+R region  |  Ctrl+Shift+Q quit"
        )
        hint.setStyleSheet("color: #555555; font-size: 10px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer_layout.addWidget(hint)

    # ------------------------------------------------------------------
    # Markdown → HTML helper
    # ------------------------------------------------------------------

    @staticmethod
    def _markdown_to_html(text: str) -> str:
        """Convert a simplified subset of Markdown to HTML for QLabel.

        Handles: headings (##), bold (**), italic (*), inline code (`),
        unordered lists (- / *), ordered lists (1.), and paragraphs.
        """
        import re

        lines = text.split("\n")
        html_lines: list[str] = []
        in_ul = False
        in_ol = False

        def _close_lists() -> None:
            nonlocal in_ul, in_ol
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            if in_ol:
                html_lines.append("</ol>")
                in_ol = False

        for line in lines:
            stripped = line.strip()

            # Blank line → close lists, add spacing
            if not stripped:
                _close_lists()
                html_lines.append("<br>")
                continue

            # Headings
            m_heading = re.match(r"^(#{1,4})\s+(.*)", stripped)
            if m_heading:
                _close_lists()
                level = len(m_heading.group(1))
                sizes = {1: "17px", 2: "15px", 3: "14px", 4: "13px"}
                size = sizes.get(level, "13px")
                html_lines.append(
                    f'<p style="font-size:{size}; font-weight:bold; '
                    f'color:#61dafb; margin:4px 0;">{m_heading.group(2)}</p>'
                )
                continue

            # Unordered list item
            m_ul = re.match(r"^[-*]\s+(.*)", stripped)
            if m_ul:
                if not in_ul:
                    _close_lists()
                    html_lines.append("<ul style='margin:2px 0 2px 16px;'>")
                    in_ul = True
                html_lines.append(f"<li>{m_ul.group(1)}</li>")
                continue

            # Ordered list item
            m_ol = re.match(r"^\d+[.)\s]\s*(.*)", stripped)
            if m_ol:
                if not in_ol:
                    _close_lists()
                    html_lines.append("<ol style='margin:2px 0 2px 16px;'>")
                    in_ol = True
                html_lines.append(f"<li>{m_ol.group(1)}</li>")
                continue

            # Regular paragraph
            _close_lists()
            html_lines.append(f"<p style='margin:2px 0;'>{stripped}</p>")

        _close_lists()
        html = "\n".join(html_lines)

        # Inline formatting
        html = re.sub(r"`([^`]+)`", r"<code style='background:#333;padding:1px 4px;border-radius:3px;color:#f8c555;'>\1</code>", html)
        html = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html)
        html = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", html)

        return html
