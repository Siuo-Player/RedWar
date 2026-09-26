from __future__ import annotations

import sys
import types
from types import SimpleNamespace

_evaluator = types.ModuleType("ai.evaluator")
_evaluator.avaliador_mestre = lambda _state: 0
sys.modules.setdefault("ai.evaluator", _evaluator)

import pygame

import main


def _controller_for_replays(records):
    controller = object.__new__(main.JogoController)
    controller.ecra = pygame.Surface((1000, 800))
    controller.replay_records = records
    controller.replay_error = None
    controller.replay_buttons = []
    controller.btn_replays_back = pygame.Rect(0, 0, 0, 0)
    return controller


def _sample_record():
    return {
        "game_id": "test-replay",
        "created_at": "2026-09-26T12:00:00+00:00",
        "result": {"winner": "Brancas Vencem"},
    }


def test_recent_replays_empty_state_is_safe_and_keeps_back_button():
    pygame.font.init()
    controller = _controller_for_replays([])

    controller._draw_recent_replays(1000, 800)

    assert controller.replay_buttons == []
    assert controller.btn_replays_back.width > 0
    assert controller.btn_replays_back.height > 0


def test_recent_replays_with_record_uses_list_not_rect_dict_key():
    pygame.font.init()
    record = _sample_record()
    controller = _controller_for_replays([record])

    controller._draw_recent_replays(1000, 800)

    assert len(controller.replay_buttons) == 1
    rect, stored_record = controller.replay_buttons[0]
    assert isinstance(rect, pygame.Rect)
    assert stored_record is record


def test_recent_replays_loaded_records_remain_clickable():
    pygame.font.init()
    record = _sample_record()
    controller = _controller_for_replays([record])
    called = []

    controller._open_replay = lambda selected: called.append(selected)

    controller._draw_recent_replays(1000, 800)
    rect, _ = controller.replay_buttons[0]

    for button_rect, selected_record in controller.replay_buttons:
        if button_rect.collidepoint(rect.center):
            controller._open_replay(selected_record)
            break

    assert called == [record]
