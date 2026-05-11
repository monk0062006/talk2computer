from __future__ import annotations

import logging
import queue
import threading

import numpy as np
import sounddevice as sd

log = logging.getLogger(__name__)


class Recorder:
    """Records mono audio at `sample_rate` Hz to a buffer until `stop()` is called."""

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._q: queue.Queue[np.ndarray] = queue.Queue()
        self._stream: sd.InputStream | None = None
        self._running = threading.Event()

    def _callback(self, indata, frames, time_info, status):
        if status:
            log.debug("audio status: %s", status)
        # indata is float32 in [-1, 1]
        self._q.put(indata.copy())

    def start(self) -> None:
        if self._running.is_set():
            return
        # Drain any leftover frames from a previous session.
        while not self._q.empty():
            try:
                self._q.get_nowait()
            except queue.Empty:
                break
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()
        self._running.set()

    def stop(self) -> np.ndarray:
        if not self._running.is_set():
            return np.zeros(0, dtype=np.float32)
        self._running.clear()
        assert self._stream is not None
        self._stream.stop()
        self._stream.close()
        self._stream = None

        chunks: list[np.ndarray] = []
        while True:
            try:
                chunks.append(self._q.get_nowait())
            except queue.Empty:
                break
        if not chunks:
            return np.zeros(0, dtype=np.float32)
        audio = np.concatenate(chunks, axis=0)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        return audio.astype(np.float32, copy=False)

    @property
    def is_recording(self) -> bool:
        return self._running.is_set()
