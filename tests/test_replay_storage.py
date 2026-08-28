import gzip
import hashlib
import json

import pytest

from engine.game_state import GameState
from engine.pieces import FrostMage, Inquisitor, Ranger
from tools.replay.storage import (
    HOT_CACHE_SIZE,
    CHUNK_SIZE,
    ReplayCorruptionError,
    ReplayStore,
    build_record,
    reconstruct,
    snapshot_state,
)


def _record(i: int) -> dict:
    record = {
        "schema_version": 1,
        "game_id": f"game-{i:04d}",
        "created_at": "2026-08-28T00:00:00+00:00",
        "metadata": {"mode": "test", "engine_commit": "test", "rules_hash": "r", "hero_config_hash": "h"},
        "initial": {"side_to_move": "brancas", "turns_without_capture": 0, "pieces": [], "effects": []},
        "moves": [["move", 7, 0, 6, 0, None, None]] * max(1, i % 11),
        "result": {"winner": "Brancas", "termination_reason": "test", "plies": max(1, i % 11), "final_hash": i},
    }
    record["record_sha256"] = hashlib.sha256(
        json.dumps({k: v for k, v in record.items() if k != "record_sha256"}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return record


def test_round_trip_reconstructs_state():
    gs = GameState()
    gs.board[7][0] = Ranger("brancas")
    gs.board[0][0] = Ranger("pretas")
    gs.compute_initial_hash()
    initial = snapshot_state(gs)
    gs.execute_action({"type": "move", "start": (7, 0), "end": (6, 0)})
    gs.execute_action({"type": "move", "start": (0, 0), "end": (1, 0)})

    record = build_record(gs, initial)
    rebuilt = reconstruct(record)
    assert rebuilt.to_rwen() == gs.to_rwen()
    assert rebuilt.get_state_hash() == gs.get_state_hash()


def test_ten_game_hot_cache_does_not_limit_retention(tmp_path):
    store = ReplayStore(tmp_path)
    for i in range(11):
        store.save(_record(i))

    recent = store.recent()
    assert len(recent) == HOT_CACHE_SIZE
    assert recent[0]["game_id"] == "game-0010"
    assert store.load("game-0000") is not None
    assert "game-0000" not in store._load_index()["hot_cache"]


def test_chunk_archive_seals_and_keeps_old_records(tmp_path, monkeypatch):
    import tools.replay.storage as storage

    monkeypatch.setattr(storage, "CHUNK_SIZE", 2)
    store = ReplayStore(tmp_path)
    for i in range(3):
        store.save(_record(i))

    assert (tmp_path / "archive" / "chunk-000001.jsonl.gz").exists()
    assert store.load("game-0000")["game_id"] == "game-0000"


def test_corrupt_replay_is_rejected(tmp_path):
    store = ReplayStore(tmp_path)
    store.save(_record(1))
    chunk = tmp_path / "archive" / "chunk-000001.open"
    payload = bytearray(chunk.read_bytes())
    payload[-2:] = b"!!"
    chunk.write_bytes(payload)
    with pytest.raises(ReplayCorruptionError):
        store.load("game-0001")


def test_compressed_chunk_load_matches_original(tmp_path, monkeypatch):
    import tools.replay.storage as storage

    monkeypatch.setattr(storage, "CHUNK_SIZE", 1)
    store = ReplayStore(tmp_path)
    original = _record(1)
    store.save(original)
    loaded = store.load("game-0001")
    assert loaded == original
    assert gzip.decompress((tmp_path / "archive" / "chunk-000001.jsonl.gz").read_bytes()).strip()


def test_schema_version_is_validated(tmp_path):
    store = ReplayStore(tmp_path)
    store.save(_record(1))
    index = json.loads((tmp_path / "index.json").read_text())
    index["schema_version"] = 999
    (tmp_path / "index.json").write_text(json.dumps(index))
    with pytest.raises(ReplayCorruptionError):
        store.load("game-0001")


def test_silenced_spells_are_not_generated_but_authoritative_validator_rejects_direct_call():
    gs = GameState()
    gs.board[4][0] = FrostMage("brancas")
    gs.board[4][2] = Inquisitor("pretas")
    gs.board[4][3] = Ranger("pretas")
    gs.compute_initial_hash()

    assert gs.board[4][0].get_valid_spells(4, 0, gs.board, gs.tile_effects) == []
    with pytest.raises(ValueError, match="SPELL is blocked by Inquisitor silence"):
        gs.execute_action({"type": "spell", "start": (4, 0), "end": (4, 3), "spell_name": "nevada"})


def test_game_state_capture_and_finalize_persists_completed_game(tmp_path, monkeypatch):
    monkeypatch.setenv("REDWAR_REPLAY_DIR", str(tmp_path))
    import tools.replay.storage as storage

    gs = GameState()
    gs.board[7][0] = Ranger("brancas")
    gs.board[0][0] = Ranger("pretas")
    gs.compute_initial_hash()
    gs.execute_action({"type": "move", "start": (7, 0), "end": (6, 0)})
    gs.execute_action({"type": "move", "start": (0, 0), "end": (1, 0)})
    gs.game_over = True
    gs.winner = "Brancas"
    game_id = storage.finalize_completed_game(gs)

    assert game_id is not None
    assert ReplayStore(tmp_path).load(game_id) is not None
