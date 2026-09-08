import json
from pathlib import Path


DATASET = Path("data/arena/strength/2026-08-27-control-100.json")


def test_control_dataset_distinguishes_games_from_paired_units():
    payload = json.loads(DATASET.read_text(encoding="utf-8"))
    manifest = payload["manifest"]

    assert manifest["game_records"] == 100
    assert manifest["independent_units"] == 50
    assert manifest["independent_unit_policy"] == (
        "one complete colour-inverted A/B pair is one independent resampling unit"
    )
    assert len(payload["games"]) == manifest["game_records"]
    assert len(payload["independent_units"]) == manifest["independent_units"]
    assert manifest["independent_units"] != manifest["game_records"]
