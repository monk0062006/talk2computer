from __future__ import annotations

# Must run before importing anything that touches CUDA (faster_whisper / ctranslate2).
from . import _cuda_paths  # noqa: F401

import logging
import sys

from .app import App
from .config import Config


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    config = Config.load()
    app = App(config)
    try:
        app.run()
    except KeyboardInterrupt:
        app.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
