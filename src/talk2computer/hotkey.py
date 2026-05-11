from __future__ import annotations

import logging
from typing import Callable

from pynput import keyboard

log = logging.getLogger(__name__)


def _resolve_key(spec: str):
    """Resolve a config string like 'Key.ctrl_r' or 'f1' or a single char into a pynput key."""
    if spec.startswith("Key."):
        name = spec.split(".", 1)[1]
        return getattr(keyboard.Key, name)
    # Single-character key
    if len(spec) == 1:
        return keyboard.KeyCode.from_char(spec)
    # Function keys etc.
    if hasattr(keyboard.Key, spec):
        return getattr(keyboard.Key, spec)
    raise ValueError(f"Unrecognized hotkey spec: {spec!r}")


class PushToTalkHotkey:
    """Fires `on_press`/`on_release` callbacks while a specific key is held.

    Repeated press events from key auto-repeat are debounced — `on_press` fires
    only on the leading edge, `on_release` only on the trailing edge.
    """

    def __init__(
        self,
        key_spec: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ):
        self._target = _resolve_key(key_spec)
        self._on_press = on_press
        self._on_release = on_release
        self._held = False
        self._listener: keyboard.Listener | None = None

    def _matches(self, key) -> bool:
        if key == self._target:
            return True
        # Match KeyCode by char if specified that way.
        if isinstance(self._target, keyboard.KeyCode) and isinstance(key, keyboard.KeyCode):
            return self._target.char == key.char
        return False

    def _handle_press(self, key) -> None:
        if not self._matches(key) or self._held:
            return
        self._held = True
        try:
            self._on_press()
        except Exception:
            log.exception("hotkey on_press handler failed")

    def _handle_release(self, key) -> None:
        if not self._matches(key) or not self._held:
            return
        self._held = False
        try:
            self._on_release()
        except Exception:
            log.exception("hotkey on_release handler failed")

    def start(self) -> None:
        self._listener = keyboard.Listener(
            on_press=self._handle_press,
            on_release=self._handle_release,
        )
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
