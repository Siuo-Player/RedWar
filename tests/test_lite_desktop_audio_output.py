from __future__ import annotations

import os
import time

import pygame
import pytest

from ui.audio import AudioManager


def test_lite_real_desktop_audio_backend_and_playback():
    if os.environ.get("SDL_AUDIODRIVER") != "pulse":
        pytest.skip("real PulseAudio backend is exercised by the desktop acceptance lane")

    pygame.init()
    audio = AudioManager()
    try:
        assert audio.enabled is True
        assert pygame.mixer.get_init() is not None

        audio.set_enabled(True)
        for sound_name in ("move", "attack", "stun", "spell", "spawn", "surrender", "terminal"):
            audio.play(sound_name)
            deadline = time.monotonic() + 0.5
            while time.monotonic() < deadline and not pygame.mixer.get_busy():
                time.sleep(0.01)
            assert pygame.mixer.get_busy(), f"sound did not reach the active mixer: {sound_name}"
            pygame.mixer.stop()
    finally:
        pygame.mixer.quit()
        pygame.quit()
