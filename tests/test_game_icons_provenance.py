import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "tools" / "licensing" / "game_icons_manifest.json"
TOOL_PATH = ROOT / "tools" / "licensing" / "match_game_icons.py"

VALID_STATUSES = {"CONFIRMED", "HIGH CONFIDENCE", "AMBIGUOUS", "UNRESOLVED"}


def load_tool_module():
    spec = importlib.util.spec_from_file_location("match_game_icons", TOOL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_game_icons_manifest_is_structurally_valid():
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "redwar-game-icons-provenance-v1"
    assert payload["source_of_truth"]["default_license"] == "CC BY 3.0"
    assert payload["source_of_truth"]["explicit_license_exceptions"] == ["CC0"]
    assert payload["source_of_truth"]["corpus_revision"]

    assets = payload["assets"]
    assert len(assets) == 19
    assert len({entry["local_file"] for entry in assets}) == len(assets)

    for entry in assets:
        assert entry["local_file"].startswith("ui/assets/")
        assert entry["local_file"].endswith(".png")
        assert entry["match"] is None or entry["match"]["status"] in VALID_STATUSES

    summary = payload["summary"]
    assert sum(summary[key] for key in ("confirmed", "high_confidence", "ambiguous", "unresolved")) == 19


def test_game_icons_audit_tool_is_valid_python_source():
    source = TOOL_PATH.read_text(encoding="utf-8")
    compile(source, str(TOOL_PATH), "exec")


def test_upstream_cc0_exceptions_are_resolved_from_license_text(tmp_path):
    module = load_tool_module()
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "license.txt").write_text(
        "- Viscious Speed, https://example.invalid - CC0\n"
        "- Zeromancer - CC0\n"
        "- Delapouite, http://example.invalid\n",
        encoding="utf-8",
    )

    metadata = module.contributor_licenses(corpus)

    assert metadata[module.normalize_contributor_name("Viscious Speed")]["license"] == "CC0"
    assert metadata[module.normalize_contributor_name("Zeromancer")]["license"] == "CC0"
    assert metadata[module.normalize_contributor_name("Delapouite")]["license"] == "CC BY 3.0"


def test_unknown_contributor_metadata_does_not_receive_guessed_license():
    module = load_tool_module()
    resolved = module.resolve_contributor_metadata("unknown-contributor", {})

    assert resolved["license"] is None
    assert resolved["metadata_match"] == "unresolved-folder-name"
