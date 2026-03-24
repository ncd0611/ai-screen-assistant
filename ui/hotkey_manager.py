"""Global hotkey manager using pynput.

pynput callbacks execute on a background thread.  Qt GUI operations **must**
run on the main thread.  This module bridges the two worlds by emitting Qt
signals from the pynput callbacks — Qt automatically queues them onto the
main-thread event loop (``QueuedConnection``).
"""

from __future__ import annotations

from typing import Dict

from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard

import config


class HotkeyManager(QObject):
    """Registers and listens for global hotkeys using pynput.

    Hotkeys are matched regardless of which window has focus, so they work
    even when the user is interacting with a browser.

    Instead of calling callbacks directly from the pynput background thread,
    this class emits Qt signals.  Connect to these signals from the main
    thread to safely perform GUI work.

    Signals
    -------
    * ``scan_requested``  — emitted when ``Ctrl+Shift+S`` is pressed
    * ``toggle_requested`` — emitted when ``Ctrl+Shift+H`` is pressed
    * ``region_requested`` — emitted when ``Ctrl+Shift+R`` is pressed
    * ``quit_requested``   — emitted when ``Ctrl+Shift+Q`` is pressed
    """

    scan_requested = pyqtSignal()
    toggle_requested = pyqtSignal()
    region_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        # Map hotkey combos → *signal emit* methods (thread-safe in Qt).
        self._bindings: Dict[str, object] = {
            config.HOTKEY_SCAN: self.scan_requested.emit,
            config.HOTKEY_TOGGLE: self.toggle_requested.emit,
            config.HOTKEY_REGION: self.region_requested.emit,
            config.HOTKEY_QUIT: self.quit_requested.emit,
        }
        self._listener: keyboard.GlobalHotKeys | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start listening for global hotkeys in a background thread."""
        self._listener = keyboard.GlobalHotKeys(self._bindings)
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        """Stop the hotkey listener."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
