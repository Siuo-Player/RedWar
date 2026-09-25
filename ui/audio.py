"""Small, dependency-free audio manager for the local RedWar product.

The Lite product uses procedurally generated PCM tones rather than third-party
audio files. This keeps the local release self-contained and avoids external
asset licensing requirements.
"""

from __future__ import annotations

from array import array
import math
from typing import Final

import pygame


DEFAULT_VOLUME: Final[float] = 0.70
MIN_VOLUME: Final[float] = 0.0
MAX_VOLUME: Final[float] = 1.0
VOLUME_STEP: Final[float] = 0.10


class AudioManager:
    def __init__(self, volume: float = DEFAULT_VOLUME) -> None:
        self.enabled = False
        self.volume = max(MIN_VOLUME, min(MAX_VOLUME, float(volume)))
        self._sounds: dict[str, pygame.mixer.Sound] = {}

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.enabled = True
            self._build_sounds()
            self._apply_volume()
        except pygame.error as exc:
            print(f"⚠️ Áudio indisponível: {exc}")

    @staticmethod
    def _tone(frequency: float, duration: float, volume: float = 0.35) -> pygame.mixer.Sound:
        sample_rate = 22050
        count = max(1, int(sample_rate * duration))
        samples = array("h")
        amplitude = int(32767 * volume)
        fade = max(1, int(count * 0.08))
        for i in range(count):
            envelope = min(1.0, i / fade, (count - i) / fade)
            samples.append(int(amplitude * envelope * math.sin(2.0 * math.pi * frequency * i / sample_rate)))
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _build_sounds(self) -> None:
        self._sounds = {
            "move": self._tone(420.0, 0.08, 0.25),
            "attack": self._tone(170.0, 0.12, 0.32),
            "stun": self._tone(250.0, 0.13, 0.30),
            "spell": self._tone(620.0, 0.10, 0.26),
            "spawn": self._tone(520.0, 0.14, 0.24),
            "surrender": self._tone(120.0, 0.18, 0.30),
            "terminal": self._tone(85.0, 0.35, 0.34),
        }

    def _apply_volume(self) -> None:
        for sound in self._sounds.values():
            sound.set_volume(self.volume)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def set_volume(self, volume: float) -> float:
        self.volume = max(MIN_VOLUME, min(MAX_VOLUME, float(volume)))
        self._apply_volume()
        return self.volume

    def change_volume(self, delta: float) -> float:
        return self.set_volume(self.volume + delta)

    def play(self, sound_name: str) -> None:
        if not self.enabled:
            return
        sound = self._sounds.get(sound_name)
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass

    def play_action(self, action_type: str) -> None:
        self.play(str(action_type).lower())

    def play_terminal(self) -> None:
        self.play("terminal")
