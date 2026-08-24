from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.nnue.features import (
    COOLDOWN_FEATURES,
    EFFECT_FEATURES,
    FEATURE_COUNT,
    LIFESPAN_FEATURES,
    MAX_HEROES,
    PIECE_FEATURES,
    STUN_FEATURES,
    TWC_FEATURES,
    load_hero_ids,
)
from tools.nnue.io import write_model

ACCUMULATOR = 128
HIDDEN = 32
ACC_SCALE = 64
HIDDEN_SCALE = 64
OUTPUT_SCALE = 1


def _feature_weight(weights1: list[int], feature: int, accumulator_index: int, value: int) -> None:
    base = feature * ACCUMULATOR
    weights1[base + accumulator_index] = value


def build_bootstrap_model(config_path: str | Path = "engine/heroes_config.json") -> dict[str, object]:
    hero_ids = load_hero_ids(config_path)
    costs = {
        name: int(data["cost"])
        for name, data in json.loads(Path(config_path).read_text(encoding="utf-8")).items()
    }

    bias1 = [0] * ACCUMULATOR
    weights1 = [0] * (FEATURE_COUNT * ACCUMULATOR)
    bias2 = [0] * HIDDEN
    weights2 = [0] * (ACCUMULATOR * 2 * HIDDEN)
    bias3 = 0
    weights3 = [0] * HIDDEN

    # Deterministic compatibility network, deliberately weak. Its purpose is
    # to exercise every feature family and validate the C++ inference path.
    for hero, hero_id in hero_ids.items():
        cost = costs.get(hero, 50)
        for square in range(64):
            for relative_color in (0, 1):
                feature = (square * MAX_HEROES + hero_id) * 2 + relative_color
                _feature_weight(weights1, feature, relative_color, cost * ACC_SCALE)

    for square in range(64):
        for color in (0, 1):
            for bucket in range(6):
                feature = PIECE_FEATURES + (square * 2 + color) * 6 + bucket
                _feature_weight(weights1, feature, 2, bucket * ACC_SCALE)

                feature = PIECE_FEATURES + STUN_FEATURES + (square * 2 + color) * 6 + bucket
                _feature_weight(weights1, feature, 3, bucket * ACC_SCALE)

            for bucket in range(5):
                feature = (
                    PIECE_FEATURES
                    + STUN_FEATURES
                    + LIFESPAN_FEATURES
                    + (square * 2 + color) * 5
                    + bucket
                )
                _feature_weight(weights1, feature, 4, bucket * ACC_SCALE)

    state_start = PIECE_FEATURES + STUN_FEATURES + LIFESPAN_FEATURES + COOLDOWN_FEATURES
    state_end = state_start + EFFECT_FEATURES + TWC_FEATURES + 2
    for feature in range(state_start, state_end):
        _feature_weight(weights1, feature, 5, ACC_SCALE)

    # C++ stores weights as [input][hidden], not PyTorch's [hidden][input].
    for input_index, hidden_index, sign in (
        (0, 0, +1),
        (1, 1, -1),
        (2, 2, +1),
        (3, 3, +1),
        (4, 4, +1),
        (5, 5, +1),
        (ACCUMULATOR + 0, 8, +1),
        (ACCUMULATOR + 1, 9, -1),
        (ACCUMULATOR + 2, 10, +1),
        (ACCUMULATOR + 3, 11, +1),
        (ACCUMULATOR + 4, 12, +1),
        (ACCUMULATOR + 5, 13, +1),
    ):
        weights2[input_index * HIDDEN + hidden_index] = sign * HIDDEN_SCALE

    weights3[0] = +1
    weights3[1] = -1
    weights3[2] = +1
    weights3[3] = +1
    weights3[4] = +1
    weights3[5] = +1
    weights3[8] = -1
    weights3[9] = +1

    return {
        "features": FEATURE_COUNT,
        "accumulator": ACCUMULATOR,
        "hidden": HIDDEN,
        "accumulator_scale": ACC_SCALE,
        "hidden_scale": HIDDEN_SCALE,
        "output_scale": OUTPUT_SCALE,
        "bias1": bias1,
        "weights1": weights1,
        "bias2": bias2,
        "weights2": weights2,
        "bias3": bias3,
        "weights3": weights3,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a deterministic compatibility NNUE model")
    parser.add_argument("--output", default="data/nnue/ares-bootstrap.nnue")
    args = parser.parse_args()
    model = build_bootstrap_model()
    write_model(args.output, **model)
    print(f"NNUE bootstrap model written to {args.output}")


if __name__ == "__main__":
    main()
