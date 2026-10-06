from __future__ import annotations

import sys
import time
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui.audio import AudioManager


pygame.init()
audio = AudioManager()
if not audio.enabled:
    raise SystemExit("AudioManager could not initialize with the CI audio backend.")

audio.set_enabled(True)
channel = audio._sounds["terminal"].play()  # type: ignore[union-attr]
if channel is None:
    pygame.mixer.quit()
    pygame.quit()
    raise SystemExit("terminal sound could not start a mixer channel")

deadline = time.monotonic() + 1.0
while not channel.get_busy() and time.monotonic() < deadline:
    time.sleep(0.02)

if not channel.get_busy():
    pygame.mixer.quit()
    pygame.quit()
    raise SystemExit("terminal sound never became active on the real mixer")

while channel.get_busy():
    time.sleep(0.02)

# Give PulseAudio enough time to consume the final mixer buffer.
time.sleep(0.5)

pygame.mixer.quit()
pygame.quit()
