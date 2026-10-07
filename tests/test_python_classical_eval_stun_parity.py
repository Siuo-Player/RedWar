from ai.evaluator import avaliador_mestre
from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome


def _bone_lord_state(*, stunned: bool) -> GameState:
    state = GameState()
    piece = criar_peca_por_nome("BoneLord", "brancas")
    if stunned:
        piece.stun_timer = 1
    state.board[7][0] = piece
    state.turns_without_capture = 0
    return state


def test_python_evaluator_matches_classical_stun_fixture():
    # Shared expected fixture with ai/cpp_engine/SmokeTest.cpp:
    # BoneLord cost=86, PST(7,0)=40.
    unstunned = avaliador_mestre(_bone_lord_state(stunned=False))
    stunned = avaliador_mestre(_bone_lord_state(stunned=True))

    assert unstunned == 126
    assert stunned == 23
