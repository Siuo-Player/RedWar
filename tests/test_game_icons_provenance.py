import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tools" / "licensing" / "game_icons_manifest.json"

VALID_STATUSES = {"CONFIRMED", "HIGH CONFIDENCE", "AMBIGUOUS", "UNRESOLVED"}


def test_game_icons_manifest_is_structurally_valid():
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "redwar-game-icons-provenance-v1"
    assert payload["source_of_truth"]["license"] == "CC BY 3.0"
    assert payload["source_of_truth"]["corpus_revision"]

    assets = payload["assets"]
    assert len(assets) == 19
    assert len({entry["local_file"] for entry in assets}) == len(assets)

    for entry in assets:
        assert entry["local_file"].startswith("ui/assets/")
        assert entry["local_file"].endswith(".png")
        assert entry["status"] in VALID_STATUSES

    summary = payload["summary"]
    assert sum(summary[key] for key in ("confirmed", "high_confidence", "ambiguous", "unresolved")) == 19
