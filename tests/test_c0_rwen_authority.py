from engine.game_state import GameState


def test_gamestate_rwen_is_defined_on_the_authoritative_class():
    method = GameState.to_rwen
    assert method.__module__ == "engine.game_state"
    assert callable(method)


def test_rwen_shape_remains_available_without_import_patch():
    state = GameState()
    encoded = state.to_rwen()
    assert encoded.endswith(" W 0")
    assert encoded.count("/") == 7
