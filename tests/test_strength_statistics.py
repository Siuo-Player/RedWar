import math
import random

import pytest

from tools.analytics.strength_statistics import (
    MAX_GAMES,
    PROMOTION_STAGES,
    PairedGame,
    STAGE_ALPHA,
    evaluate_promotion,
    fit_bradley_terry,
    paired_bootstrap_delta,
    validate_paired_games,
)


def _paired_games(outcomes: list[tuple[str, str]]) -> list[PairedGame]:
    games: list[PairedGame] = []
    for pair_index, (first, second) in enumerate(outcomes):
        pair_id = f"pair-{pair_index}"
        games.extend(
            [
                PairedGame(pair_id, 1000 + pair_index, "white", first, pair_index * 2),
                PairedGame(pair_id, 1000 + pair_index, "black", second, pair_index * 2 + 1),
            ]
        )
    return games


def _sample_binary(true_delta_elo: float, pairs: int, seed: int) -> list[PairedGame]:
    rng = random.Random(seed)
    p = 1.0 / (1.0 + 10.0 ** (-true_delta_elo / 400.0))
    games: list[PairedGame] = []
    for pair_index in range(pairs):
        pair_id = f"synthetic-{pair_index}"
        for offset, colour in enumerate(("white", "black")):
            outcome = "challenger" if rng.random() < p else "baseline"
            games.append(
                PairedGame(
                    pair_id,
                    20_000 + pair_index,
                    colour,
                    outcome,
                    pair_index * 2 + offset,
                )
            )
    return games


def test_validate_pairs_requires_colour_inversion_and_same_opening():
    valid = _paired_games([("challenger", "baseline")])
    assert len(validate_paired_games(valid)) == 1

    same_colour = [
        PairedGame("p", 1, "white", "challenger"),
        PairedGame("p", 1, "white", "baseline"),
    ]
    with pytest.raises(ValueError, match="invert challenger colour"):
        validate_paired_games(same_colour)

    different_opening = [
        PairedGame("p", 1, "white", "challenger"),
        PairedGame("p", 2, "black", "baseline"),
    ]
    with pytest.raises(ValueError, match="same opening seed"):
        validate_paired_games(different_opening)


def test_validate_pairs_rejects_opening_reuse_across_pairs():
    reused = _paired_games([("challenger", "baseline"), ("challenger", "baseline")])
    reused[2] = PairedGame(reused[2].pair_id, reused[0].opening_seed, reused[2].challenger_colour, reused[2].outcome, reused[2].game_index)
    reused[3] = PairedGame(reused[3].pair_id, reused[0].opening_seed, reused[3].challenger_colour, reused[3].outcome, reused[3].game_index)
    with pytest.raises(ValueError, match="reused by pairs"):
        validate_paired_games(reused)


def test_bradley_terry_is_binary_and_has_no_draw_state():
    estimate = fit_bradley_terry(
        _paired_games(
            [("challenger", "baseline")] * 12
            + [("baseline", "challenger")] * 4
        )
    )
    assert estimate.games == 32
    assert estimate.challenger_wins == 16
    assert estimate.baseline_wins == 16
    assert estimate.challenger_win_probability == 0.5
    assert estimate.delta_elo == 0.0

    with pytest.raises(ValueError, match="unknown binary outcome"):
        fit_bradley_terry(["draw"])


def test_bradley_terry_recovers_known_positive_strength_signal():
    games = _sample_binary(true_delta_elo=100.0, pairs=1200, seed=7)
    estimate = fit_bradley_terry(games)
    assert 60.0 < estimate.delta_elo < 140.0
    assert 0.5 < estimate.challenger_win_probability < 1.0


def test_all_win_sample_reports_unbounded_mle():
    estimate = fit_bradley_terry(_paired_games([("challenger", "challenger")] * 4))
    assert math.isinf(estimate.delta_elo)
    assert estimate.delta_elo > 0


def test_pair_bootstrap_resamples_pairs_not_individual_games():
    games = _paired_games(
        [("challenger", "baseline")] * 4
        + [("baseline", "challenger")] * 4
    )
    interval = paired_bootstrap_delta(games, replicates=40, seed=11)
    assert interval.replicates == 40
    assert interval.cluster_count == 8
    assert interval.lower <= interval.median <= interval.upper


def test_pair_bootstrap_requires_complete_pairs():
    incomplete = [PairedGame("p", 1, "white", "challenger")]
    with pytest.raises(ValueError, match="exactly two games"):
        paired_bootstrap_delta(incomplete, replicates=10)


def test_promotion_stages_and_hard_limit_are_fixed():
    assert PROMOTION_STAGES == (96, 192, 320, 512)
    assert MAX_GAMES == 512


def test_promotion_confidence_is_one_sided_bonferroni_adjusted():
    games = _paired_games([("challenger", "baseline")] * 48)
    decision = evaluate_promotion(games, bootstrap_replicates=100, bootstrap_seed=3)
    assert decision.confidence == pytest.approx(1.0 - STAGE_ALPHA)
    two_sided_for_same_lower_tail = 1.0 - 2.0 * STAGE_ALPHA
    interval = paired_bootstrap_delta(
        games,
        replicates=100,
        confidence=two_sided_for_same_lower_tail,
        seed=3,
    )
    assert decision.lower_bound_elo == pytest.approx(interval.lower)


def test_promotion_preserves_baseline_when_evidence_is_inconclusive():
    games = _paired_games([("challenger", "baseline")] * 48)
    decision = evaluate_promotion(games, bootstrap_replicates=100, bootstrap_seed=3)
    assert decision.decision == "continue"
    assert decision.games == 96
    assert decision.stage_games == 96
    assert decision.lower_bound_elo <= 0.0


def test_promotion_accepts_when_lower_bound_is_positive():
    games = _sample_binary(true_delta_elo=300.0, pairs=48, seed=19)
    decision = evaluate_promotion(games, bootstrap_replicates=400, bootstrap_seed=4)
    assert decision.decision == "accept"
    assert decision.games == 96
    assert decision.lower_bound_elo is not None
    assert decision.lower_bound_elo > 0.0


def test_promotion_rejects_at_max_without_proof():
    games = _paired_games([("challenger", "baseline")] * 256)
    decision = evaluate_promotion(games, bootstrap_replicates=100, bootstrap_seed=5)
    assert decision.decision == "reject"
    assert decision.games == MAX_GAMES
    assert decision.stage_games == MAX_GAMES
    assert decision.lower_bound_elo is not None
    assert decision.lower_bound_elo <= 0.0


def test_promotion_does_not_look_between_stages():
    games = _paired_games([("challenger", "baseline")] * 49)
    decision = evaluate_promotion(games, bootstrap_replicates=50, bootstrap_seed=6)
    assert decision.decision == "continue"
    assert decision.games == 98
    assert decision.stage_games is None
