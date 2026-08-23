from pathlib import Path

import pytest

from tools.analytics.game_analyzer import analisar_partidas
from tools.scripts.audit_structure import audit
from tools.scripts.build_cpp_engine import ENGINE_SOURCES, SMOKE_SOURCES


def test_game_analyzer_reads_arena_jsonl_without_resimulating(tmp_path: Path):
    source = tmp_path / "games.jsonl"
    source.write_text(
        '{"outcome":"challenger","challenger_color":"white","plies":12,'
        '"opening_index":0,"action_counts":{"move":8,"stun":4}}\n'
        '{"outcome":"baseline","challenger_color":"black","plies":10,'
        '"opening_index":1,"action_counts":{"move":10}}\n',
        encoding="utf-8",
    )

    summary = analisar_partidas(source)

    assert summary["games"] == 2
    assert summary["invalid_records"] == 0
    assert summary["challenger_wins"] == 1
    assert summary["baseline_wins"] == 1
    assert summary["margin"] == 0
    assert summary["action_counts"] == {"move": 18, "stun": 4}
    assert summary["average_plies"] == pytest.approx(11.0)


def test_game_analyzer_rejects_invalid_json(tmp_path: Path):
    source = tmp_path / "broken.jsonl"
    source.write_text("{not-json}\n", encoding="utf-8")

    with pytest.raises(ValueError):
        analisar_partidas(source)


def test_structure_audit_is_non_destructive_and_knows_expected_top_level(tmp_path: Path):
    for name in {"ai", "data", "deploy", "docs", "engine", "logs", "online", "tests", "tools", "ui"}:
        (tmp_path / name).mkdir()

    assert audit(tmp_path) == []


def test_production_cpp_build_does_not_glob_test_sources():
    assert "main.cpp" in ENGINE_SOURCES
    assert "nnue.cpp" in ENGINE_SOURCES
    assert "SmokeTest.cpp" not in ENGINE_SOURCES
    assert "SmokeTest.cpp" in SMOKE_SOURCES
