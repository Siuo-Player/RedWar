from __future__ import annotations

import argparse
import json
import random
import subprocess
from pathlib import Path

from tools.nnue.features import load_hero_ids, parse_rwen


def _rwen(rows: tuple[tuple[str, ...], ...], turn: str, twc: int) -> str:
    if len(rows) != 8 or any(len(row) != 8 for row in rows):
        raise ValueError(
            f"teacher position must contain exactly 8x8 cells: rows={len(rows)} "
            f"widths={[len(row) for row in rows]}"
        )
    return "/".join(",".join(row) for row in rows) + f" {turn} {twc}"


def _split_rwen(rwen: str) -> tuple[list[list[str]], str, int]:
    parts = rwen.split()
    if len(parts) != 3:
        raise ValueError(f"teacher position must have board, turn and twc: {rwen!r}")
    board, turn, twc = parts
    rows = [row.split(",") for row in board.split("/")]
    if len(rows) != 8 or any(len(row) != 8 for row in rows):
        raise ValueError(
            f"teacher position must contain exactly 8x8 cells: rows={len(rows)} "
            f"widths={[len(row) for row in rows]}"
        )
    return rows, turn, int(twc)


def _join_rwen(rows: list[list[str]], turn: str, twc: int) -> str:
    return _rwen(tuple(tuple(row) for row in rows), turn, twc)


# Keep the three original seed positions as explicit canonical RWEN strings.
# Defining them this way avoids accidental tuple-shape mistakes during module import.
BASE_POSITIONS = [
    "B_Sentry_0_N_0,.,.,.,B_Ranger_0_N_0,.,.,./.,B_Phantom_0_N_0,.,.,.,B_FrostMage_0_N_0,.,./.,.,.,B_Templar_0_N_0,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,W_Templar_0_N_0,.,.,W_Phantom_0_N_0,.,.,./.,W_FrostMage_0_N_0,.,.,.,W_Ranger_0_N_0,.,./W_Sentry_0_N_0,.,.,.,W_Inquisitor_0_N_0,.,.,. W 0",
    "W_FrostMage_1_N_0,B_Bone_2_N_0,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,W_BoneLord_0_N_0,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,B_Phantom_0_N_0,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. B 17",
    "W_Sentry_0_N_0,.,.,.,B_FrostMage_0_N_0,.,.,./.,W_Templar_2_N_0,.,.,.,.,.,.,./.,.,B_Phantom_0_N_0,.,.,.,.,.,./.,.,.,.,W_Lich_0_N_0,.,.,./.,.,.,.,.,B_BoneLord_0_N_0,.,./.,W_Ranger_0_N_0,.,.,.,.,.,.,./.,.,.,.,.,.,.,./B_Sentry_0_N_0,.,.,.,W_Inquisitor_0_N_0,.,.,. W 23",
]


def _spatial_families(base: str) -> list[tuple[str, int]]:
    """Create deterministic, parser-valid positional families from each seed.

    The generator deliberately avoids pretending that transformed boards are game
    trajectories. These are broad evaluator-training probes: occupancy is kept
    sparse, pieces are only moved to empty squares, and no new hero is invented.
    """
    rows, turn, twc = _split_rwen(base)
    occupied = [(r, c) for r in range(8) for c in range(8) if rows[r][c] != "."]
    empty = [(r, c) for r in range(8) for c in range(8) if rows[r][c] == "."]
    families = [(base, 0)]

    for family in range(1, 5):
        mutated = [row[:] for row in rows]
        moved = min(family, len(occupied), len(empty))
        for i in range(moved):
            source = occupied[(family * 2 + i * 3) % len(occupied)]
            target = empty[(family * 5 + i * 7) % len(empty)]
            token = mutated[source[0]][source[1]]
            mutated[source[0]][source[1]] = "."
            mutated[target[0]][target[1]] = token
        families.append((_join_rwen(mutated, turn, twc), family))
    return families


def _state_variants(rwen: str, mode: int) -> str:
    rows, turn, twc = _split_rwen(rwen)
    cells = [(r, c) for r in range(8) for c in range(8) if rows[r][c] != "."]
    if not cells:
        return rwen
    r, c = cells[mode % len(cells)]
    fields = rows[r][c].split("_")
    if mode % 3 == 0:
        fields[2] = str((int(fields[2]) + 1) % 6)
    elif mode % 3 == 1:
        fields[3] = str((mode + 1) % 6)
    else:
        fields[4] = str((mode + 1) % 5)
    rows[r][c] = "_".join(fields)
    return _join_rwen(rows, turn, twc)


def _effect_variant(rwen: str, effect_mode: int) -> str:
    rows, turn, twc = _split_rwen(rwen)
    empties = [(r, c) for r in range(8) for c in range(8) if rows[r][c] == "."]
    if not empties:
        return rwen
    r, c = empties[effect_mode % len(empties)]
    effect_type = ("fire", "ice", "other")[effect_mode % 3]
    effect_team = "W" if effect_mode % 2 == 0 else "B"
    timer = effect_mode % 4
    rows[r][c] = f".:{effect_team}_{effect_type}_{timer}"
    return _join_rwen(rows, turn, twc)


def build_positions() -> list[tuple[str, str]]:
    positions: list[tuple[str, str]] = []
    seen: set[str] = set()
    twcs = (0, 10, 20, 30, 40, 50)
    turns = ("W", "B")
    for base_index, base in enumerate(BASE_POSITIONS):
        # Validate every seed before applying transformations.
        _split_rwen(base)
        for family_rwen, family_index in _spatial_families(base):
            family_id = f"base{base_index}-family{family_index}"
            for turn in turns:
                for twc in twcs:
                    for state_mode in range(2):
                        candidate = _join_rwen(_split_rwen(family_rwen)[0], turn, twc)
                        candidate = _state_variants(candidate, family_index + state_mode)
                        for effect_mode in range(2):
                            final_candidate = candidate
                            if effect_mode:
                                final_candidate = _effect_variant(
                                    candidate, family_index + state_mode
                                )
                            if final_candidate not in seen:
                                seen.add(final_candidate)
                                positions.append((final_candidate, family_id))
    return positions


def classical_eval(engine: Path, rwen: str) -> int:
    proc = subprocess.run(
        [str(engine)],
        input=f"position rwen {rwen}\neval classical\nquit\n",
        text=True,
        capture_output=True,
        cwd=engine.parent,
        check=True,
    )
    for line in proc.stdout.splitlines():
        if line.startswith("info score classical "):
            return int(line.rsplit(" ", 1)[1])
    raise RuntimeError(f"engine did not return a classical score: {proc.stdout!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    engine = args.engine.resolve()
    hero_ids = load_hero_ids()
    positions = build_positions()
    if len(positions) < 300:
        raise RuntimeError(f"teacher corpus unexpectedly small: {len(positions)} rows")

    rng = random.Random(20260912)
    rng.shuffle(positions)
    rows = []
    for index, (rwen, group) in enumerate(positions, 1):
        try:
            parse_rwen(rwen, hero_ids)
        except ValueError as exc:
            raise ValueError(f"Invalid teacher RWEN at position {index}: {exc}") from exc
        rows.append(
            {
                "rwen": rwen,
                "score": classical_eval(engine, rwen),
                "source": "classical-v2",
                "group": group,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(f"teacher_rows={len(rows)}")
    print(f"teacher_groups={len({row['group'] for row in rows})}")
    print(f"teacher_output={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
