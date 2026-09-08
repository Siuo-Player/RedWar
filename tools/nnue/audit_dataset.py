"""Audit an NNUE JSONL dataset for reproducibility and exact-position leakage risks."""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any


def load_rows(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or "rwen" not in row or "score" not in row:
            raise ValueError(f"line {lineno}: expected a JSON object with rwen and score")
        rows.append(row)
    if not rows:
        raise ValueError("dataset is empty")
    return rows


def grouped_split(rows: list[dict[str, Any]], fraction: float) -> tuple[set[int], set[int]]:
    if not 0.0 < fraction < 1.0:
        raise ValueError("fraction must be between 0 and 1")
    groups: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        key = str(row["rwen"]).strip()
        groups.setdefault(key, []).append(index)

    ranked = sorted(
        groups.items(),
        key=lambda item: hashlib.sha256(item[0].encode("utf-8")).hexdigest(),
    )
    target = max(1, min(len(rows) - 1, round(len(rows) * fraction)))
    valid: set[int] = set()
    for _key, indices in ranked:
        valid.update(indices)
        if len(valid) >= target:
            break
    train = set(range(len(rows))) - valid
    return train, valid


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a RedWar NNUE JSONL dataset")
    parser.add_argument("dataset")
    parser.add_argument("--validation-fraction", type=float, default=0.1)
    parser.add_argument("--fail-on-duplicate-ratio", type=float, default=None)
    args = parser.parse_args()

    if not 0.0 < args.validation_fraction < 1.0:
        parser.error("--validation-fraction must be between 0 and 1")

    rows = load_rows(args.dataset)
    keys = [str(row["rwen"]).strip() for row in rows]
    scores = [float(row["score"]) for row in rows]
    counts: dict[str, int] = {}
    labels: dict[str, set[float]] = {}
    for key, score in zip(keys, scores):
        counts[key] = counts.get(key, 0) + 1
        labels.setdefault(key, set()).add(score)

    duplicates = sum(count - 1 for count in counts.values() if count > 1)
    duplicate_ratio = duplicates / len(rows)
    conflicting_labels = sum(1 for values in labels.values() if len(values) > 1)

    train, valid = grouped_split(rows, args.validation_fraction)
    train_keys = {keys[i] for i in train}
    valid_keys = {keys[i] for i in valid}
    overlap = train_keys & valid_keys

    print(f"rows={len(rows)}")
    print(f"unique_positions={len(counts)}")
    print(f"duplicate_rows={duplicates}")
    print(f"duplicate_ratio={duplicate_ratio:.6f}")
    print(f"positions_with_conflicting_scores={conflicting_labels}")
    print(f"grouped_train_rows={len(train)}")
    print(f"grouped_validation_rows={len(valid)}")
    print(f"grouped_exact_position_overlap={len(overlap)}")
    print(f"score_min={min(scores):.3f}")
    print(f"score_max={max(scores):.3f}")
    print(f"score_mean={statistics.fmean(scores):.3f}")
    print(f"score_stdev={statistics.stdev(scores):.3f}" if len(scores) > 1 else "score_stdev=0.000")

    if overlap:
        raise SystemExit("ERROR: grouped split leaked exact RWEN positions")
    if args.fail_on_duplicate_ratio is not None and duplicate_ratio > args.fail_on_duplicate_ratio:
        raise SystemExit(
            f"ERROR: duplicate ratio {duplicate_ratio:.6f} exceeds "
            f"threshold {args.fail_on_duplicate_ratio:.6f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
