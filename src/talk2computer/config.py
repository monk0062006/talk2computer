from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from .platform_defaults import (
    DEFAULT_COMPUTE,
    DEFAULT_DEVICE,
    DEFAULT_HOTKEY,
    DEFAULT_MODEL,
    config_dir,
)

CONFIG_PATH = config_dir() / "config.json"


@dataclass
class Config:
    model_size: str = DEFAULT_MODEL
    device: str = DEFAULT_DEVICE
    compute_type: str = DEFAULT_COMPUTE
    language: str | None = "en"
    hotkey: str = DEFAULT_HOTKEY
    sample_rate: int = 16000
    min_recording_seconds: float = 0.3
    inject_method: str = "paste"  # "paste" or "type"
    auto_submit: bool = True  # press Enter after pasting (sends chats, fires search, etc.)
    extra: dict = field(default_factory=dict)

    @classmethod
    def load(cls) -> "Config":
        if CONFIG_PATH.exists():
            try:
                data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                known = {f for f in cls.__dataclass_fields__}
                clean = {k: v for k, v in data.items() if k in known}
                return cls(**clean)
            except Exception:
                pass
        cfg = cls()
        cfg.save()
        return cfg

    def save(self) -> None:
        CONFIG_PATH.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
