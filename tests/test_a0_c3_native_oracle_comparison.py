from __future__ import annotations

from tools.analytics.legal_action_oracle import legal_actions
from tests.test_cross_backend_movegen import cpp_actions, make_cases


def oracle_action_text(action: tuple) -> str:
    action_type, (sr, sc), (er, ec), spell_name, spawn_name = action
    origin = f"{chr(ord('A') + sc)}{8 - sr}"
    target = f"{chr(ord('A') + ec)}{8 - er}"
    if action_type == "SPAWN":
        return f"SPAWN {spawn_name} {origin} {target}"
    if action_type == "SPELL":
        return f"SPELL {spell_name} {origin} {target}"
    return f"{action_type} {origin} {target}"


def test_independent_oracle_matches_native_cpp_move_generation():
    cases = make_cases()
    cpp_cases = cpp_actions([state.to_rwen() for _, state in cases])

    for (label, state), actual in zip(cases, cpp_cases):
        expected = {oracle_action_text(action) for action in legal_actions(state)}
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        assert not missing and not extra, (
            f"{label}: independent oracle/native mismatch\n"
            f"Missing in C++ ({len(missing)}): {missing}\n"
            f"Extra in C++ ({len(extra)}): {extra}"
        )
