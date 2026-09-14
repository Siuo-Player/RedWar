"""Compare two deterministic Ares search-baseline JSON artifacts.

The LMR experiment requires a frozen no-LMR reference.  This utility compares
machine-readable outputs produced by ``move_ordering_baseline.py`` without
interpreting node-count improvements as strength evidence.

The comparison is intentionally conservative: case ordering, node budgets,
return codes, validation errors, best moves, legality/mode fields and PASS/FAIL
results must remain identical.  Node counts and elapsed time are reported but
are not used as correctness gates.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def _index_rows(payload: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    cases = payload.get("cases")
    results = payload.get("results")
    if not isinstance(cases, list) or not isinstance(results, list):
        raise ValueError("baseline artifact must contain list fields 'cases' and 'results'")

    for result in results:
        if not isinstance(result, dict):
            raise ValueError("each case result must be a JSON object")
        case = result.get("case")
        case_rows = result.get("results")
        if not isinstance(case, str) or not isinstance(case_rows, list):
            raise ValueError("each case result needs string 'case' and list 'results'")
        for row in case_rows:
            if not isinstance(row, dict) or not isinstance(row.get("nodes"), int):
                raise ValueError(f"invalid result row for case={case}")
            key = (case, row["nodes"])
            if key in rows:
                raise ValueError(f"duplicate result row: case={case} nodes={row['nodes']}")
            rows[key] = row
    return rows


def compare(reference: dict[str, Any], candidate: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    diagnostics: list[str] = []

    for field in ("schema_version", "cases", "node_budgets"):
        if reference.get(field) != candidate.get(field):
            errors.append(
                f"metadata mismatch for {field}: "
                f"reference={reference.get(field)!r} candidate={candidate.get(field)!r}"
            )

    try:
        ref_rows = _index_rows(reference)
        cand_rows = _index_rows(candidate)
    except ValueError as exc:
        errors.append(str(exc))
        return errors, diagnostics

    if set(ref_rows) != set(cand_rows):
        missing = sorted(set(ref_rows) - set(cand_rows))
        extra = sorted(set(cand_rows) - set(ref_rows))
        if missing:
            errors.append(f"candidate is missing rows: {missing}")
        if extra:
            errors.append(f"candidate has unexpected rows: {extra}")

    for key in sorted(set(ref_rows) & set(cand_rows)):
        ref = ref_rows[key]
        cand = cand_rows[key]
        case, nodes = key

        for field in ("bestmove", "legal", "mode", "passed"):
            if ref.get(field) != cand.get(field):
                errors.append(
                    f"regression at case={case} nodes={nodes}: {field} "
                    f"reference={ref.get(field)!r} candidate={cand.get(field)!r}"
                )

        ref_time = float(ref.get("elapsed_seconds", 0.0))
        cand_time = float(cand.get("elapsed_seconds", 0.0))
        ref_nodes = int(ref.get("nodes", nodes))
        cand_nodes = int(cand.get("nodes", nodes))
        diagnostics.append(
            f"case={case} nodes={nodes} reference_nodes={ref_nodes} "
            f"candidate_nodes={cand_nodes} reference_time={ref_time:.6f}s "
            f"candidate_time={cand_time:.6f}s"
        )

    return errors, diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path, help="frozen no-LMR JSON artifact")
    parser.add_argument("candidate", type=Path, help="candidate LMR JSON artifact")
    args = parser.parse_args()

    reference = _load(args.reference)
    candidate = _load(args.candidate)
    errors, diagnostics = compare(reference, candidate)

    for line in diagnostics:
        print(line)
    if errors:
        print("SEARCH REGRESSION: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("SEARCH REGRESSION: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
