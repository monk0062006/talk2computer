from __future__ import annotations

import logging
import time

import pyperclip
from pynput.keyboard import Controller, Key

from .platform_defaults import IS_MAC

log = logging.getLogger(__name__)

_keyboard = Controller()

# macOS uses Cmd+V to paste; Windows/Linux use Ctrl+V.
_PASTE_MODIFIER = Key.cmd if IS_MAC else Key.ctrl


def _paste() -> None:
    _keyboard.press(_PASTE_MODIFIER)
    _keyboard.press("v")
    _keyboard.release("v")
    _keyboard.release(_PASTE_MODIFIER)


def _press_enter() -> None:
    _keyboard.press(Key.enter)
    _keyboard.release(Key.enter)


def inject(text: str, method: str = "paste", auto_submit: bool = False) -> None:
    if not text:
        return
    if method == "type":
        _keyboard.type(text)
        if auto_submit:
            _press_enter()
        return

    # Default: clipboard + Ctrl+V, with best-effort restore of prior clipboard.
    try:
        previous = pyperclip.paste()
    except Exception:
        previous = None

    try:
        pyperclip.copy(text)
    except Exception:
        log.exception("clipboard copy failed; falling back to direct typing")
        _keyboard.type(text)
        if auto_submit:
            _press_enter()
        return

    # Tiny delay so the focused app sees the new clipboard contents.
    time.sleep(0.03)
    _paste()

    if auto_submit:
        # Brief gap so the paste fully lands before we submit.
        time.sleep(0.05)
        _press_enter()

    if previous is not None:
        # Give the target app time to consume the paste before we overwrite.
        time.sleep(0.15)
        try:
            pyperclip.copy(previous)
        except Exception:
            pass
