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
