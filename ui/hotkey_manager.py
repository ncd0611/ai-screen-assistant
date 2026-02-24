"""Global hotkey manager using pynput."""

from __future__ import annotations

from typing import Callable, Dict

from pynput import keyboard

import config


class HotkeyManager:
    """Registers and listens for global hotkeys using pynput.

    Hotkeys are matched regardless of which window has focus, so they work
    even when the user is interacting with a browser.

    Default bindings
    ----------------
    * ``Ctrl+Shift+S``: capture screen and query AI
    * ``Ctrl+Shift+H``: toggle overlay visibility
    * ``Ctrl+Shift+R``: open region selector
    * ``Ctrl+Shift+Q``: quit the application
    """

    def __init__(
        self,
        on_scan: Callable[[], None],
        on_toggle: Callable[[], None],
        on_region: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        """Initialise with handler callbacks.

        Args:
            on_scan: Called when the scan hotkey is pressed.
            on_toggle: Called when the toggle-visibility hotkey is pressed.
            on_region: Called when the region-select hotkey is pressed.
            on_quit: Called when the quit hotkey is pressed.
        """
        self._bindings: Dict[str, Callable[[], None]] = {
            config.HOTKEY_SCAN: on_scan,
            config.HOTKEY_TOGGLE: on_toggle,
            config.HOTKEY_REGION: on_region,
            config.HOTKEY_QUIT: on_quit,
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
