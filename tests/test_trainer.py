import random

import pytest

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome
from tools.analytics.trainer import executar_acao_treino, preencher_draft_aleatorio
from tools.balance.auto_pricer import obter_partidas_validas


def test_invalid_spell_does_not_get_silently_accepted():
    gs = GameState()
    gs.board[0][0] = criar_peca_por_nome("Sentry", "brancas")

    with pytest.raises(ValueError, match=r"Unknown spell: unknown"):
        executar_acao_treino(
            gs,
            {
                "type": "spell",
                "start": (0, 0),
                "end": (0, 0),
                "spell_name": "unknown",
            },
        )


def test_auto_pricer_ignores_invalid_matches():
    stats = {
        "matches": [
            {"valid": True, "result": 1.0},
            {"valid": False, "result": 0.5, "invalid_action": "Unknown spell: unknown"},
            {"result": 0.0},
        ]
    }

    valid = obter_partidas_validas(stats)

    assert len(valid) == 2
    assert all(match.get("valid", True) for match in valid)


def test_draft_rng_does_not_touch_global_random_state():
    random.seed(12345)
    before = random.getstate()

    gs = GameState()
    preencher_draft_aleatorio(gs, "brancas", [6, 7], 200, random.Random(42))

    after = random.getstate()
    assert after == before
