from engine.game_state import GameState


def test_gamestate_rwen_is_authoritative():
    assert GameState.to_rwen.__module__ == "engine.game_state"
    assert callable(GameState.to_rwen)


def test_empty_rwen_shape_is_stable():
    encoded = GameState().to_rwen()
    assert encoded.endswith(" W 0")
    assert encoded.count("/") == 7
