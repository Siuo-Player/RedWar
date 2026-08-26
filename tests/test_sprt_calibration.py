import pytest

from tools.analytics.sprt_calibration import calibrate_sprt_baseline


def test_calibration_reports_empirical_draw_rate_and_decisive_rate():
    result = calibrate_sprt_baseline([
        "win",
        "loss",
        "draw",
        "win",
        "draw",
    ])

    assert result["games"] == 5
    assert result["wins"] == 2
    assert result["losses"] == 1
    assert result["draws"] == 2
    assert result["draw_rate"] == pytest.approx(0.4)
    assert result["decisive_games"] == 3
    assert result["decisive_win_rate"] == pytest.approx(2 / 3)
    assert result["calibration_status"] == "descriptive_only"
    assert result["implied_elo_delta"] > 0


def test_calibration_is_zero_at_decisive_balance():
    result = calibrate_sprt_baseline(["win", "loss"])

    assert result["draw_rate"] == 0.0
    assert result["decisive_win_rate"] == 0.5
    assert result["implied_elo_delta"] == pytest.approx(0.0)


def test_calibration_handles_all_draws_without_inventing_strength():
    result = calibrate_sprt_baseline(["draw", "draw", "draw"])

    assert result["draw_rate"] == 1.0
    assert result["decisive_games"] == 0
    assert result["decisive_win_rate"] == 0.5
    assert result["implied_elo_delta"] == 0.0
    assert result["calibration_status"] == "insufficient_decisive_games"


def test_calibration_rejects_empty_or_invalid_input():
    with pytest.raises(ValueError, match="at least one"):
        calibrate_sprt_baseline([])
    with pytest.raises(ValueError, match="win, loss or draw"):
        calibrate_sprt_baseline(["invalid"])
