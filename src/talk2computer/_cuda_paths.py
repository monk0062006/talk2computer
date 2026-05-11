"""Make CUDA DLLs from pip-installed nvidia-* packages discoverable on Windows.

Import this module *before* anything that loads CUDA (faster_whisper /
ctranslate2 / onnxruntime). It is safe to import on non-Windows or when the
nvidia packages are not installed — it becomes a no-op.

Why both PATH and add_dll_directory: ctranslate2 loads cuBLAS via the raw
Win32 LoadLibrary API, which obeys PATH but ignores directories registered
through os.add_dll_directory (that only helps ctypes.CDLL).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def setup() -> list[str]:
    if sys.platform != "win32":
        return []
    try:
        import nvidia  # type: ignore
    except ImportError:
        return []

    bin_dirs: list[str] = []
    for root in (Path(p) for p in nvidia.__path__):
        if not root.exists():
            continue
        for sub in root.iterdir():
            bin_dir = sub / "bin"
            if bin_dir.is_dir():
                bin_dirs.append(str(bin_dir))

    if not bin_dirs:
        return []

    current_path = os.environ.get("PATH", "")
    os.environ["PATH"] = os.pathsep.join(bin_dirs) + os.pathsep + current_path

    for d in bin_dirs:
        try:
            os.add_dll_directory(d)
        except (OSError, AttributeError):
            pass

    return bin_dirs


# Side-effect import: run immediately so anything imported after us inherits PATH.
_REGISTERED = setup()
