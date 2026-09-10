import copy

import pytest

from engine.actions import ActionType, GameAction, normalize_action
from engine.game_state import GameState
from engine.legal_actions import is_legal_action, legal_actions, resolve_legal_action
from engine.pieces import criar_peca_por_nome


def _live_state(*, white_to_move: bool = True) -> GameState:
    state = GameState()
    state.board[7][0] = criar_peca_por_nome("Ranger", "brancas")
    state.board[0][7] = criar_peca_por_nome("Ranger", "pretas")
    state.white_to_move = white_to_move
    state.compute_initial_hash()
    return state


def test_surrender_is_a_canonical_non_board_action():
    action = GameAction(ActionType.SURRENDER, None, None)

    assert action.to_dict() == {"type": "surrender"}
    assert normalize_action({"type": "surrender"}) == action
    assert action not in legal_actions(_live_state())
    assert not is_legal_action(_live_state(), action)
    assert resolve_legal_action(_live_state(), action) == action


def test_surrender_rejects_board_coordinates():
    with pytest.raises(ValueError, match="must not contain board coordinates"):
        normalize_action({"type": "surrender", "start": (7, 0), "end": (7, 1)})


def test_surrender_from_side_to_move_ends_game_without_board_mutation():
    state = _live_state(white_to_move=True)
    before_board = copy.deepcopy(state.to_rwen())
    before_hash = state.get_state_hash()
    before_counter = state.turns_without_capture

    state.execute_action({"type": "surrender"})

    assert state.game_over is True
    assert state.winner == "Desistência (Brancas) - Pretas Vencem"
    assert state.to_rwen() == before_board
    assert state.get_state_hash() == before_hash
    assert state.turns_without_capture == before_counter
    assert state.last_move == {"type": "surrender", "team": "brancas"}
    assert state.move_log[-1]["acao_escolhida"] == {
        "type": "surrender",
        "actor_team": "brancas",
    }


def test_surrender_honors_explicit_actor_team_and_side_to_move():
    state = _live_state(white_to_move=False)
    before = state.to_rwen()

    with pytest.raises(ValueError, match="does not match side to move"):
        state.execute_action({"type": "surrender", "actor_team": "brancas"})

    assert state.game_over is False
    assert state.winner is None
    assert state.to_rwen() == before


def test_surrender_works_for_black_side_to_move():
    state = _live_state(white_to_move=False)

    state.execute_action(GameAction(ActionType.SURRENDER, None, None, actor_team="pretas"))

    assert state.game_over is True
    assert state.winner == "Desistência (Pretas) - Brancas Vencem"


def test_terminal_game_cannot_be_surrendered_again():
    state = _live_state()
    state.execute_action({"type": "surrender"})
    after_first = (state.to_rwen(), state.winner, len(state.move_log))

    with pytest.raises(ValueError, match="illegal action for terminal position"):
        state.execute_action({"type": "surrender"})

    assert (state.to_rwen(), state.winner, len(state.move_log)) == after_first
