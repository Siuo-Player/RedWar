# tests/test_frostmage_inquisitor_endgame_audit.py
"""
Deterministic Audit of FrostMage vs Inquisitor Endgame Dynamics (Issue #444).

Investigates whether 16 FrostMages vs 1 Inquisitor is:
1. Legally winnable with correct FrostMage play.
2. A legitimate losing/stalemate position.
3. An interaction/ice-placement deadlock.

Conclusion:
Under authoritative RedWar rules:
- Stun on a lone Inquisitor immediately leaves Black with zero legal moves on their turn,
  triggering 'Oponente Bloqueado' and awarding the win to Black ('Pretas Vencem (Oponente Bloqueado)').
- Refusing to stun leads to a loss on 50-turn material tiebreak: Inquisitor (cost 128) > 16 FrostMages (cost 80).
- Direct NEVADA on Inquisitor creates an ice shield on Inquisitor's tile that prevents direct retargeting
  and cross-AOE follow-up until ice melts (by which time stun has already expired).
- If an auxiliary enemy piece is present, indirect splash targeting (centering on an adjacent tile)
  allows a 2-turn execution by avoiding ice placement on the victim's square.
"""
from __future__ import annotations

import pytest

from engine.actions import ActionType
from engine.game_state import GameState
from engine.legal_actions import legal_actions
from engine.pieces import Cleric, FrostMage, Inquisitor


def test_lone_inquisitor_stun_triggers_immediate_terminal_block():
    """Stunning a lone enemy piece leaves them with 0 legal moves on their turn,
    immediately triggering the 'Oponente Bloqueado' terminal condition.
    """
    gs = GameState()
    gs.board[4][4] = Inquisitor("pretas")
    for r in range(2):
        for c in range(8):
            gs.board[r][c] = FrostMage("brancas")
    gs.white_to_move = True
    gs.compute_initial_hash()

    # White FrostMage at (1, 4) casts NEVADA targeting (3, 4), splashing Inquisitor at (4, 4)
    gs.make_action((1, 4), (3, 4), "spell", spell_name="nevada")

    assert gs.game_over is True
    assert gs.winner == "Pretas Vencem (Oponente Bloqueado)"
    assert gs.winner_team == "pretas"


def test_frostmage_ice_shield_prevents_direct_retargeting_and_cross_aoe():
    """Direct targeting of NEVADA on Inquisitor puts ice on Inquisitor's tile,
    shielding Inquisitor from subsequent cross-AOE and direct retargeting until ice melts.
    """
    gs = GameState()
    gs.board[4][4] = Inquisitor("pretas")
    gs.board[0][0] = Cleric("pretas")  # Auxiliary piece so Black is not blocked
    gs.board[4][1] = FrostMage("brancas")
    gs.board[1][4] = FrostMage("brancas")
    gs.white_to_move = True
    gs.compute_initial_hash()

    # White FrostMage at (4, 1) casts NEVADA directly on (4, 4)
    gs.make_action((4, 1), (4, 4), "spell", spell_name="nevada")
    assert gs.tile_effects[4][4] is not None
    assert gs.tile_effects[4][4]["type"] == "ice"

    # Black moves Cleric
    gs.make_action((0, 0), (1, 0), "move")

    # On White's turn, (4, 4) has ice: direct retargeting is forbidden
    actions = legal_actions(gs)
    assert not any(a.type == ActionType.SPELL and a.end == (4, 4) for a in actions)

    # Cross-AOE from adjacent square (3, 4) skips (4, 4) because tile already has ice
    gs.make_action((1, 4), (3, 4), "spell", spell_name="nevada")
    assert gs.board[4][4] is not None  # Inquisitor survives on the ice tile


def test_frostmage_can_eliminate_inquisitor_via_indirect_splash_when_auxiliary_piece_exists():
    """When an auxiliary enemy piece exists (preventing immediate terminal block) and the first
    NEVADA is cast on an adjacent tile (leaving Inquisitor's tile free of ice), a second FrostMage
    can legally target Inquisitor directly on the next turn and execute the capture.
    """
    gs = GameState()
    gs.board[4][4] = Inquisitor("pretas")
    gs.board[0][0] = Cleric("pretas")
    gs.board[4][1] = FrostMage("brancas")
    gs.board[1][4] = FrostMage("brancas")
    gs.white_to_move = True
    gs.compute_initial_hash()

    # Turn 1: White splashes Inquisitor by centering at (4, 3)
    gs.make_action((4, 1), (4, 3), "spell", spell_name="nevada")
    assert gs.tile_effects[4][4] is None  # Inquisitor's tile has no ice
    assert gs.board[4][4].stun_timer == 1

    # Black moves Cleric
    gs.make_action((0, 0), (1, 0), "move")

    # Turn 2: Second FrostMage targets Inquisitor directly at (4, 4) while stunned
    gs.make_action((1, 4), (4, 4), "spell", spell_name="nevada")
    assert gs.board[4][4] is None  # Inquisitor captured!


def test_sixteen_frostmages_vs_lone_inquisitor_material_outcome():
    """If White refuses to stun the lone Inquisitor, after 50 turns without capture,
    Inquisitor (cost 128) defeats 16 FrostMages (cost 80 = 16 * 5) on material tiebreak.
    """
    gs = GameState()
    gs.board[4][4] = Inquisitor("pretas")
    for r in range(2):
        for c in range(8):
            gs.board[r][c] = FrostMage("brancas")
    gs.turns_without_capture = 50
    gs.compute_initial_hash()
    gs.check_game_over()

    assert gs.game_over is True
    assert "128 vs 80" in gs.winner
    assert gs.winner_team == "pretas"


def test_inquisitor_silence_aura_boundary_and_frostmage_range():
    """FrostMage at Chebyshev distance > 2 from Inquisitor is outside the silence aura
    and can cast NEVADA up to Manhattan distance 3 to hit Inquisitor.
    """
    gs = GameState()
    gs.board[4][4] = Inquisitor("pretas")
    gs.board[4][1] = FrostMage("brancas")
    gs.white_to_move = True
    gs.compute_initial_hash()

    # Chebyshev distance max(|4-4|, |1-4|) = 3 > 2 -> Not silenced
    assert gs.is_piece_silenced(gs.board[4][1], 4, 1) is False

    # Manhattan distance |4-4| + |3-1| = 2 <= 3 -> Valid focus target
    actions = legal_actions(gs)
    assert any(a.type == ActionType.SPELL and a.start == (4, 1) and a.end == (4, 3) for a in actions)
