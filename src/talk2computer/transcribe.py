from __future__ import annotations

# Belt-and-suspenders: ensure CUDA DLL paths are set even if this module is
# imported without going through the package entry point.
from . import _cuda_paths  # noqa: F401

import logging
import threading

import numpy as np

log = logging.getLogger(__name__)


class Transcriber:
    """Lazy-loads a faster-whisper model and transcribes float32 mono audio."""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str | None = "en",
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self._model = None
        self._lock = threading.Lock()

    def load(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            from faster_whisper import WhisperModel

            log.info(
                "loading whisper model: size=%s device=%s compute=%s",
                self.model_size, self.device, self.compute_type,
            )
            try:
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
            except Exception as e:
                if self.device == "cuda":
                    log.warning(
                        "CUDA load failed (%s); falling back to CPU int8", e
                    )
                    self.device = "cpu"
                    self.compute_type = "int8"
                    self._model = WhisperModel(
                        self.model_size,
                        device=self.device,
                        compute_type=self.compute_type,
                    )
                else:
                    raise

    def transcribe(self, audio: np.ndarray) -> str:
        if audio.size == 0:
            return ""
        self.load()
        assert self._model is not None
        segments, _info = self._model.transcribe(
            audio,
            language=self.language,
            beam_size=1,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        return "".join(seg.text for seg in segments).strip()
