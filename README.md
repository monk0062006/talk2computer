# talk2computer

A local, private, free voice dictation tool — a Wispr Flow alternative. No cloud, no subscription, no audio leaves your machine. Works on **Windows** and **macOS**.

## How it works

1. Hold the configured hotkey (default: **Left Ctrl** on Windows/Linux, **Right Option** on macOS) to record your voice.
2. Release the hotkey — the audio is transcribed locally with `faster-whisper`.
3. The transcription is pasted into whatever app currently has focus, then (by default) Enter is pressed to submit.

## Install

Requires Python 3.10+.

### Windows (with NVIDIA GPU — recommended)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[cuda]"
```

The `[cuda]` extra pulls cuBLAS/cuDNN/nvrtc (~1.5 GB). Skip it (`pip install -e .`) if you don't have an NVIDIA GPU — the app will run on CPU.

### Windows (CPU only) / macOS / Linux

```bash
python -m venv .venv
# macOS / Linux:
source .venv/bin/activate
# Windows PowerShell:
# .\.venv\Scripts\Activate.ps1

pip install -e .
```

First run downloads the chosen Whisper model (default `medium` on Windows-CUDA, `small` elsewhere) into the local Hugging Face cache.

## macOS-specific setup

macOS requires you to grant the app two permissions in **System Settings → Privacy & Security**:

1. **Microphone** — required to record audio.
2. **Accessibility** — required for the global hotkey listener to see your key presses and for the auto-paste to send Cmd+V.

When you first run the app, macOS will pop up permission prompts; if it doesn't, grant them manually for your Python executable (or the terminal app you launched from).

## Run

```bash
python -m talk2computer
```

A system tray icon will appear. Hold the hotkey, speak, release.

## Configuration

Settings are stored in:
- **Windows:** `%APPDATA%\talk2computer\config.json`
- **macOS:** `~/Library/Application Support/talk2computer/config.json`
- **Linux:** `~/.config/talk2computer/config.json`

Editable fields:

| Field | Description |
|---|---|
| `model_size` | `tiny`, `base`, `small`, `medium`, `large-v3` |
| `device` | `cpu` or `cuda` (falls back to `cpu` automatically if CUDA fails) |
| `compute_type` | `int8`, `float16`, `float32` |
| `language` | ISO code (e.g. `en`) or `null` for auto-detect |
| `hotkey` | pynput key name. Examples: `Key.ctrl_l`, `Key.ctrl_r`, `Key.alt_r`, `Key.caps_lock`, `Key.f12` |
| `auto_submit` | `true` to press Enter after pasting (submits chats, fires search) |
| `inject_method` | `paste` (clipboard + Ctrl/Cmd+V) or `type` (character-by-character) |

## License

MIT
