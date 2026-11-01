# tests/test_wiki_integrity.py
"""
Test suite validating the integrity and completeness of the RedWar GitHub Wiki documentation.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WIKI_DIR = ROOT / "wiki"


def test_wiki_directory_exists_and_contains_core_pages():
    assert WIKI_DIR.exists()
    assert WIKI_DIR.is_dir()

    expected_pages = [
        "Home.md",
        "Game-Rules.md",
        "Hero-Roster-and-Academy.md",
        "Ares-Engine-and-SPRT-Methodology.md",
        "Game-Modes.md",
        "Deployment-and-Security.md",
    ]
    for page in expected_pages:
        page_path = WIKI_DIR / page
        assert page_path.exists(), f"Missing wiki page: {page}"
        content = page_path.read_text(encoding="utf-8")
        assert len(content) > 100, f"Wiki page too short: {page}"


def test_home_page_links_to_all_sections():
    home = (WIKI_DIR / "Home.md").read_text(encoding="utf-8")
    assert "Game-Rules" in home
    assert "Hero-Roster-and-Academy" in home
    assert "Ares-Engine-and-SPRT-Methodology" in home
    assert "Game-Modes" in home
    assert "Deployment-and-Security" in home
