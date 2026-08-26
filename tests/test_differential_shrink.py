from tools.analytics.differential_shrink import first_divergence, shrink_failing_prefix


def test_first_divergence_reports_first_value_mismatch():
    assert first_divergence(["a", "b", "c"], ["a", "x", "c"]) == 1


def test_first_divergence_reports_length_mismatch():
    assert first_divergence(["a", "b"], ["a"]) == 1
    assert first_divergence(["a"], ["a", "b"]) == 1


def test_first_divergence_returns_none_for_equal_sequences():
    assert first_divergence([1, 2, 3], [1, 2, 3]) is None


def test_shrink_failing_prefix_finds_shortest_reproducing_prefix():
    sequence = list(range(10))

    def fails(prefix):
        return len(prefix) >= 6

    assert shrink_failing_prefix(sequence, fails) == list(range(6))


def test_shrink_failing_prefix_does_not_mutate_input():
    sequence = ["a", "b", "c", "d"]
    original = list(sequence)

    assert shrink_failing_prefix(sequence, lambda prefix: len(prefix) >= 3) == ["a", "b", "c"]
    assert sequence == original


def test_shrink_failing_prefix_rejects_non_failing_full_sequence():
    try:
        shrink_failing_prefix([1, 2, 3], lambda _prefix: False)
    except ValueError as exc:
        assert "does not reproduce" in str(exc)
    else:
        raise AssertionError("expected ValueError")
