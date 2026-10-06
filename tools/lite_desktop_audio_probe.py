from __future__ import annotations

import time

import pygame

from ui.audio import AudioManager


pygame.init()
audio = AudioManager()
if not audio.enabled:
    raise SystemExit("AudioManager could not initialize with the CI audio backend.")

audio.set_enabled(True)
audio.play_terminal()

deadline = time.monotonic() + 1.0
while pygame.mixer.get_busy() and time.monotonic() < deadline:
    time.sleep(0.02)

pygame.mixer.quit()
pygame.quit()
