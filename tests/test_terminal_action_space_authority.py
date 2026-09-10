from engine.game_state import GameState
from engine.legal_actions import legal_actions
from engine.pieces import criar_peca_por_nome


def test_no_legal_action_termination_delegates_to_canonical_action_space(monkeypatch):
    gs = GameState()
    gs.board[4][4] = criar_peca_por_nome("Ranger", "brancas")
    gs.board[4][6] = criar_peca_por_nome("Bone", "pretas")

    # The position has ordinary Ranger movement options. Force the canonical
    # action-space to report none so this test specifically proves that
    # check_game_over() consumes that authority instead of re-scanning pieces.
    assert legal_actions(gs)
    monkeypatch.setattr("engine.legal_actions.legal_actions", lambda _gs: ())

    gs.check_game_over()
    assert gs.game_over is True
    assert "Oponente Bloqueado" in gs.winner


def test_valid_no_action_state_still_terminates():
    gs = GameState()
    gs.board[0][0] = criar_peca_por_nome("Obelisk", "brancas")
    gs.board[7][7] = criar_peca_por_nome("Obelisk", "pretas")
    for col in range(1, 8):
        gs.board[0][col] = criar_peca_por_nome("StoneWall", "brancas")
    assert legal_actions(gs) == ()
    gs.check_game_over()
    assert gs.game_over is True
    assert "Oponente Bloqueado" in gs.winner
