from __future__ import annotations

import json
from pathlib import Path


def test_game_icons_manifest_completeness():
    root = Path(__file__).resolve().parent.parent
    assets_dir = root / "ui" / "assets"
    manifest_file = root / "tools" / "licensing" / "game_icons_manifest.json"

    assert manifest_file.exists(), "game_icons_manifest.json must exist"

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    manifest_files = {entry["local_file"].replace("\\", "/") for entry in manifest.get("assets", [])}
    actual_files = {f"ui/assets/{p.name}" for p in assets_dir.glob("*.png")}

    assert actual_files, "Expected at least one PNG asset in ui/assets"
    # All actual assets must be tracked in the manifest
    missing_from_manifest = actual_files - manifest_files
    assert not missing_from_manifest, f"PNG assets missing from manifest: {missing_from_manifest}"


def test_requirements_documented_in_licenses():
    root = Path(__file__).resolve().parent.parent
    req_file = root / "requirements.txt"
    third_party_doc = root / "docs" / "THIRD_PARTY_LICENSES.md"
    legal_doc = root / "docs" / "LEGAL_AND_LICENSES.md"

    assert req_file.exists()
    assert third_party_doc.exists()
    assert legal_doc.exists()

    tp_text = third_party_doc.read_text(encoding="utf-8")
    legal_text = legal_doc.read_text(encoding="utf-8")

    packages = ["pygame", "pytest", "websockets", "Cython"]
    for pkg in packages:
        assert pkg in tp_text, f"Package {pkg} must be documented in THIRD_PARTY_LICENSES.md"
        assert pkg in legal_text, f"Package {pkg} must be documented in LEGAL_AND_LICENSES.md"


def test_repository_licenses_present():
    root = Path(__file__).resolve().parent.parent
    mit_license = root / "LICENSE"
    gpl_license = root / "ai" / "LICENSE"

    assert mit_license.exists(), "Root LICENSE must exist"
    assert "MIT License" in mit_license.read_text(encoding="utf-8")

    assert gpl_license.exists(), "AI subfolder LICENSE must exist"
    assert "General Public License" in gpl_license.read_text(encoding="utf-8")
