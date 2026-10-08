from dataclasses import dataclass
import numpy as np


@dataclass
class AudioBlock:
    samples: np.ndarray
    start: float
    rate: int
    discontinuity: bool = False


@dataclass
class Utterance:
    id: int
    audio: np.ndarray
    start: float
    end: float
    final: bool
    captured_at: float


@dataclass
class Caption:
    id: int
    start: float
    end: float
    original: str
    translation: str = ''
    language: str = 'en'
    source: str = 'system'
    final: bool = True
    latency: float | None = None


class Stabilizer:
    """Only extend a common prefix across consecutive interim hypotheses."""
    def __init__(self):
        self.previous = ''
        self.stable = ''

    def update(self, text: str, final: bool = False) -> str:
        if final:
            self.previous = self.stable = ''
            return text.strip()
        n = 0
        for a, b in zip(self.previous, text):
            if a != b:
                break
            n += 1
        prefix = text[:n]
        # Avoid presenting a partial English word as stable.
        if prefix and prefix[-1].isascii() and not prefix[-1].isspace():
            prefix = prefix.rsplit(' ', 1)[0] + ' ' if ' ' in prefix else ''
        if len(prefix) >= len(self.stable) and prefix.startswith(self.stable):
            self.stable = prefix
        self.previous = text
        return self.stable.strip() or text.strip()
