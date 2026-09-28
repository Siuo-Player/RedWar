"""Remove local RedWar replay records that contain no moves.

Usage:
    python tools/replay/cleanup_empty_replays.py
    python tools/replay/cleanup_empty_replays.py --yes
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.replay.storage import ReplayStore


def _ordered_game_ids(store: ReplayStore) -> list[str]:
    index = store._load_index()
    return [
        game_id
        for game_id, _entry in sorted(
            index.get("games", {}).items(),
            key=lambda item: (int(item[1]["chunk"]), int(item[1]["line"])),
        )
    ]


def _find_empty_replays(store: ReplayStore) -> tuple[list[str], list[dict]]:
    empty: list[str] = []
    kept: list[dict] = []

    for game_id in _ordered_game_ids(store):
        record = store.load(game_id)
        if record is None:
            raise RuntimeError(f"Replay index references missing game: {game_id}")

        moves = record.get("moves", [])
        if not isinstance(moves, list):
            raise RuntimeError(f"Replay {game_id} has a malformed moves field")

        if not moves:
            empty.append(game_id)
        else:
            kept.append(record)

    return empty, kept


def _rebuild(root: Path, kept_records: list[dict]) -> Path:
    store = ReplayStore(root)
    old_index = store._load_index()
    important = old_index.get("important", {}) or {}

    temp_root = Path(tempfile.mkdtemp(prefix=f"{root.name}.cleanup-", dir=str(root.parent)))
    backup_root = root.with_name(
        f"{root.name}.backup-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    )
    temp_store = ReplayStore(temp_root)

    try:
        for record in kept_records:
            temp_store.save(record)

        for game_id, marker in important.items():
            if temp_store.load(game_id) is not None:
                temp_store.mark_important(
                    game_id,
                    str(marker.get("reason", "")) if isinstance(marker, dict) else str(marker),
                )

        backup_root.mkdir(parents=False)
        old_archive = root / "archive"
        old_index_path = root / "index.json"

        if old_archive.exists():
            shutil.move(str(old_archive), str(backup_root / "archive"))
        if old_index_path.exists():
            shutil.move(str(old_index_path), str(backup_root / "index.json"))

        new_archive = temp_root / "archive"
        new_index = temp_root / "index.json"
        if new_archive.exists():
            shutil.move(str(new_archive), str(root / "archive"))
        if new_index.exists():
            shutil.move(str(new_index), str(root / "index.json"))

        return backup_root
    except Exception:
        restored_archive = backup_root / "archive"
        restored_index = backup_root / "index.json"

        current_archive = root / "archive"
        current_index = root / "index.json"
        if current_archive.exists() and not restored_archive.exists():
            shutil.move(str(current_archive), str(restored_archive))
        if current_index.exists() and not restored_index.exists():
            shutil.move(str(current_index), str(restored_index))

        if restored_archive.exists() and not current_archive.exists():
            shutil.move(str(restored_archive), str(current_archive))
        if restored_index.exists() and not current_index.exists():
            shutil.move(str(restored_index), str(current_index))
        raise
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remove RedWar replay records with zero moves."
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Replay root; defaults to REDWAR_REPLAY_DIR or data/replays.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Actually rebuild the archive. Without this flag, only report what would be removed.",
    )
    args = parser.parse_args()

    store = ReplayStore(args.root)
    empty_ids, kept_records = _find_empty_replays(store)

    print(f"Replays encontrados: {len(empty_ids) + len(kept_records)}")
    print(f"Replays vazios:      {len(empty_ids)}")

    if empty_ids:
        for game_id in empty_ids:
            print(f"  - {game_id}")
    else:
        print("Nenhum replay vazio encontrado.")

    if not empty_ids:
        return 0

    if not args.yes:
        print("\nNada foi apagado. Use --yes para remover os replays vazios.")
        return 0

    root = store.root
    backup_root = _rebuild(root, kept_records)
    print(f"\nRemovidos: {len(empty_ids)}")
    print(f"Backup criado em: {backup_root}")
    print(f"Replays restantes: {len(kept_records)}")

    verify_store = ReplayStore(root)
    remaining_empty, _ = _find_empty_replays(verify_store)
    if remaining_empty:
        raise RuntimeError(
            f"Limpeza incompleta: ainda existem {len(remaining_empty)} replays vazios."
        )

    print("Verificação final: nenhum replay vazio permanece no índice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
