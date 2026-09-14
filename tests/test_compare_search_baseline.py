from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "analytics" / "compare_search_baseline.py"


def _write(path: Path, *, bestmove: str = "A1A2") -> None:
    payload = {
        "schema_version": 1,
        "cases": ["case-a"],
        "node_budgets": [10, 25],
        "results": [
            {
                "case": "case-a",
                "return_code": 0,
                "validation_errors": [],
                "results": [
                    {
                        "nodes": 10,
                        "bestmove": bestmove,
                        "elapsed_seconds": 0.01,
                        "legal": "true",
                        "mode": "normal",
                        "passed": True,
                    },
                    {
                        "nodes": 25,
                        "bestmove": bestmove,
                        "elapsed_seconds": 0.02,
                        "legal": "true",
                        "mode": "normal",
                        "passed": True,
                    },
                ],
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _run(reference: Path, candidate: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(reference), str(candidate)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_identical_baselines_pass(tmp_path: Path) -> None:
    reference = tmp_path / "reference.json"
    candidate = tmp_path / "candidate.json"
    _write(reference)
    _write(candidate)

    completed = _run(reference, candidate)

    assert completed.returncode == 0
    assert "SEARCH REGRESSION: PASS" in completed.stdout


def test_bestmove_change_fails(tmp_path: Path) -> None:
    reference = tmp_path / "reference.json"
    candidate = tmp_path / "candidate.json"
    _write(reference, bestmove="A1A2")
    _write(candidate, bestmove="A1B1")

    completed = _run(reference, candidate)

    assert completed.returncode == 1
    assert "bestmove" in completed.stderr
    assert "SEARCH REGRESSION: FAIL" in completed.stderr
