"""Compact, durable local replay storage for RedWar."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
HOT_CACHE_SIZE = 10
CHUNK_SIZE = 256
DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data" / "replays"
_INITIAL_STATES: dict[int, dict[str, Any]] = {}
_FINALIZED_GAMES: dict[int, str] = {}


class ReplayCorruptionError(ValueError):
    """Raised when replay data cannot be decoded or fails integrity checks."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _git_commit() -> str | None:
    try:
        root = Path(__file__).resolve().parents[2]
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _termination_reason(winner: str | None) -> str:
    text = (winner or "").casefold()
    if "bloqueado" in text:
        return "opponent_blocked"
    if "material" in text:
        return "no_capture_material_tiebreak"
    if "aniquilação mútua" in text:
        return "mutual_annihilation_tiebreak"
    if "aniquilação" in text:
        return "annihilation"
    return "unknown" if not winner else "game_over"


def snapshot_state(gs: Any) -> dict[str, Any]:
    """Return the battle-start state needed for deterministic reconstruction."""
    pieces = []
    effects = []
    for r, row in enumerate(gs.board):
        for c, piece in enumerate(row):
            if piece is not None:
                pieces.append(
                    [
                        r,
                        c,
                        piece.name,
                        piece.team,
                        int(getattr(piece, "stun_timer", 0)),
                        getattr(piece, "lifespan", None),
                        int(getattr(piece, "spawn_cooldown", 0)),
                    ]
                )
    for r, row in enumerate(gs.tile_effects):
        for c, effect in enumerate(row):
            if effect is not None:
                effects.append(
                    [
                        r,
                        c,
                        effect.get("type"),
                        effect.get("team"),
                        int(effect.get("timer", 0)),
                    ]
                )
    return {
        "side_to_move": "brancas" if gs.white_to_move else "pretas",
        "turns_without_capture": int(gs.turns_without_capture),
        "pieces": pieces,
        "effects": effects,
    }


def _compact_action(action: dict[str, Any]) -> list[Any]:
    return [
        str(action["type"]).lower(),
        int(action["start"][0]),
        int(action["start"][1]),
        int(action["end"][0]),
        int(action["end"][1]),
        action.get("spell_name"),
        action.get("spawn_name"),
    ]


def _expand_action(item: list[Any]) -> dict[str, Any]:
    if not isinstance(item, list) or len(item) != 7:
        raise ReplayCorruptionError("Malformed compact replay action")
    return {
        "type": str(item[0]),
        "start": (int(item[1]), int(item[2])),
        "end": (int(item[3]), int(item[4])),
        "spell_name": item[5],
        "spawn_name": item[6],
    }


def build_record(gs: Any, initial: dict[str, Any]) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    record = {
        "schema_version": SCHEMA_VERSION,
        "game_id": uuid.uuid4().hex,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "metadata": {
            "engine_commit": _git_commit(),
            "rules_hash": _sha256_file(root / "engine" / "game_state.py"),
            "hero_config_hash": _sha256_file(root / "engine" / "heroes_config.json"),
            "mode": "local",
            "player_side": "brancas",
            "opponent": "Ares",
        },
        "initial": initial,
        "moves": [
            _compact_action(entry["acao_escolhida"])
            for entry in gs.move_log
            if isinstance(entry, dict) and isinstance(entry.get("acao_escolhida"), dict)
        ],
        "result": {
            "winner": gs.winner,
            "termination_reason": _termination_reason(gs.winner),
            "plies": len(gs.move_log),
            "final_hash": int(gs.get_state_hash()),
        },
    }
    record["record_sha256"] = hashlib.sha256(_canonical_json(record)).hexdigest()
    return record


def capture_initial(gs: Any) -> None:
    """Capture the first battle state for a live GameState."""
    _INITIAL_STATES.setdefault(id(gs), snapshot_state(gs))


