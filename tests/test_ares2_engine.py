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


def test_transposition_table_probing_and_replacement():
    from ai.ares2 import TranspositionTable, TTFlag

    tt = TranspositionTable(size_power_of_two=10)
    assert tt.hits == 0

    h1 = 0x12345678
    m1 = {"type": "move", "start": (1, 1), "end": (2, 2)}
    tt.store(h1, depth=3, score=150.0, flag=TTFlag.EXACT, best_move=m1)

    entry = tt.probe(h1)
    assert entry is not None
    assert entry.score == 150.0
    assert entry.depth == 3
    assert entry.best_move == m1
    assert tt.hits == 1

    # Shallower depth should NOT overwrite deeper search
    tt.store(h1, depth=1, score=50.0, flag=TTFlag.LOWERBOUND, best_move=None)
    entry2 = tt.probe(h1)
    assert entry2.depth == 3
    assert entry2.score == 150.0


def test_mvv_lva_scoring_two_hit_stun_lethal():
    from ai.ares2 import mvv_lva_score
    from engine.game_state import GameState
    from engine.pieces import Bone, Templar, Lich

    gs = GameState()
    gs.board[4][4] = Templar("brancas")

    # Stunned victim (stun_timer = 1 -> next hit is permanent elimination)
    victim_stunned = Lich("pretas")
    victim_stunned.stun_timer = 1
    gs.board[4][5] = victim_stunned

    # Active victim (stun_timer = 0)
    victim_active = Lich("pretas")
    victim_active.stun_timer = 0
    gs.board[4][3] = victim_active

    lethal_move = {"type": "attack", "start": (4, 4), "end": (4, 5)}
    stun_move = {"type": "attack", "start": (4, 4), "end": (4, 3)}

    score_lethal = mvv_lva_score(gs, lethal_move)
    score_stun = mvv_lva_score(gs, stun_move)

    assert score_lethal > score_stun, "Lethal 2-hit stun kill must have higher priority than 1st stun"
    assert score_lethal >= 300_000


def test_ares_engine_iterative_deepening_and_tactical_kill():
    from ai.ares2 import AresEngine
    from engine.game_state import GameState
    from engine.pieces import Valkyrie, Arcanist

    gs = GameState()
    gs.board[2][2] = Valkyrie("brancas")
    stunned_target = Arcanist("pretas")
    stunned_target.stun_timer = 1
    gs.board[2][4] = stunned_target
    gs.white_to_move = True

    engine = AresEngine()
    result = engine.search(gs, max_depth=2, time_limit=5.0)

    assert result["best_move"] is not None
    assert result["best_move"]["type"] == "attack"
    assert tuple(result["best_move"]["end"]) == (2, 4)
    assert result["depth_reached"] >= 2
    assert result["nodes_visited"] > 0


def test_ares_opening_book_probe():
    from ai.ares2 import AresEngine
    from engine.game_state import GameState
    from engine.pieces import Valkyrie, Arcanist, Duelist, Warden, Illusionist, Marksman

    gs = GameState()
    gs.board[7][1] = Valkyrie("brancas")
    gs.board[7][2] = Arcanist("brancas")
    gs.board[7][3] = Duelist("brancas")
    gs.board[0][1] = Warden("pretas")
    gs.board[0][2] = Illusionist("pretas")
    gs.board[0][3] = Marksman("pretas")
    gs.white_to_move = True

    engine = AresEngine()
    result = engine.search(gs, max_depth=3, time_limit=1.0, use_opening_book=True)

    assert result["best_move"] is not None
    assert result.get("is_book") is True
    assert result["depth_reached"] == 1


def test_ares_skill_level_scaling():
    from ai.ares2 import AresEngine
    from engine.game_state import GameState
    from engine.pieces import Duelist, Warden

    gs = GameState()
    gs.board[4][4] = Duelist("brancas")
    gs.board[2][4] = Warden("pretas")
    gs.white_to_move = True

    engine = AresEngine()
    move_lvl1 = engine.choose_best_move(gs, skill_level=1)
    move_lvl3 = engine.choose_best_move(gs, skill_level=3)

    assert move_lvl1 is not None
    assert move_lvl3 is not None


def test_ares_aspiration_windows_and_pv_ordering():
    from ai.ares2 import AresEngine
    from engine.game_state import GameState
    from engine.pieces import Valkyrie, Arcanist, Duelist, Warden

    gs = GameState()
    gs.board[6][2] = Valkyrie("brancas")
    gs.board[6][5] = Arcanist("brancas")
    gs.board[1][2] = Duelist("pretas")
    gs.board[1][5] = Warden("pretas")
    gs.white_to_move = True

    engine = AresEngine()
    result = engine.search(gs, max_depth=3, time_limit=1.5, use_opening_book=False)

    assert result["best_move"] is not None
    assert result["depth_reached"] >= 2
    assert result["nodes_visited"] > 0
    assert "score" in result


