from __future__ import annotations
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


def data_dir() -> Path:
    p = Path(os.environ.get('YUSPEAK_DATA_DIR', str(Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'YuSpeak')))
    p.mkdir(parents=True, exist_ok=True)
    return p


def resource(name: str) -> Path:
    return Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent)) / 'assets' / name


@dataclass
class CaptionStyle:
    font: str = 'Microsoft YaHei UI'
    size: int = 28
    bold: bool = True
    original_color: str = '#ffffff'
    translation_color: str = '#7de4d4'
    outline: int = 2
    shadow: bool = True
    opacity: int = 55
    spacing: int = 12
    width: int = 1000
    lines: int = 3
    order: str = 'original'
    mode: str = 'bilingual'
    locked: bool = True
    x: int | None = None
    y: int | None = None
    expiry: float = 7.0


@dataclass
class Settings:
    ui_language: str = 'zh'
    theme: str = 'dark'
    source: str = 'system'
    device_name: str = ''
    language: str = 'en'
    model: str = 'base'
    inference: str = 'cpu'
    model_root: str = ''
    save_sessions: bool = True
    save_audio: bool = False
    close_to_tray: bool = True
    log_level: str = 'INFO'
    hotkeys: dict = field(default_factory=lambda: {'overlay': 'Ctrl+Alt+S', 'listen': 'Ctrl+Alt+R', 'lock': 'Ctrl+Alt+L'})
    caption: CaptionStyle = field(default_factory=CaptionStyle)

    @property
    def models(self) -> Path:
        p = Path(self.model_root) if self.model_root else data_dir() / 'models'
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def load(cls):
        try:
            d = json.loads((data_dir() / 'settings.json').read_text('utf-8'))
            style = d.pop('caption', {})
            s = cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
            s.caption = CaptionStyle(**{k: v for k, v in style.items() if k in CaptionStyle.__dataclass_fields__})
            return s
        except (OSError, ValueError, TypeError):
            return cls()

    def save(self):
        p = data_dir() / 'settings.json'
        tmp = p.with_suffix('.tmp')
        tmp.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), 'utf-8')
        tmp.replace(p)
