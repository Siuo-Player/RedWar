from __future__ import annotations

from tests.test_a0_c3_native_oracle_randomized import _make_state
from tests.test_a0_c3_native_oracle_comparison import oracle_action_text
from tests.test_cross_backend_movegen import cpp_actions
from tools.analytics.legal_action_oracle import legal_actions


def _with_effect(state, effect_type: str | None, row: int, col: int):
    cloned = state.fast_clone()
    cloned.tile_effects[row][col] = None if effect_type is None else {
        "team": "brancas",
        "type": effect_type,
        "timer": 3,
    }
    return cloned


def _oracle_set(state):
    return {oracle_action_text(action) for action in legal_actions(state)}


def test_fire_effect_is_legality_invariant_for_randomized_states():
    # Fire is an environmental status effect, not an occupancy/geometry blocker.
    # Compare no-effect, fire and alternate fire ownership on the same states.
    seeds = list(range(32))
    variants = []
    expected = []

    for seed in seeds:
        base = _make_state(seed)
        row = (seed * 7) % 8
        col = (seed * 11 + 3) % 8
        base.tile_effects[row][col] = None
        variants.extend([
            base,
            _with_effect(base, "fire", row, col),
        ])
        expected.append(_oracle_set(base))

    native = cpp_actions([state.to_rwen() for state in variants])

    for index, seed in enumerate(seeds):
        base_native = native[index * 2]
        fire_native = native[index * 2 + 1]
        assert base_native == fire_native, (
            f"seed={seed}: native legal actions changed after adding fire effect\n"
            f"Base={sorted(base_native)}\nFire={sorted(fire_native)}"
        )
        assert expected[index] == base_native, (
            f"seed={seed}: oracle/native mismatch in fire metamorphic fixture"
        )
