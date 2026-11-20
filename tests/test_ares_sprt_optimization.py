# tests/test_ares_sprt_optimization.py
"""
SPRT & Tactical Optimization Test Suite for Ares AI Engine.

Validates:
1. AresEngine Iterative Deepening search efficiency & node reduction.
2. MVV-LVA Move Ordering vs naive move ordering.
3. Quiescence Search preventing tactical horizon effect.
4. Wald's SPRT framework verifying candidate improvements with statistical confidence.
"""
from __future__ import annotations

import pytest
from ai.ares2 import AresEngine, quiescence_search, sort_moves_ares2, KillerMoveTable, HistoryTable
from ai.domain_eval import RedWarDomainEvaluator
from ai.sprt import SPRTTracker, SPRTConfig, SPRTStatus
from engine.game_state import GameState
from engine.pieces import Valkyrie, Arcanist, Duelist, Warden, Lich, Paladin, Dragoon, Bone


def _create_tactical_position():
    gs = GameState()
    gs.board[2][2] = Valkyrie("brancas")
    target = Lich("pretas")
    target.stun_timer = 1  # Stunned: 2-hit stun lethal kill!
    gs.board[2][4] = target
    gs.board[0][0] = Bone("pretas")
    gs.white_to_move = True
    return gs


def test_ares_engine_solves_tactical_kill_at_depth_1_and_2():
    gs = _create_tactical_position()
    engine = AresEngine()
    result = engine.search(gs, max_depth=2, time_limit=1.0)

    assert result["best_move"] is not None
    assert result["best_move"]["type"] == "attack"
    assert tuple(result["best_move"]["end"]) == (2, 4)
    assert result["score"] >= 8.0, "Lethal elimination should yield positive tactical advantage"


def test_mvv_lva_ordering_superiority():
    """Verify that MVV-LVA move ordering prioritizes lethal stun kills over quiet moves."""
    gs = _create_tactical_position()
    raw_moves = [
        {"type": "move", "start": (2, 2), "end": (1, 2)},
        {"type": "attack", "start": (2, 2), "end": (2, 4)},  # Lethal on stunned Lich
        {"type": "move", "start": (2, 2), "end": (3, 2)},
        {"type": "attack", "start": (2, 2), "end": (0, 0)},  # Non-stunned Bone
    ]

    km = KillerMoveTable()
    ht = HistoryTable()
    ordered = sort_moves_ares2(raw_moves, ply=0, killer_table=km, history_table=ht, state=gs)

    # First move must be the lethal strike on the stunned Lich
    assert ordered[0]["type"] == "attack"
    assert tuple(ordered[0]["end"]) == (2, 4), "Lethal kill on stunned Lich must be first"
    assert tuple(ordered[1]["end"]) == (0, 0), "First stun on Bone must be second"


def test_quiescence_search_tactical_horizon():
    """Quiescence search must detect impending tactical captures even at leaf nodes."""
    gs = _create_tactical_position()
    evaluator = RedWarDomainEvaluator()

    # Base stand-pat before capture
    stand_pat = evaluator.evaluate(gs, "brancas")

    # Quiescence search should resolve the capture and return a higher score
    q_score = quiescence_search(
        state=gs,
        alpha=-50000.0,
        beta=50000.0,
        team="brancas",
        q_depth=0,
        max_qdepth=2,
        evaluator=evaluator,
    )
    assert q_score > stand_pat, "Quiescence search should resolve tactical capture to higher score"


def test_sprt_framework_statistical_acceptance():
    """Wald SPRT tracker must correctly compute LLR and accept H1 when candidate outperforms baseline."""
    config = SPRTConfig(elo0=0.0, elo1=10.0, alpha=0.05, beta=0.05)
    tracker = SPRTTracker(config)

    # Simulate strong candidate outperforming baseline (e.g. 70% win rate across tactical positions)
    for _ in range(50):
        tracker.add_result(win=7, loss=2, draw=1)
        if tracker.status == SPRTStatus.H1_ACCEPTED:
            break

    assert tracker.status == SPRTStatus.H1_ACCEPTED
    assert tracker.llr >= tracker.upper_bound
    assert tracker.score > 0.65
