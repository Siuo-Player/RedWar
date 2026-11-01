from __future__ import annotations

import pytest

from ai.bot import CppEngineBot
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def _create_clean_state() -> GameState:
    state = GameState()
    state.board = [[None for _ in range(8)] for _ in range(8)]
    state.white_to_move = True
    state.turns_without_capture = 0
    return state


def test_second_stun_lethal_is_prioritized_over_first_stun():
    """In Stockfish-like ordering, a second-stun (lethal kill) must be scored
    strictly higher than a first-stun on an active piece."""
    state = _create_clean_state()
    # White Templar at E4 (can attack adjacent squares)
    state.board[4][4] = criar_peca_por_nome("Templar", "brancas")
    # Black Bone at E5: ALREADY stunned (1 more stun = DEATH!)
    stunned_victim = criar_peca_por_nome("Bone", "pretas")
    stunned_victim.stun_timer = 2
    state.board[4][5] = stunned_victim
    # Black Bone at E3: Active (not stunned)
    active_enemy = criar_peca_por_nome("Bone", "pretas")
    active_enemy.stun_timer = 0
    state.board[4][3] = active_enemy

    bot = CppEngineBot(nodes=1)
    best_move = bot.play(state)

    assert best_move is not None, "Engine should find a move"
    # E4 -> E5 is the lethal kill on the stunned victim
    assert best_move.get("start") == [4, 4] or best_move.get("start") == (4, 4)
    assert best_move.get("end") == [4, 5] or best_move.get("end") == (4, 5), (
        f"Expected lethal strike on E5, got {best_move}"
    )


def test_mvv_lva_prioritizes_higher_value_victim():
    """When multiple lethal targets exist, MVV-LVA must prioritize the
    higher-value victim."""
    state = _create_clean_state()
    # White Templar at E4
    state.board[4][4] = criar_peca_por_nome("Templar", "brancas")
    # Black Lich at E5 (cost 28): stunned (lethal target)
    high_value_victim = criar_peca_por_nome("Lich", "pretas")
    high_value_victim.stun_timer = 2
    state.board[4][5] = high_value_victim
    # Black Bone at E3 (cost 8): stunned (lethal target)
    low_value_victim = criar_peca_por_nome("Bone", "pretas")
    low_value_victim.stun_timer = 2
    state.board[4][3] = low_value_victim

    bot = CppEngineBot(nodes=1)
    best_move = bot.play(state)

    assert best_move is not None
    # Must target E5 (Lich, cost 28) over E3 (Bone, cost 8)
    assert best_move.get("end") == [4, 5] or best_move.get("end") == (4, 5), (
        f"Expected MVV-LVA target on high-value Lich at E5, got {best_move}"
    )


def test_tactical_stun_is_prioritized_over_quiet_move():
    """A first stun on an active enemy must be scored higher than quiet moves."""
    state = _create_clean_state()
    # White Templar at E4
    state.board[4][4] = criar_peca_por_nome("Templar", "brancas")
    # Black Bone at E5: active enemy
    state.board[4][5] = criar_peca_por_nome("Bone", "pretas")

    bot = CppEngineBot(nodes=1)
    best_move = bot.play(state)

    assert best_move is not None
    assert best_move.get("end") == [4, 5] or best_move.get("end") == (4, 5), (
        f"Expected tactical stun on E5, got quiet move {best_move}"
    )


def test_lethal_aimed_shot_is_prioritized_over_quiet_move():
    """A lethal ranged spell (Aimed Shot on a stunned high-value target)
    must be prioritized over quiet moves."""
    state = _create_clean_state()
    # White Ranger at E2 (row 4, col 1)
    state.board[4][1] = criar_peca_por_nome("Ranger", "brancas")
    # Black Lich at E6 (row 4, col 5): stunned target
    target = criar_peca_por_nome("Lich", "pretas")
    target.stun_timer = 2
    state.board[4][5] = target

    bot = CppEngineBot(nodes=50)
    best_move = bot.play(state)

    assert best_move is not None
    assert best_move.get("type") == "spell"
    assert best_move.get("spell_name") == "aimed_shot"
    assert best_move.get("end") == (4, 5) or best_move.get("end") == [4, 5]
