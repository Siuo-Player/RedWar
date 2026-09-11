import pytest

from tools.analytics.opening_book import PROMOTION_OPENING_SEEDS
from tools.analytics.promotion_arena import PROMOTION_STAGES, STAGE_OPENING_RANGES, opening_seeds_for_stage


def test_promotion_stage_schedule_is_cumulative_and_fresh():
    seen: set[int] = set()
    previous = 0
    expected_pairs = {96: 48, 192: 48, 320: 64, 512: 96}
    for stage in PROMOTION_STAGES:
        seeds = opening_seeds_for_stage(stage)
        assert len(seeds) == expected_pairs[stage]
        assert len(set(seeds)) == len(seeds)
        assert not seen.intersection(seeds)
        seen.update(seeds)
        assert stage - previous == 2 * len(seeds)
        previous = stage

    assert seen == set(PROMOTION_OPENING_SEEDS)
    assert len(seen) == 256


def test_promotion_schedule_ranges_match_declared_bank():
    assert STAGE_OPENING_RANGES == {
        96: (0, 48),
        192: (48, 96),
        320: (96, 160),
        512: (160, 256),
    }

    with pytest.raises(ValueError, match="stage"):
        opening_seeds_for_stage(128)
