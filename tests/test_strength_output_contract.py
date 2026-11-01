from pathlib import Path

from tools.analytics.strength_rating import Rating, compare


ROOT = Path(__file__).resolve().parents[1]
ARENA = ROOT / "tools" / "analytics" / "arena_tournament.py"


def test_strength_estimate_exposes_proxy_interval_type():
    estimate = compare(Rating(), Rating())
    assert estimate.interval_type == "engineering_uncertainty_proxy_v1"


def test_arena_does_not_label_uncertainty_as_confidence_interval():
    text = ARENA.read_text(encoding="utf-8")
    assert "rating_delta_ci95_half_width" not in text
    assert "IC95" not in text
    assert "rating_delta_uncertainty_proxy_half_width" in text
    assert "rating_delta_uncertainty_type" in text