def finalize_completed_game(gs: Any) -> str | None:
    """Persist a completed game; repeated finalization returns the same game id."""
    key = id(gs)
    finalized_id = _FINALIZED_GAMES.get(key)
    if finalized_id is not None:
        return finalized_id if gs.game_over else None

    initial = _INITIAL_STATES.pop(key, None)
    if initial is None or not gs.game_over:
        return None

    record = build_record(gs, initial)
    ReplayStore().save(record)
    game_id = str(record["game_id"])
    _FINALIZED_GAMES[key] = game_id
    return game_id


class ReplayStore:
    """Append-only chunked archive. The hot cache is ten IDs, not ten retained games."""

    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root is not None else Path(
            os.environ.get("REDWAR_REPLAY_DIR", str(DEFAULT_ROOT))
        )
        self.archive = self.root / "archive"
        self.index_path = self.root / "index.json"

    def _load_index(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return {
                "schema_version": SCHEMA_VERSION,
                "hot_cache": [],
                "games": {},
                "important": {},
                "next_chunk": 1,
                "open_count": 0,
            }
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReplayCorruptionError("Replay index is unreadable") from exc
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ReplayCorruptionError("Unsupported replay index schema")
        return data

    def _write_index(self, index: dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix="index.", suffix=".tmp", dir=self.root)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(index, handle, ensure_ascii=False, sort_keys=True, indent=2)
                handle.write("\n")
            os.replace(tmp_name, self.index_path)
        finally:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass

    def _open_path(self, chunk_id: int) -> Path:
        return self.archive / f"chunk-{chunk_id:06d}.open"

    def _sealed_path(self, chunk_id: int) -> Path:
        return self.archive / f"chunk-{chunk_id:06d}.jsonl.gz"

    def _seal(self, chunk_id: int) -> None:
        source = self._open_path(chunk_id)
        if not source.exists():
            return
        try:
            compressed = gzip.compress(source.read_bytes(), compresslevel=9, mtime=0)
        except OSError as exc:
            raise ReplayCorruptionError(f"Cannot read replay chunk {chunk_id}") from exc
        fd, tmp_name = tempfile.mkstemp(
            prefix=f"chunk-{chunk_id:06d}.", suffix=".tmp", dir=self.archive
        )
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(compressed)
            os.replace(tmp_name, self._sealed_path(chunk_id))
            source.unlink()
        finally:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass

    def save(self, record: dict[str, Any]) -> None:
        if record.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Unsupported replay schema")
        game_id = str(record.get("game_id", ""))
        if not game_id:
            raise ValueError("Replay game_id is required")
        actual = hashlib.sha256(
            _canonical_json({k: v for k, v in record.items() if k != "record_sha256"})
        ).hexdigest()
        if record.get("record_sha256") != actual:
            raise ValueError("Replay record hash does not match its content")

        self.archive.mkdir(parents=True, exist_ok=True)
        index = self._load_index()
        games = index.setdefault("games", {})
        if game_id in games:
            raise ValueError(f"Replay already exists: {game_id}")

        chunk_id = int(index.get("next_chunk", 1))
        open_count = int(index.get("open_count", 0))
        if open_count >= CHUNK_SIZE:
            self._seal(chunk_id)
            chunk_id += 1
            open_count = 0
            index["next_chunk"] = chunk_id

        with self._open_path(chunk_id).open("ab") as handle:
            handle.write(_canonical_json(record) + b"\n")
        games[game_id] = {
            "chunk": chunk_id,
            "line": open_count,
            "sha256": record["record_sha256"],
        }

        hot = [gid for gid in index.get("hot_cache", []) if gid != game_id]
        hot.append(game_id)
        index["hot_cache"] = hot[-HOT_CACHE_SIZE:]
        index["open_count"] = open_count + 1
        if index["open_count"] >= CHUNK_SIZE:
            self._seal(chunk_id)
            index["next_chunk"] = chunk_id + 1
            index["open_count"] = 0
        self._write_index(index)

    def _read_chunk(self, chunk_id: int) -> list[dict[str, Any]]:
        sealed = self._sealed_path(chunk_id)
        opened = self._open_path(chunk_id)
        try:
            if sealed.exists():
                raw = gzip.decompress(sealed.read_bytes())
            elif opened.exists():
                raw = opened.read_bytes()
            else:
                raise ReplayCorruptionError(f"Replay chunk {chunk_id} is missing")
        except (OSError, EOFError, gzip.BadGzipFile) as exc:
            raise ReplayCorruptionError(f"Replay chunk {chunk_id} cannot be decoded") from exc
        records = []
        for line in raw.splitlines():
            try:
                records.append(json.loads(line.decode("utf-8")))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ReplayCorruptionError(
                    f"Replay chunk {chunk_id} contains invalid JSON"
                ) from exc
        return records

    def load(self, game_id: str) -> dict[str, Any] | None:
        index = self._load_index()
        entry = index.get("games", {}).get(game_id)
        if entry is None:
            return None
        records = self._read_chunk(int(entry["chunk"]))
        line = int(entry["line"])
        if not 0 <= line < len(records):
            raise ReplayCorruptionError(f"Replay index points outside chunk for {game_id}")
        record = records[line]
        if record.get("schema_version") != SCHEMA_VERSION:
            raise ReplayCorruptionError(f"Unsupported replay schema for {game_id}")
        actual = hashlib.sha256(
            _canonical_json({k: v for k, v in record.items() if k != "record_sha256"})
        ).hexdigest()
        if record.get("record_sha256") != actual or entry.get("sha256") != actual:
            raise ReplayCorruptionError(f"Replay integrity check failed for {game_id}")
        return record

    def recent(self) -> list[dict[str, Any]]:
        return [
            self.load(gid)
            for gid in reversed(self._load_index().get("hot_cache", []))
        ]

    def mark_important(self, game_id: str, reason: str) -> None:
        if self.load(game_id) is None:
            raise KeyError(game_id)
        index = self._load_index()
        index.setdefault("important", {})[game_id] = {
            "reason": str(reason),
            "marked_at": datetime.now(timezone.utc).isoformat(),
        }
        self._write_index(index)


def _restore_state(snapshot: dict[str, Any]):
    from engine.game_state import GameState
    from engine.pieces import criar_peca_por_nome

    if not isinstance(snapshot, dict):
        raise ReplayCorruptionError("Initial replay state must be an object")
    gs = GameState()
    for item in snapshot.get("pieces", []):
        if not isinstance(item, list) or len(item) != 7:
            raise ReplayCorruptionError("Malformed replay piece")
        r, c, name, team, stun, lifespan, cooldown = item
        piece = criar_peca_por_nome(str(name), str(team))
        piece.stun_timer = int(stun)
        piece.lifespan = lifespan
        piece.spawn_cooldown = int(cooldown)
        gs.board[int(r)][int(c)] = piece
    for item in snapshot.get("effects", []):
        if not isinstance(item, list) or len(item) != 5:
            raise ReplayCorruptionError("Malformed replay effect")
        r, c, effect_type, team, timer = item
        gs.tile_effects[int(r)][int(c)] = {
            "type": effect_type,
            "team": team,
            "timer": int(timer),
        }
    gs.white_to_move = snapshot.get("side_to_move") == "brancas"
    gs.turns_without_capture = int(snapshot.get("turns_without_capture", 0))
    gs.compute_initial_hash()
    return gs


def reconstruct(record: dict[str, Any]):
    if record.get("schema_version") != SCHEMA_VERSION:
        raise ReplayCorruptionError("Unsupported replay schema")
    gs = _restore_state(record["initial"])
    for compact in record.get("moves", []):
        action = _expand_action(compact)
        affected_area = []
        if action["type"] == "stun":
            attacker = gs.board[action["start"][0]][action["start"][1]]
            if attacker:
                stuns = attacker.get_valid_stuns(
                    action["start"][0],
                    action["start"][1],
                    gs.board,
                    gs.tile_effects,
                )
                if action["end"] in stuns:
                    affected_area = stuns[action["end"]].get("aoe", [])
        gs.make_action(
            action["start"],
            action["end"],
            action["type"],
            affected_area=affected_area,
            spawn_name=action.get("spawn_name"),
            spell_name=action.get("spell_name"),
            is_simulation=True,
        )
    return gs
