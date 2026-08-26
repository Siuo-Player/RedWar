from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

T = TypeVar("T")


def first_divergence(expected: Sequence[T], actual: Sequence[T]) -> int | None:
    """Return the first differing index, or the first length mismatch."""
    limit = min(len(expected), len(actual))
    for index in range(limit):
        if expected[index] != actual[index]:
            return index
    if len(expected) != len(actual):
        return limit
    return None


def shrink_failing_prefix(
    sequence: Sequence[T],
    reproduces_failure: Callable[[Sequence[T]], bool],
) -> list[T]:
    """Return the shortest prefix that still reproduces a failure.

    Arbitrary action deletion can make later game actions illegal, so this helper
    only removes a prefix boundary and preserves the original action order.
    The predicate must be monotonic over prefixes.
    """
    items = list(sequence)
    if not items or not reproduces_failure(items):
        raise ValueError("full sequence does not reproduce the failure")

    lo = 1
    hi = len(items)
    while lo < hi:
        mid = (lo + hi) // 2
        if reproduces_failure(items[:mid]):
            hi = mid
        else:
            lo = mid + 1
    return items[:lo]
