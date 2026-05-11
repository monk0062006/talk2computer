"""Single source of truth for platform-specific defaults.

Centralizing these here keeps config.py / injector.py / transcribe.py from
each re-deriving the same `sys.platform` checks.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

IS_WIN = sys.platform == "win32"
IS_MAC = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")


def config_dir() -> Path:
    if IS_WIN:
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        p = Path(base) / "talk2computer"
    elif IS_MAC:
        p = Path.home() / "Library" / "Application Support" / "talk2computer"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else (Path.home() / ".config")
        p = base / "talk2computer"
    p.mkdir(parents=True, exist_ok=True)
    return p


# --- Model / device defaults -------------------------------------------------
# Windows + NVIDIA is the common consumer case where CUDA is fast. Mac uses
# CPU with int8 quantization — plenty fast on Apple Silicon and avoids the
# Metal/Core ML setup pain. Linux defaults to CPU and can be overridden by
# editing config.json.

if IS_WIN:
    DEFAULT_MODEL = "medium"
    DEFAULT_DEVICE = "cuda"
    DEFAULT_COMPUTE = "float16"
else:
    DEFAULT_MODEL = "small"
    DEFAULT_DEVICE = "cpu"
    DEFAULT_COMPUTE = "int8"


# --- Hotkey defaults ---------------------------------------------------------
# Mac: Right Option (`Key.alt_r`) is a "dead" key for most users and doesn't
# conflict with the Cmd-based shortcuts the OS uses everywhere.
# Win/Linux: keep parity with the current talk2computer default (Left Ctrl).
# Note: Left Ctrl conflicts with Ctrl+X shortcuts — user explicitly chose this.

if IS_MAC:
    DEFAULT_HOTKEY = "Key.alt_r"
else:
    DEFAULT_HOTKEY = "Key.ctrl_l"
