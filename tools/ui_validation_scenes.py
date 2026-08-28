from tools.ui_validation import SCENES, scene_path


def test_scene_registry_has_expected_validation_cases(tmp_path):
    expected = {
        "battle_idle",
        "selected_hero_hovered_cell",
        "ambiguous_action_choice",
        "illegal_destination",
        "frostmage_nevada",
        "narrow_window",
    }
    assert set(SCENES) == expected
    assert scene_path(tmp_path, "battle_idle").name == "battle_idle.png"


def test_unknown_scene_is_rejected(tmp_path):
    try:
        scene_path(tmp_path, "unknown")
    except ValueError as exc:
        assert "unknown validation scene" in str(exc)
    else:
        raise AssertionError("unknown scene must be rejected")
