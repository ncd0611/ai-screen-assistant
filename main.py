"""Entry point for AI Screen Assistant."""

from __future__ import annotations

import asyncio
import sys
from typing import Optional, Tuple

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication

import config
from ai.github_ai_client import GitHubAIClient
from capture.screen_capture import ScreenCapture
from ui.hotkey_manager import HotkeyManager
from ui.overlay import OverlayWindow
from ui.region_selector import RegionSelector


# ── Background worker ─────────────────────────────────────────────────────────

class AIWorker(QObject):
    """Runs the AI API call in a QThread so the UI stays responsive."""

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(
        self,
        base64_image: str,
        client: GitHubAIClient,
    ) -> None:
        super().__init__()
        self._image = base64_image
        self._client = client

    def run(self) -> None:
        """Execute the async AI call synchronously inside the worker thread."""
        try:
            answer = asyncio.run(self._client.answer_from_screenshot(self._image))
            self.finished.emit(answer)
        except Exception as exc:  # noqa: BLE001
            import traceback
            details = traceback.format_exc()
            self.error.emit(f"{exc}\n\nDetails:\n{details}")


# ── Main application ──────────────────────────────────────────────────────────

class App:
    """Wires together all components of the AI Screen Assistant."""

    def __init__(self) -> None:
        self._qt_app = QApplication(sys.argv)
        self._qt_app.setQuitOnLastWindowClosed(False)

        self._capture = ScreenCapture()
        self._ai_client = GitHubAIClient()
        self._overlay = OverlayWindow()
        self._region: Optional[Tuple[int, int, int, int]] = config.CAPTURE_REGION
        self._region_selector = RegionSelector()
        self._region_selector.region_selected.connect(self._on_region_selected)
        self._region_selector.region_cleared.connect(self._on_region_cleared)

        self._hotkeys = HotkeyManager()
        self._hotkeys.scan_requested.connect(self._trigger_scan)
        self._hotkeys.toggle_requested.connect(self._overlay.toggle_visibility)
        self._hotkeys.region_requested.connect(self._region_selector.start)
        self._hotkeys.quit_requested.connect(self._quit)
        self._thread: Optional[QThread] = None
        self._worker: Optional[AIWorker] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> int:
        """Start the application and block until it exits.

        Returns:
            Exit code (0 = normal exit).
        """
        self._overlay.update_capture_mode(self._region)
        self._overlay.show()
        self._hotkeys.start()
        return self._qt_app.exec()

    # ------------------------------------------------------------------
    # Slots / callbacks
    # ------------------------------------------------------------------

    def _trigger_scan(self) -> None:
        """Capture the screen and send it to the AI (called from hotkey)."""
        # Temporarily hide the overlay so it doesn't appear in the screenshot
        was_visible = self._overlay.isVisible()
        self._overlay.hide()

        try:
            b64 = self._capture.capture_as_base64(self._region)
        except Exception as exc:  # noqa: BLE001
            import traceback
            self._overlay.show_error(
                f"Screen capture failed: {exc}\n{traceback.format_exc()}"
            )
            return
        finally:
            if was_visible:
                self._overlay.show_loading()

        self._start_worker(b64)

    def _start_worker(self, b64_image: str) -> None:
        """Launch the AI worker in a background QThread."""
        # Ignore new request while one is already in flight
        if self._thread is not None:
            try:
                if self._thread.isRunning():
                    return
            except RuntimeError:
                # C++ object already deleted — safe to proceed
                pass

        self._thread = QThread()
        self._worker = AIWorker(b64_image, self._ai_client)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_ai_finished)
        self._worker.error.connect(self._on_ai_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        # Clear Python references when the thread finishes, then schedule deletion
        self._thread.finished.connect(self._cleanup_worker)

        self._thread.start()

    def _on_ai_finished(self, answer: str) -> None:
        token_info = self._ai_client.current_token_label
        self._overlay.show_result(f"*({token_info})*\n\n{answer}")

    def _on_ai_error(self, message: str) -> None:
        self._overlay.show_error(message)

    def _cleanup_worker(self) -> None:
        """Release thread/worker references so the next scan can proceed."""
        if self._thread is not None:
            self._thread.deleteLater()
        if self._worker is not None:
            self._worker.deleteLater()
        self._thread = None
        self._worker = None

    def _on_region_selected(self, x: int, y: int, w: int, h: int) -> None:
        self._region = (x, y, w, h)
        self._overlay.update_capture_mode(self._region)
        self._overlay.show_result(f"Đã chọn vùng chụp: **{w}×{h}** tại ({x}, {y})\n\nNhấn **Ctrl+Shift+S** để quét vùng này.\nNhấn **Ctrl+Shift+R** để chọn lại (ESC/Right-click = toàn màn hình).")

    def _on_region_cleared(self) -> None:
        self._region = None
        self._overlay.update_capture_mode(None)
        self._overlay.show_result("Đã chuyển về chế độ **chụp toàn màn hình**.\n\nNhấn **Ctrl+Shift+S** để quét.")

    def _quit(self) -> None:
        self._hotkeys.stop()
        self._qt_app.quit()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Application entry point."""
    app = App()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
