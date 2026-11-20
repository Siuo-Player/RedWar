"""Focused, deterministic FrostMage/Inquisitor rule-interaction regressions.

These fixtures are synthetic. They verify local interactions and do not claim
to reproduce Issue #444's original manual game or prove a forced result for
every possible 16-vs-1 position.
"""
from __future__ import annotations

from engine.actions import ActionType
from engine.game_state import GameState
from engine.legal_actions import legal_actions
from engine.pieces import Cleric, FrostMage, Inquisitor


def _play_legal(
    gs: GameState,
    start: tuple[int, int],
    end: tuple[int, int],
    action_type: ActionType,
    *,
    spell_name: str | None = None,
) -> None:
    """Execute only an action present in the canonical legal-action list."""
    matches = [
        action
        for action in legal_actions(gs)
        if action.type is action_type
        and action.start == start
        and action.end == end
        and action.spell_name == spell_name
    ]
    assert len(matches) == 1, (
        f"Expected one legal {action_type.value} from {start} to {end} "
        f"({spell_name=}), got {len(matches)}"
    )
    gs.execute_action(matches[0])


def test_stunning_lone_inquisitor_triggers_blocked_side_terminal_result():
    """The existing RedWar rule awards the win to the side with no legal actions."""
    gs = GameState()
    gs.board[4][4] = Inquisitor("pretas")
    for r in range(2):
        for c in range(8):
            gs.board[r][c] = FrostMage("brancas")
    gs.white_to_move = True
    gs.compute_initial_hash()

    _play_legal(gs, (1, 4), (3, 4), ActionType.SPELL, spell_name="nevada")

    assert gs.game_over is True
    assert gs.white_to_move is False
    assert legal_actions(gs) == ()
    assert gs.winner == "Brancas Vencem (Oponente Bloqueado)"
    assert gs.winner_team == "brancas"


def test_ice_on_inquisitor_square_prevents_direct_focus_and_splash_targeting():
    """An ice-covered enemy tile is excluded from direct focus and cross splash."""
    gs = GameState()
    gs.board[4][4] = Inquisitor("pretas")
    gs.board[0][0] = Cleric("pretas")
    gs.board[4][1] = FrostMage("brancas")
    gs.board[1][4] = FrostMage("brancas")
    gs.white_to_move = True
    gs.compute_initial_hash()

    _play_legal(gs, (4, 1), (4, 4), ActionType.SPELL, spell_name="nevada")
    assert gs.tile_effects[4][4]["type"] == "ice"
    assert gs.board[4][4].stun_timer == 1

    _play_legal(gs, (0, 0), (1, 1), ActionType.MOVE)

    white_actions = legal_actions(gs)
    assert not any(
        action.type is ActionType.SPELL
        and action.spell_name == "nevada"
        and action.end == (4, 4)
        for action in white_actions
    )
    # A cross focused at (3, 4) would only hit the Inquisitor on (4, 4);
    # because that tile is iced, no such spell is offered as a legal action.
    assert not any(
        action.type is ActionType.SPELL
        and action.spell_name == "nevada"
        and action.end == (3, 4)
        for action in white_actions
    )
    assert gs.board[4][4] is not None


def test_indirect_splash_then_direct_nevada_is_legal_when_black_has_auxiliary_piece():
    """A legal splash can stun without icing the Inquisitor's tile; a later legal
    direct NEVADA then captures it while the stun remains active.
    """
    gs = GameState()
    gs.board[4][4] = Inquisitor("pretas")
    gs.board[0][0] = Cleric("pretas")
    gs.board[4][1] = FrostMage("brancas")
    gs.board[1][4] = FrostMage("brancas")
    gs.white_to_move = True
    gs.compute_initial_hash()

    _play_legal(gs, (4, 1), (4, 3), ActionType.SPELL, spell_name="nevada")
    assert gs.tile_effects[4][4] is None
    assert gs.board[4][4].stun_timer == 1

    _play_legal(gs, (0, 0), (1, 1), ActionType.MOVE)
    _play_legal(gs, (1, 4), (4, 4), ActionType.SPELL, spell_name="nevada")

    assert gs.board[4][4] is None


def test_material_tiebreak_compares_128_inquisitor_against_80_frostmages():
    """Checks the material resolver at its threshold, not a forced game outcome."""
    gs = GameState()
    gs.board[4][4] = Inquisitor("pretas")
    for r in range(2):
        for c in range(8):
            gs.board[r][c] = FrostMage("brancas")
    gs.turns_without_capture = gs.max_twc
    gs.compute_initial_hash()

    gs.check_game_over()

    assert gs.game_over is True
    assert "128 vs 80" in gs.winner
    assert gs.winner_team == "pretas"


def test_frostmage_outside_inquisitor_aura_has_legal_nevada_range():
    """A FrostMage at Chebyshev distance 3 is outside the radius-two silence aura."""
    gs = GameState()
    gs.board[4][4] = Inquisitor("pretas")
    gs.board[4][1] = FrostMage("brancas")
    gs.white_to_move = True
    gs.compute_initial_hash()

    assert gs.is_piece_silenced(gs.board[4][1], 4, 1) is False
    assert any(
        action.type is ActionType.SPELL
        and action.start == (4, 1)
        and action.end == (4, 3)
        and action.spell_name == "nevada"
        for action in legal_actions(gs)
    )
