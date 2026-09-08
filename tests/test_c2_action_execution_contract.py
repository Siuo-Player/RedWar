import pytest

from engine.actions import ActionType, GameAction
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def _state_with_piece(name="Bone"):
    state = GameState()
    state.board[6][0] = criar_peca_por_nome(name, "brancas")
    state.compute_initial_hash()
    return state


def _observable_snapshot(state):
    return {
        "rwen": state.to_rwen(),
        "hash": state.get_state_hash(),
        "move_log_len": len(state.move_log),
        "move_log": tuple(
            (
                entry.get("short"),
                entry.get("team"),
                entry.get("acao_escolhida"),
            )
            for entry in state.move_log
        ),
        "last_move": dict(state.last_move) if state.last_move is not None else None,
        "state_history": dict(state.state_history),
        "history_marker": state._last_history_hash,
        "turn": state.white_to_move,
        "white_time": state.white_time,
        "black_time": state.black_time,
        "game_over": state.game_over,
        "winner": state.winner,
        "score": state.current_score,
    }


def test_execute_action_accepts_canonical_game_action_and_matches_legacy_path():
    canonical_state = _state_with_piece()
    legacy_state = canonical_state.fast_clone()

    action = GameAction(ActionType.MOVE, (6, 0), (5, 0))
    canonical_state.execute_action(action)
    legacy_state.execute_action({"type": "move", "start": (6, 0), "end": (5, 0)})

    assert canonical_state.to_rwen() == legacy_state.to_rwen()
    assert canonical_state.get_state_hash() == legacy_state.get_state_hash()


def test_legal_shape_but_illegal_transition_preserves_domain_error_and_state():
    state = _state_with_piece()
    before = _observable_snapshot(state)

    invalid_transition = GameAction(ActionType.SPAWN, (6, 0), (6, 0), spawn_name="Bone")
    with pytest.raises(ValueError, match="SPAWN target square is occupied"):
        state.execute_action(invalid_transition)

    assert _observable_snapshot(state) == before


def test_illegal_action_space_membership_is_rejected_before_transition_mutation():
    state = _state_with_piece()
    before = _observable_snapshot(state)
    illegal = GameAction(ActionType.MOVE, (6, 0), (0, 0))

    with pytest.raises(ValueError, match="illegal action"):
        state.execute_action(illegal)

    assert _observable_snapshot(state) == before


def test_inquisitor_domain_rejection_preserves_specific_error_without_mutation():
    state = _state_with_piece("Cleric")
    state.board[6][2] = criar_peca_por_nome("Inquisitor", "pretas")
    state.compute_initial_hash()
    before = _observable_snapshot(state)

    action = GameAction(ActionType.SPELL, (6, 0), (5, 0), spell_name="purify")
    with pytest.raises(ValueError, match="SPELL is blocked by Inquisitor silence"):
        state.execute_action(action)

    assert _observable_snapshot(state) == before


def test_unknown_legacy_action_is_rejected_without_mutation():
    state = _state_with_piece()
    before = _observable_snapshot(state)

    with pytest.raises(ValueError):
        state.execute_action({"type": "teleport", "start": (6, 0), "end": (5, 0)})

    assert _observable_snapshot(state) == before


def test_action_contract_keeps_transition_authority_in_gamestate():
    state = _state_with_piece()
    action = GameAction(ActionType.MOVE, (6, 0), (5, 0))

    state.execute_action(action)

    assert state.board[6][0] is None
    assert state.board[5][0] is not None
    assert state.white_to_move is False
