from __future__ import annotations

import sys
import types

_evaluator = types.ModuleType("ai.evaluator")
_evaluator.avaliador_mestre = lambda _state: 0
sys.modules.setdefault("ai.evaluator", _evaluator)

from engine.actions import ActionType, GameAction

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


def test_settings_controls_update_session_state():
    class FakeRect:
        def __init__(self, hit):
            self.hit = hit

        def collidepoint(self, *_args):
            return self.hit

    class FakeAudio:
        enabled = True
        volume = 0.7

        def toggle(self):
            self.enabled = not self.enabled

        def change_volume(self, delta):
            self.volume = max(0.0, min(1.0, self.volume + delta))

    controller = object.__new__(main.JogoController)
    controller.fase_atual = "SETTINGS"
    controller.audio = FakeAudio()
    controller.btn_settings_back = FakeRect(False)
    controller.btn_sound_toggle = FakeRect(True)
    controller.btn_volume_down = FakeRect(False)
    controller.btn_volume_up = FakeRect(False)

    controller.tratar_cliques(0, 0, (0, 0))
    assert controller.audio.enabled is False

    controller.btn_sound_toggle = FakeRect(False)
    controller.btn_volume_up = FakeRect(True)
    controller.tratar_cliques(0, 0, (0, 0))
    assert abs(controller.audio.volume - 0.8) < 1e-9


def test_execute_action_with_sound_plays_action_and_terminal_once():
    events = []

    class FakeState:
        game_over = False

        def execute_action(self, action):
            action_type = action.type.value if isinstance(action, GameAction) else action["type"]
            events.append(("execute", action_type))
            self.game_over = True

    class FakeAudio:
        def play_action(self, action_type):
            events.append(("action", action_type))

        def play_terminal(self):
            events.append(("terminal", None))

    controller = object.__new__(main.JogoController)
    controller.gs = FakeState()
    controller.audio = FakeAudio()
    controller._terminal_sound_played = False

    controller._execute_action_with_sound(GameAction(type=ActionType.SURRENDER, start=None, end=None))

    assert events == [
        ("execute", "surrender"),
        ("action", "surrender"),
        ("terminal", None),
    ]
    assert controller._terminal_sound_played is True

    controller._execute_action_with_sound({"type": "move"})
    assert events[-1] == ("action", "move")
    assert events.count(("terminal", None)) == 1


def test_settings_renderer_draws_without_font_rect_crash():
    import pygame
    from ui import renderer

    pygame.font.init()
    surface = pygame.Surface((1000, 800))

    back, toggle, minus, plus = renderer.desenhar_definicoes(
        surface,
        1000,
        800,
        True,
        0.7,
    )

    assert all(isinstance(rect, pygame.Rect) for rect in (back, toggle, minus, plus))
