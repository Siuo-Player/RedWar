"""Semantic stateful sequence helpers for RedWar differential testing.

This module only describes and records command sequences. It does not implement
alternative game rules; the existing Python/C++ differential machinery remains
the oracle for transition results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Iterable


COMMANDS = (
    "request_legal_actions",
    "serialize_roundtrip",
    "make_unmake",
)


@dataclass
class SequenceState:
    seed: int
    step: int = 0
    commands: list[str] = field(default_factory=list)

    def record(self, command: str) -> None:
        if command not in COMMANDS:
            raise ValueError(f"unknown semantic command: {command}")
        self.commands.append(command)
        self.step += 1


def generate_sequence(seed: int, length: int = 32) -> list[str]:
    """Generate a deterministic semantic sequence from a fixed seed."""
    if length < 0:
        raise ValueError("length must be non-negative")
    rng = random.Random(seed)
    state = SequenceState(seed=seed)
    for _ in range(length):
        state.record(rng.choice(COMMANDS))
    return state.commands


def first_divergence(
    expected: Iterable[object],
    actual: Iterable[object],
) -> int | None:
    """Return the first differing zero-based index, or None when equal."""
    for index, (left, right) in enumerate(zip(expected, actual)):
        if left != right:
            return index
    expected_list = list(expected)
    actual_list = list(actual)
    if len(expected_list) != len(actual_list):
        return min(len(expected_list), len(actual_list))
    return None
