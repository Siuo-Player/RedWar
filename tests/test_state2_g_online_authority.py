import pytest

from engine.pieces import Bone
from online.server.authority import AuthoritativeSession


def test_server_session_executes_only_for_active_player():
    session = AuthoritativeSession.new()
    session.state.board[6][0] = Bone("brancas")

    with pytest.raises(ValueError, match="non-active player"):
        session.apply_text_action("pretas", "MOVE A2 A3")

    before = session.state.to_rwen()
    after = session.apply_text_action("brancas", "MOVE A2 A3")

    assert after == session.state.to_rwen()
    assert after != before
    assert session.state.board[5][0] is not None
    assert session.state.board[6][0] is None


def test_server_session_accepts_canonical_action_and_serializes_state():
    session = AuthoritativeSession.new()
    session.state.board[6][0] = Bone("brancas")

    before = session.state_payload()
    assert before["white_to_move"] is True
    assert before["board"][6][0]["team"] == "brancas"
    assert before["board"][6][0]["name"] == "Bone"

    result = session.apply_action(
        "brancas",
        {"type": "move", "start": [6, 0], "end": [5, 0]},
    )

    assert result == session.state.to_rwen()
    after = session.state_payload()
    assert after["white_to_move"] is False
    assert after["board"][6][0] is None
    assert after["board"][5][0]["team"] == "brancas"


def test_server_session_rejects_action_from_wrong_piece_without_mutation():
    session = AuthoritativeSession.new()
    session.state.board[6][0] = Bone("brancas")
    before = session.state.to_rwen()

    with pytest.raises(ValueError, match="does not belong"):
        session.apply_action(
            "brancas",
            {"type": "move", "start": [6, 1], "end": [5, 1]},
        )

    assert session.state.to_rwen() == before
