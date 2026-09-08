from __future__ import annotations

from tools.nnue.train import _grouped_validation_split


def test_grouped_validation_split_is_deterministic_and_has_no_exact_overlap():
    rows = [
        {"rwen": "state-a", "score": 10},
        {"rwen": "state-a", "score": 10},
        {"rwen": "state-b", "score": 5},
        {"rwen": "state-c", "score": -2},
        {"rwen": "state-d", "score": 9},
        {"rwen": "state-e", "score": 1},
        {"rwen": "state-f", "score": 0},
        {"rwen": "state-g", "score": -1},
        {"rwen": "state-h", "score": 3},
        {"rwen": "state-i", "score": 7},
    ]

    first_train, first_valid = _grouped_validation_split(rows, 0.2)
    second_train, second_valid = _grouped_validation_split(rows, 0.2)

    assert (first_train, first_valid) == (second_train, second_valid)
    assert first_train
    assert first_valid

    train_keys = {rows[index]["rwen"] for index in first_train}
    valid_keys = {rows[index]["rwen"] for index in first_valid}
    assert train_keys.isdisjoint(valid_keys)


def test_grouped_validation_split_rejects_invalid_fraction():
    rows = [{"rwen": "a", "score": 0}, {"rwen": "b", "score": 1}]

    try:
        _grouped_validation_split(rows, 0.0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for zero validation fraction")
