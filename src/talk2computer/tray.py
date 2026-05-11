from __future__ import annotations

import logging
import threading
from typing import Callable

import pystray
from PIL import Image, ImageDraw

log = logging.getLogger(__name__)

_STATE_COLORS = {
    "idle":         ((40, 40, 40),  (180, 180, 180)),
    "recording":    ((40, 40, 40),  (220, 50, 50)),
    "transcribing": ((40, 40, 40),  (230, 170, 40)),
    "error":        ((40, 40, 40),  (220, 80, 80)),
}


def _make_icon(state: str) -> Image.Image:
    bg, fg = _STATE_COLORS.get(state, _STATE_COLORS["idle"])
    img = Image.new("RGB", (64, 64), bg)
    d = ImageDraw.Draw(img)
    d.ellipse((14, 14, 50, 50), fill=fg)
    return img


class TrayController:
    """Wraps a pystray Icon and exposes a thread-safe `set_state(...)`."""

    def __init__(self, on_quit: Callable[[], None]):
        self._on_quit = on_quit
        self._icon = pystray.Icon(
            "talk2computer",
            _make_icon("idle"),
            "talk2computer — idle",
            menu=pystray.Menu(
                pystray.MenuItem("talk2computer", None, enabled=False),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._quit),
            ),
        )
        self._thread: threading.Thread | None = None

    def _quit(self, icon, item) -> None:
        try:
            self._on_quit()
        finally:
            icon.stop()

    def set_state(self, state: str, detail: str = "") -> None:
        try:
            self._icon.icon = _make_icon(state)
            tip = f"talk2computer — {state}"
            if detail:
                tip += f": {detail}"
            self._icon.title = tip
        except Exception:
            log.debug("tray set_state failed", exc_info=True)

    def run(self) -> None:
        # Blocks the current thread — pystray on Windows must run on the main thread.
        self._icon.run()

    def stop(self) -> None:
        try:
            self._icon.stop()
        except Exception:
            pass
