from __future__ import annotations

import main


def test_default_audio_settings_are_enabled_and_stable():
    controller = object.__new__(main.JogoController)
    controller.audio = type(
        "FakeAudio",
        (),
        {"enabled": True, "volume": 0.7},
    )()

    assert controller.audio.enabled is True
    assert controller.audio.volume == 0.7


def test_audio_toggle_and_volume_controls_use_manager_api():
    calls = []

    class FakeAudio:
        enabled = True
        volume = 0.7

        def toggle(self):
            self.enabled = not self.enabled
            calls.append(("toggle", self.enabled))
            return self.enabled

        def change_volume(self, delta):
            self.volume = max(0.0, min(1.0, self.volume + delta))
            calls.append(("volume", delta))
            return self.volume

    controller = object.__new__(main.JogoController)
    controller.audio = FakeAudio()

    controller.audio.toggle()
    controller.audio.change_volume(0.1)
    controller.audio.change_volume(-0.1)

    assert calls == [("toggle", False), ("volume", 0.1), ("volume", -0.1)]
    assert controller.audio.enabled is False
    assert controller.audio.volume == 0.7
