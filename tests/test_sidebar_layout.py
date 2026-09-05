import pytest

from tools.replay.interaction import _panel_geometry
from ui.sidebar_layout import sidebar_layout_for_viewport


def test_wide_viewport_uses_available_right_side_width():
    layout = sidebar_layout_for_viewport(
        viewport_width=1920,
        board_left=40,
        board_width=960,
    )

    assert layout.mode == "wide"
    assert layout.panel_x == 1030
    assert layout.panel_width == 870
    assert layout.right_margin == 20


def test_medium_viewport_uses_medium_mode_and_available_width():
    layout = sidebar_layout_for_viewport(
        viewport_width=1280,
        board_left=40,
        board_width=760,
    )

    assert layout.mode == "medium"
    assert layout.panel_x == 830
    assert layout.panel_width == 430


def test_narrow_viewport_contracts_to_minimum_width():
    layout = sidebar_layout_for_viewport(
        viewport_width=900,
        board_left=20,
        board_width=700,
        minimum_width=240,
    )

    assert layout.mode == "narrow"
    assert layout.panel_x == 750
    assert layout.panel_width == 240


def test_custom_margins_are_deterministic():
    layout = sidebar_layout_for_viewport(
        viewport_width=1400,
        board_left=10,
        board_width=800,
        right_margin=16,
        board_gap=24,
        minimum_width=220,
    )

    assert layout.mode == "medium"
    assert layout.panel_x == 834
    assert layout.panel_width == 550
    assert layout.right_margin == 16


@pytest.mark.parametrize(
    "kwargs",
    [
        {"viewport_width": 0, "board_left": 0, "board_width": 1},
        {"viewport_width": 1000, "board_left": -1, "board_width": 1},
        {"viewport_width": 1000, "board_left": 0, "board_width": 0},
        {"viewport_width": 1000, "board_left": 0, "board_width": 1, "right_margin": -1},
        {"viewport_width": 1000, "board_left": 0, "board_width": 1, "board_gap": -1},
        {"viewport_width": 1000, "board_left": 0, "board_width": 1, "minimum_width": 0},
    ],
)
def test_invalid_geometry_is_rejected(kwargs):
    with pytest.raises(ValueError):
        sidebar_layout_for_viewport(**kwargs)


def test_battle_panel_geometry_uses_shared_layout_contract():
    class FakeSurface:
        def get_size(self):
            return (1280, 720)

    class FakeController:
        ecra = FakeSurface()

        @staticmethod
        def get_ui_metrics():
            return 40, 40, 80

    expected = sidebar_layout_for_viewport(
        viewport_width=1280,
        board_left=40,
        board_width=8 * 80,
    )

    assert _panel_geometry(FakeController()) == (expected.panel_x, expected.panel_width, 40)
