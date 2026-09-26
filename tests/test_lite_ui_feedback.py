from __future__ import annotations

import sys
import types
from types import SimpleNamespace

_evaluator = types.ModuleType("ai.evaluator")
_evaluator.avaliador_mestre = lambda _state: 0
sys.modules.setdefault("ai.evaluator", _evaluator)

import pygame

import main
from tools.replay import hover_visuals, interaction


def _state_with_pieces(*pieces):
    board = [[None for _ in range(8)] for _ in range(8)]
    for row, col, piece in pieces:
        board[row][col] = piece
    return SimpleNamespace(board=board)


def test_silence_effect_targets_only_enemy_pieces_in_active_inquisitor_radius():
    inquisitor = SimpleNamespace(name="Inquisitor", team="pretas", can_act=lambda: True)
    enemy_inside = SimpleNamespace(name="Ranger", team="brancas")
    enemy_outside = SimpleNamespace(name="Ranger", team="brancas")
    allied_inside = SimpleNamespace(name="Ranger", team="pretas")

    gs = _state_with_pieces(
        (4, 4, inquisitor),
        (4, 6, enemy_inside),
        (4, 7, enemy_outside),
        (5, 5, allied_inside),
    )

    assert hover_visuals._silenced_enemy_cells(gs) == {(4, 6)}


def test_stunned_inquisitor_does_not_apply_visual_silence():
    inquisitor = SimpleNamespace(name="Inquisitor", team="pretas", can_act=lambda: False)
    enemy = SimpleNamespace(name="Ranger", team="brancas")
    gs = _state_with_pieces((4, 4, inquisitor), (4, 5, enemy))

    assert hover_visuals._silenced_enemy_cells(gs) == set()


def test_sidebar_wraps_long_feedback_without_overflowing_line_width():
    pygame.font.init()
    font = pygame.font.SysFont("arial", 13)
    lines = interaction._wrap_lines(
        font,
        "Ações legais: Mover / Atacar / Atordoar / Usar NEVADA",
        150,
    )

    assert len(lines) > 1
    assert all(font.size(line)[0] <= 150 for line in lines)


def test_terminal_message_is_explicit_for_player_and_hotseat():
    controller = object.__new__(main.JogoController)
    controller.modo_local_2p = False
    controller.gs = SimpleNamespace(winner="Aniquilação (Brancas Vencem)")
    assert controller._terminal_message() == "GANHASTE!"

    controller.modo_local_2p = True
    controller.gs = SimpleNamespace(winner="Desempate por Material - Pretas Vencem")
    assert controller._terminal_message() == "VITÓRIA — PRETAS"
