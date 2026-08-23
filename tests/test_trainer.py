import pytest

from engine.game_state import GameState
from tools.analytics.trainer import executar_acao_treino
from tools.balance.auto_pricer import obter_partidas_validas


def test_invalid_spell_does_not_get_silently_accepted():
    gs = GameState()
    # Make the source-square validation succeed so the test reaches the
    # spell-name validation that it is actually intended to cover.
    piece = next(
        (candidate for row in gs.board for candidate in row if candidate is not None),
        None,
    )
    assert piece is not None
    start = next(
        (position for r, row in enumerate(gs.board) for c, candidate in enumerate(row)
         if candidate is piece for position in [(r, c)]),
        None,
    )
    assert start is not None

    with pytest.raises(ValueError, match=r"Unknown spell: unknown"):
        executar_acao_treino(
            gs,
            {
                "type": "spell",
                "start": start,
                "end": start,
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