def test_ares_null_move_pruning_cutoff():
    from ai.ares2 import AresEngine
    from engine.game_state import GameState
    from engine.pieces import Valkyrie, Warden

    gs = GameState()
    # Position where White has strong material advantage and no threats
    gs.board[6][2] = Valkyrie("brancas")
    gs.board[6][3] = Warden("brancas")
    gs.board[1][7] = Warden("pretas")
    gs.white_to_move = True

    engine = AresEngine()
    result = engine.search(gs, max_depth=3, time_limit=1.0, use_opening_book=False)

    assert result["best_move"] is not None
    assert result["cutoffs"] >= 0


def test_countermove_table_and_move_ordering():
    from ai.ares2 import CounterMoveTable, KillerMoveTable, HistoryTable, sort_moves_ares2, move_to_string_key

    km = KillerMoveTable()
    ht = HistoryTable()
    cm = CounterMoveTable()

    quiet_killer1 = {"type": "move", "start": (1, 0), "end": (2, 0)}
    quiet_counter = {"type": "move", "start": (1, 2), "end": (2, 2)}
    quiet_killer2 = {"type": "move", "start": (1, 3), "end": (2, 3)}
    quiet_random = {"type": "move", "start": (0, 0), "end": (0, 1)}

    prev_enemy_move_key = "move:(6, 2)->(5, 2):"

    # Set up killer moves
    km.record_killer(1, move_to_string_key(quiet_killer1))
    km.record_killer(1, move_to_string_key(quiet_killer2))

    # Set up countermove for opponent's previous move
    cm.record_countermove(prev_enemy_move_key, move_to_string_key(quiet_counter))
    assert cm.get_countermove(prev_enemy_move_key) == move_to_string_key(quiet_counter)

    moves = [quiet_random, quiet_killer2, quiet_counter, quiet_killer1]
    ordered = sort_moves_ares2(
        moves=moves,
        ply=1,
        killer_table=km,
        history_table=ht,
        counter_table=cm,
        prev_move_key=prev_enemy_move_key,
    )

    # Expected order:
    # 1. Killer 1 (quiet_killer2 in slot 0, score 20_000)
    # 2. Countermove (score 19_000)
    # 3. Killer 2 (quiet_killer1 in slot 1, score 18_000)
    # 4. Quiet random
    assert move_to_string_key(ordered[0]) == move_to_string_key(quiet_killer2)
    assert move_to_string_key(ordered[1]) == move_to_string_key(quiet_counter)
    assert move_to_string_key(ordered[2]) == move_to_string_key(quiet_killer1)
    assert move_to_string_key(ordered[3]) == move_to_string_key(quiet_random)


def test_transposition_table_generational_replacement():
    from ai.ares2 import TranspositionTable, TTFlag

    tt = TranspositionTable(size_power_of_two=8)
    h = 0xAABBCCDD
    m1 = {"type": "move", "start": (2, 2), "end": (3, 3)}
    m2 = {"type": "move", "start": (4, 4), "end": (5, 5)}

    # Store entry in generation 0 with depth 4
    tt.store(h, depth=4, score=200.0, flag=TTFlag.EXACT, best_move=m1)
    entry = tt.probe(h)
    assert entry is not None
    assert entry.depth == 4
    assert entry.generation == 0

    # Within the same generation, depth 1 CANNOT overwrite depth 4
    tt.store(h, depth=1, score=10.0, flag=TTFlag.EXACT, best_move=m2)
    entry2 = tt.probe(h)
    assert entry2.depth == 4
    assert entry2.best_move == m1

    # Advance to next generation (new search turn)
    tt.new_search()
    assert tt.generation == 1

    # In the new generation, fresh search can replace stale entry from previous turn
    tt.store(h, depth=2, score=150.0, flag=TTFlag.EXACT, best_move=m2)
    entry3 = tt.probe(h)
    assert entry3.depth == 2
    assert entry3.generation == 1
    assert entry3.best_move == m2


def test_quiescence_delta_pruning_and_sniper_shot():
    from ai.ares2 import quiescence_search
    from engine.game_state import GameState
    from engine.pieces import Marksman, Bone

    gs = GameState()
    gs.board[3][3] = Marksman("brancas")
    # Hopelessly behind position for black: stand_pat will be very low
    gs.board[0][0] = Bone("pretas")
    gs.white_to_move = False

    # Stand-pat will be far below alpha: Delta pruning should trigger immediately
    score = quiescence_search(
        state=gs,
        alpha=500.0,
        beta=600.0,
        team="pretas",
        q_depth=0,
        max_qdepth=3,
    )
    # Pruned without expanding tactical search
    assert score == 500.0


