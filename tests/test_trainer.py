import pytest

from engine.game_state import GameState
from engine.pieces import HERO_DEFS, Piece
from tools.analytics.trainer import executar_acao_treino
from tools.balance.auto_pricer import obter_partidas_validas


def test_invalid_spell_does_not_get_silently_accepted():
    gs = GameState()
    data = HERO_DEFS["Sentry"]
    gs.board[0][0] = Piece("brancas", "Sentry", data["cost"], data["acronym"])

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
