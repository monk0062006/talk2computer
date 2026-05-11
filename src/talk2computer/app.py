from __future__ import annotations

import logging
import threading
import time

from .audio import Recorder
from .config import Config
from .hotkey import PushToTalkHotkey
from .injector import inject
from .overlay import RecordingOverlay
from .transcribe import Transcriber
from .tray import TrayController

log = logging.getLogger(__name__)


class App:
    def __init__(self, config: Config):
        self.config = config
        self.recorder = Recorder(sample_rate=config.sample_rate)
        self.transcriber = Transcriber(
            model_size=config.model_size,
            device=config.device,
            compute_type=config.compute_type,
            language=config.language,
        )
        self.overlay = RecordingOverlay()
        self.tray = TrayController(on_quit=self.shutdown)
        self.hotkey = PushToTalkHotkey(
            config.hotkey,
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._recording_started_at: float = 0.0
        self._busy = threading.Lock()
        self._stopping = False

    # --- Hotkey callbacks (run on listener thread) ---

    def _on_press(self) -> None:
        if self._stopping:
            return
        if not self._busy.acquire(blocking=False):
            log.debug("ignoring press; previous transcription still running")
            return
        try:
            self.recorder.start()
            self._recording_started_at = time.monotonic()
            self.tray.set_state("recording")
            self.overlay.show("● Recording")
        except Exception:
            log.exception("failed to start recording")
            self.tray.set_state("error", "mic")
            self._busy.release()

    def _on_release(self) -> None:
        if not self.recorder.is_recording:
            # Press was rejected; nothing to do.
            return
        duration = time.monotonic() - self._recording_started_at
        try:
            audio = self.recorder.stop()
        except Exception:
            log.exception("failed to stop recorder")
            self.tray.set_state("error", "mic")
            self.overlay.hide()
            self._busy.release()
            return

        self.overlay.hide()

        if duration < self.config.min_recording_seconds or audio.size == 0:
            self.tray.set_state("idle")
            self._busy.release()
            return

        # Transcribe + inject on a worker so the hotkey listener stays responsive.
        threading.Thread(
            target=self._transcribe_and_inject,
            args=(audio,),
            daemon=True,
        ).start()

    def _transcribe_and_inject(self, audio) -> None:
        try:
            self.tray.set_state("transcribing")
            text = self.transcriber.transcribe(audio)
            # Don't log the transcribed content — it can contain sensitive
            # dictation (passwords, OTPs, private messages). Length is enough
            # for debug.
            log.info("transcribed (%d chars)", len(text))
            if text:
                inject(
                    text,
                    method=self.config.inject_method,
                    auto_submit=self.config.auto_submit,
                )
            self.tray.set_state("idle")
        except Exception:
            log.exception("transcription failed")
            self.tray.set_state("error", "transcribe")
        finally:
            self._busy.release()

    # --- Lifecycle ---

    def run(self) -> None:
        log.info("starting talk2computer (hotkey=%s)", self.config.hotkey)
        self.overlay.start()
        self.hotkey.start()

        # Warm up the model on a background thread so the first dictation is fast.
        threading.Thread(target=self._warm_model, daemon=True).start()

        # Tray blocks the main thread until quit is selected.
        self.tray.run()

    def _warm_model(self) -> None:
        try:
            self.tray.set_state("idle", "loading model")
            self.transcriber.load()
            self.tray.set_state("idle")
        except Exception:
            log.exception("model warmup failed")
            self.tray.set_state("error", "model")

    def shutdown(self) -> None:
        if self._stopping:
            return
        self._stopping = True
        log.info("shutting down")
        try:
            self.hotkey.stop()
        except Exception:
            pass
        try:
            self.overlay.quit()
        except Exception:
            pass