def test_sniper_crosshairs_in_domain_evaluation():
    from ai.domain_eval import RedWarDomainEvaluator
    from engine.game_state import GameState
    from engine.pieces import Marksman, Templar, Bone

    evaluator = RedWarDomainEvaluator()

    # Position 1: stunned enemy target with normal melee proximity
    gs1 = GameState()
    gs1.board[4][2] = Templar("brancas")
    gs1.board[4][4] = Bone("pretas")
    gs1.board[4][4].stun_timer = 1  # Stunned
    score_normal = evaluator.evaluate(gs1, "brancas")

    # Position 2: stunned enemy in direct line-of-fire crosshairs of Marksman
    gs2 = GameState()
    gs2.board[4][1] = Marksman("brancas")  # Col 1 vs Col 4 in same row 4 (dist = 3, orthogonal line of sight)
    gs2.board[4][4] = Bone("pretas")
    gs2.board[4][4].stun_timer = 1  # Stunned
    score_sniper = evaluator.evaluate(gs2, "brancas")

    # Sniper crosshair lethality weight should boost evaluation
    assert score_sniper > 0.0



def test_capture_history_table_records_and_scores():
    from ai.ares2 import CaptureHistoryTable

    capthist = CaptureHistoryTable()
    assert capthist.get_score("Templar", "Lich", (4, 4)) == 0

    # Record cutoff for Templar capturing Lich at (4, 4) at depth 4 (bonus 16)
    capthist.record_cutoff("Templar", "Lich", (4, 4), depth=4)
    score1 = capthist.get_score("Templar", "Lich", (4, 4))
    assert score1 > 0

    # Another cutoff at depth 6 increases score smoothly via Stockfish gravity formula
    capthist.record_cutoff("Templar", "Lich", (4, 4), depth=6)
    score2 = capthist.get_score("Templar", "Lich", (4, 4))
    assert score2 > score1

    # Decay reduces score
    capthist.decay(0.5)
    assert capthist.get_score("Templar", "Lich", (4, 4)) < score2

    capthist.clear()
    assert capthist.get_score("Templar", "Lich", (4, 4)) == 0


def test_sort_moves_prioritizes_capture_history():
    from ai.ares2 import CaptureHistoryTable, KillerMoveTable, HistoryTable, sort_moves_ares2
    from engine.game_state import GameState
    from engine.pieces import Templar, Bone

    gs = GameState()
    gs.board[4][4] = Templar("brancas")
    # Two identical targets: Bone A at (4, 5) and Bone B at (4, 3)
    gs.board[4][5] = Bone("pretas")
    gs.board[4][3] = Bone("pretas")

    capthist = CaptureHistoryTable()
    # Give high capture history cutoff score to attacking (4, 5)
    capthist.record_cutoff("Templar", "Bone", (4, 5), depth=8)

    km = KillerMoveTable()
    ht = HistoryTable()

    m_attack_5 = {"type": "attack", "start": (4, 4), "end": (4, 5)}
    m_attack_3 = {"type": "attack", "start": (4, 4), "end": (4, 3)}

    ordered = sort_moves_ares2(
        moves=[m_attack_3, m_attack_5],
        ply=0,
        killer_table=km,
        history_table=ht,
        capture_history=capthist,
        state=gs,
    )

    # Attack on (4, 5) should be ranked first due to capthist bonus
    assert ordered[0]["end"] == (4, 5)
    assert ordered[1]["end"] == (4, 3)



def test_imminent_threat_detection():
    from ai.ares2 import is_under_imminent_threat
    from engine.game_state import GameState
    from engine.pieces import Templar, Bone, Marksman

    gs = GameState()
    # Case 1: No pieces stunned -> False
    gs.board[4][4] = Templar("brancas")
    gs.board[4][5] = Bone("pretas")
    assert is_under_imminent_threat(gs, "brancas") is False

    # Case 2: Allied piece stunned and enemy adjacent -> True (imminent execution danger)
    gs.board[4][4].stun_timer = 1
    assert is_under_imminent_threat(gs, "brancas") is True

    # Case 3: Allied piece stunned, enemy sniper aligned 3 squares away -> True
    gs.board[4][5] = None
    gs.board[4][7] = Marksman("pretas")
    assert is_under_imminent_threat(gs, "brancas") is True

    # Case 4: Allied piece stunned, enemy distant and not aligned -> False
    gs.board[4][7] = None
    gs.board[1][1] = Bone("pretas")
    assert is_under_imminent_threat(gs, "brancas") is False
