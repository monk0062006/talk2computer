from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk

log = logging.getLogger(__name__)


class RecordingOverlay:
    """A tiny always-on-top label showing recording state.

    tkinter is not thread-safe, so a background thread posts messages onto a
    queue and the Tk mainloop polls it.
    """

    def __init__(self):
        self._cmd_q: queue.Queue[tuple[str, str]] = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def show(self, text: str = "● Recording", color: str = "#dc3232") -> None:
        self._cmd_q.put(("show", f"{color}|{text}"))

    def hide(self) -> None:
        self._cmd_q.put(("hide", ""))

    def quit(self) -> None:
        self._cmd_q.put(("quit", ""))

    def _run(self) -> None:
        try:
            root = tk.Tk()
        except Exception:
            log.exception("failed to start overlay tk root")
            return
        root.withdraw()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        try:
            root.attributes("-alpha", 0.88)
        except tk.TclError:
            pass

        frame = tk.Frame(root, bg="#1e1e1e", padx=14, pady=8)
        frame.pack()
        label = tk.Label(
            frame,
            text="",
            fg="#ffffff",
            bg="#1e1e1e",
            font=("Segoe UI", 11, "bold"),
        )
        label.pack()

        def position():
            root.update_idletasks()
            w, h = root.winfo_reqwidth(), root.winfo_reqheight()
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            x = (sw - w) // 2
            y = sh - h - 80
            root.geometry(f"+{x}+{y}")

        def pump():
            try:
                while True:
                    cmd, payload = self._cmd_q.get_nowait()
                    if cmd == "show":
                        color, text = payload.split("|", 1)
                        label.config(text=text, fg=color)
                        position()
                        root.deiconify()
                    elif cmd == "hide":
                        root.withdraw()
                    elif cmd == "quit":
                        root.destroy()
                        return
            except queue.Empty:
                pass
            root.after(40, pump)

        root.after(40, pump)
        root.mainloop()
