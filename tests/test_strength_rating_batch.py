from tools.analytics.strength_rating_batch import MatchResult, estimate_batch


def test_batch_estimate_is_independent_of_game_order():
    results = [
        MatchResult("Ares", "Base", "win"),
        MatchResult("Ares", "Base", "loss"),
        MatchResult("Base", "Ares", "draw"),
        MatchResult("Ares", "Base", "win"),
    ]
    forward = estimate_batch(results, left="Ares", right="Base")
    reverse = estimate_batch(reversed(results), left="Ares", right="Base")
    assert forward == reverse
    assert (forward.wins, forward.draws, forward.losses) == (2, 1, 1)
    assert forward.games == 4
    assert forward.elo_delta > 0


def test_batch_estimate_handles_colour_reversal():
    result = estimate_batch(
        [
            MatchResult("Ares", "Base", "win"),
            MatchResult("Base", "Ares", "win"),
        ],
        left="Ares",
        right="Base",
    )
    assert result.wins == 1
    assert result.losses == 1
    assert result.draws == 0
    assert result.score_rate == 0.5
    assert result.elo_delta == 0.0


def test_batch_estimate_rejects_empty_sample():
    try:
        estimate_batch([], left="Ares", right="Base")
    except ValueError as exc:
        assert "at least one" in str(exc)
    else:
        raise AssertionError("empty matchup must be rejected")
