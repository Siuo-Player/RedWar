from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from engine.setup import validate_complete_pre_match_setup
from tools.analytics.trainer import preencher_draft_aleatorio


def test_trainer_random_draft_uses_canonical_pre_match_validator():
    gs = GameState()
    preencher_draft_aleatorio(gs, "pretas", [0, 1], 200, __import__("random").Random(1))
    preencher_draft_aleatorio(gs, "brancas", [6, 7], 200, __import__("random").Random(2))
    costs = validate_complete_pre_match_setup(gs.board)
    assert costs["brancas"] <= 200
    assert costs["pretas"] <= 200


def test_pre_match_validator_rejects_non_draftable_runtime_piece():
    gs = GameState()
    gs.board[0][0] = criar_peca_por_nome("Ghoul", "pretas")
    try:
        validate_complete_pre_match_setup(gs.board)
    except ValueError as exc:
        assert "Non-draftable" in str(exc)
    else:
        raise AssertionError("non-draftable piece must be rejected by pre-match validator")
