from __future__ import annotations

import argparse
from pathlib import Path

from tools.nnue.features import FEATURE_COUNT, MAX_HEROES, load_hero_ids
from tools.nnue.io import write_model

ACCUMULATOR = 128
HIDDEN = 32
ACC_SCALE = 64
HIDDEN_SCALE = 64
OUTPUT_SCALE = 1


def build_bootstrap_model(config_path: str | Path = "engine/heroes_config.json") -> dict[str, object]:
    hero_ids = load_hero_ids(config_path)
    costs = {name: int(data["cost"]) for name, data in __import__("json").loads(Path(config_path).read_text()).items()}

    bias1 = [0] * ACCUMULATOR
    weights1 = [0] * (FEATURE_COUNT * ACCUMULATOR)
    bias2 = [0] * HIDDEN
    weights2 = [0] * (ACCUMULATOR * 2 * HIDDEN)
    bias3 = 0
    weights3 = [0] * HIDDEN

    # Four first hidden signals:
    #   perspective 0: own material, enemy material
    #   perspective 1: own material, enemy material
    # This creates a deterministic, material-only NNUE model used by tests.
    for hero, hero_id in hero_ids.items():
        cost = costs.get(hero, 50)
        for square in range(64):
            for relative_color in (0, 1):
                feature = (square * MAX_HEROES + hero_id) * 2 + relative_color
                base = feature * ACCUMULATOR
                if relative_color == 0:
                    weights1[base + 0] = cost * ACC_SCALE
                else:
                    weights1[base + 1] = cost * ACC_SCALE

    # C++ layout concatenates the two 128-wide perspective accumulators.
    for input_index, hidden_index, sign in (
        (0, 0, +1), (1, 1, +1),
        (ACCUMULATOR + 0, 2, +1), (ACCUMULATOR + 1, 3, +1),
    ):
        weights2[input_index * HIDDEN + hidden_index] = sign * HIDDEN_SCALE

    weights3[0] = +1
    weights3[1] = -1
    weights3[2] = -1
    weights3[3] = +1

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
