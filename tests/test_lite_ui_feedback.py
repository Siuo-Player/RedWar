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
    controller.modo_ia_vs_ia = False
    controller.gs = SimpleNamespace(winner="Aniquilação (Brancas Vencem)")
    assert controller._terminal_message() == "GANHASTE!"

    controller.modo_local_2p = True
    controller.gs = SimpleNamespace(winner="Desempate por Material - Pretas Vencem")
    assert controller._terminal_message() == "VITÓRIA — PRETAS"


def test_battle_render_does_not_draw_legacy_sidebar_over_intent_sidebar():
    import inspect

    source = inspect.getsource(main.JogoController.renderizar)

    assert 'desenhar_painel_heroi(' not in source
    assert 'desenhar_log(' not in source

def test_selected_frostmage_explains_spell_silence_from_active_inquisitor():
    from engine.game_state import GameState
    from engine.pieces import FrostMage, Inquisitor

    gs = GameState()
    mage = FrostMage("brancas")
    inquisitor = Inquisitor("pretas")
    gs.board[4][4] = inquisitor
    gs.board[4][5] = mage

    reason = interaction._selected_piece_silence_reason(gs, mage, (4, 5))
    assert reason is not None
    assert "Inquisitor" in reason
    assert "NEVADA" in reason

    # The UI must follow the engine's active-source rule, not infer silence
    # from proximity alone when the Inquisitor is stunned.
    inquisitor.stun_timer = 2
    assert interaction._selected_piece_silence_reason(gs, mage, (4, 5)) is None


def test_selected_piece_silence_feedback_does_not_block_movement_or_allies():
    from engine.game_state import GameState
    from engine.pieces import FrostMage, Inquisitor, Templar

    gs = GameState()
    mage = FrostMage("brancas")
    enemy_inquisitor = Inquisitor("pretas")
    allied_inquisitor = Inquisitor("brancas")
    gs.board[4][4] = enemy_inquisitor
    gs.board[4][5] = mage

    assert interaction._selected_piece_silence_reason(gs, mage, (4, 5)) is not None
    assert mage.get_valid_moves(4, 5, gs.board, gs.tile_effects)

    gs.board[4][4] = allied_inquisitor
    assert interaction._selected_piece_silence_reason(gs, mage, (4, 5)) is None

    # The same aura should not clutter the UI for a hero with no spells.
    gs.board[4][4] = enemy_inquisitor
    no_spell_hero = Templar("brancas")
    gs.board[4][5] = no_spell_hero
    assert interaction._selected_piece_silence_reason(gs, no_spell_hero, (4, 5)) is None

def test_silence_feedback_does_not_misname_other_heroes_spells():
    from engine.game_state import GameState
    from engine.pieces import Cleric, Inquisitor

    gs = GameState()
    cleric = Cleric("brancas")
    inquisitor = Inquisitor("pretas")
    gs.board[4][4] = inquisitor
    gs.board[4][5] = cleric

    reason = interaction._selected_piece_silence_reason(gs, cleric, (4, 5))
    assert reason is not None
    assert "spells" in reason
    assert "NEVADA" not in reason

def test_silence_status_prioritizes_recovery_action():
    from engine.game_state import GameState
    from engine.pieces import FrostMage, Inquisitor

    gs = GameState()
    mage = FrostMage("brancas")
    inquisitor = Inquisitor("pretas")
    gs.board[4][4] = inquisitor
    gs.board[4][5] = mage

    assert interaction._selected_piece_status_lines(gs, mage, (4, 5)) == [
        "Silenciado: spells bloqueadas",
        "Sai do raio do Inquisitor",
    ]

