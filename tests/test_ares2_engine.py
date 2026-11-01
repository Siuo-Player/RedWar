from __future__ import annotations

import pytest

from ai.ares2 import (
    DynamicTimeManager,
    HistoryTable,
    KillerMoveTable,
    move_to_string_key,
    sort_moves_ares2,
)


def test_killer_move_table_tracks_two_slots():
    km = KillerMoveTable(max_depth=10)
    assert km.get_killers(2) == (None, None)

    # First killer at ply 2
    km.record_killer(2, "move:(1, 0)->(2, 0):")
    assert km.get_killers(2) == ("move:(1, 0)->(2, 0):", None)

    # Second killer pushes previous killer to slot 1
    km.record_killer(2, "move:(1, 1)->(3, 1):")
    assert km.get_killers(2) == ("move:(1, 1)->(3, 1):", "move:(1, 0)->(2, 0):")

    # Re-recording same move in slot 0 doesn't duplicate
    km.record_killer(2, "move:(1, 1)->(3, 1):")
    assert km.get_killers(2) == ("move:(1, 1)->(3, 1):", "move:(1, 0)->(2, 0):")


def test_history_table_records_depth_squared():
    ht = HistoryTable()
    assert ht.get_score((1, 1), (2, 2)) == 0

    ht.record_cutoff((1, 1), (2, 2), depth=4)  # 4^2 = 16
    assert ht.get_score((1, 1), (2, 2)) == 16

    ht.record_cutoff((1, 1), (2, 2), depth=10)  # 16 + 100 = 116
    assert ht.get_score((1, 1), (2, 2)) == 116


def test_dynamic_time_allocation():
    # 60 seconds left, 0 increment, 30 moves to go -> ~2 seconds
    budget = DynamicTimeManager.allocate_time_budget(60.0, 0.0, moves_to_go=30, tactical_alert=False)
    assert 1.8 <= budget <= 2.2

    # Under tactical alert, time budget scales up
    tactical_budget = DynamicTimeManager.allocate_time_budget(60.0, 0.0, moves_to_go=30, tactical_alert=True)
    assert tactical_budget > budget
    # Capped at 35% of remaining time
    assert tactical_budget <= 60.0 * 0.35

    # Low time safety
    scramble_budget = DynamicTimeManager.allocate_time_budget(0.5, 0.0, moves_to_go=10)
    assert 0.05 <= scramble_budget <= 0.5


def test_sort_moves_ares2_ordering():
    km = KillerMoveTable()
    ht = HistoryTable()

    quiet1 = {"type": "move", "start": (1, 0), "end": (2, 0)}
    quiet2 = {"type": "move", "start": (1, 1), "end": (3, 1)}
    quiet_hist = {"type": "move", "start": (0, 0), "end": (0, 1)}
    attack_move = {"type": "attack", "start": (2, 2), "end": (3, 3)}

    # Record killer for quiet1
    km.record_killer(1, move_to_string_key(quiet1))

    # Record history for quiet_hist
    ht.record_cutoff((0, 0), (0, 1), depth=8)  # 64 score

    moves = [quiet2, quiet_hist, quiet1, attack_move]
    sorted_moves = sort_moves_ares2(moves, ply=1, killer_table=km, history_table=ht)

    # Ordering should be:
    # 1. attack_move (score 100_000)
    # 2. quiet1 (killer 1, score 10_000)
    # 3. quiet_hist (history heuristic, score 64)
    # 4. quiet2 (score 0)
    assert sorted_moves[0]["type"] == "attack"
    assert move_to_string_key(sorted_moves[1]) == move_to_string_key(quiet1)
    assert move_to_string_key(sorted_moves[2]) == move_to_string_key(quiet_hist)
    assert move_to_string_key(sorted_moves[3]) == move_to_string_key(quiet2)
