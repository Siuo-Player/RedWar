from pathlib import Path

import pytest

from tools.analytics.holdout_validation import canonical_sha256, load_holdout, validate_holdout


def test_holdout_manifest_is_non_empty_and_unique():
    manifest = load_holdout()
    ids = [case["id"] for case in manifest["cases"]]
    assert len(ids) >= 8
    assert len(ids) == len(set(ids))


def test_holdout_hash_is_deterministic():
    first = canonical_sha256()
    second = canonical_sha256()
    assert first == second
    assert len(first) == 64
    assert validate_holdout()[0] == 8


def test_holdout_validator_rejects_duplicate_ids(tmp_path: Path):
    source = load_holdout()
    source["cases"].append(dict(source["cases"][0]))
    path = tmp_path / "holdout.json"
    import json

    path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="unique"):
        load_holdout(path)
