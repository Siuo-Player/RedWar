"""Benchmark replay representations on representative synthetic RedWar games.

The benchmark intentionally does not change the production codec. It compares:
1. pretty JSON (baseline/debug-friendly),
2. canonical compact JSON,
3. gzip-compressed canonical JSON (current local archive), and
4. MessagePack as a binary candidate when the optional package is installed.

Use this tool again with a real replay corpus once accumulated; the fixture set
here is a repeatable engineering baseline, not evidence about gameplay strength.
"""

from __future__ import annotations

import argparse
import gzip
import json
import statistics
import time
from dataclasses import dataclass
from typing import Any, Callable

try:
    import msgpack  # type: ignore
except ImportError:  # pragma: no cover - optional benchmark dependency
    msgpack = None


@dataclass(frozen=True)
class Case:
    name: str
    record: dict[str, Any]


def make_case(name: str, plies: int, rich: bool) -> Case:
    pieces = []
    effects = []
    if rich:
        names = ["FrostMage", "Lich", "Ranger", "Inquisitor", "Pyromancer", "Dragoon", "Geomancer", "Cleric"]
        for i, hero in enumerate(names):
            pieces.append([i // 4, i % 8, hero, "brancas" if i % 2 == 0 else "pretas", i % 3, 5 if i % 3 == 0 else None, i % 5])
            effects.append([i // 4, (i + 2) % 8, "ice" if i % 2 else "fire", "brancas" if i % 2 == 0 else "pretas", 3 + i % 4])
    else:
        pieces = [[7, 0, "Ranger", "brancas", 0, None, 0], [0, 7, "Ranger", "pretas", 0, None, 0]]

    move_types = ["move", "move", "attack", "stun", "spell", "spawn"] if rich else ["move", "attack"]
    moves = []
    for i in range(plies):
        kind = move_types[i % len(move_types)]
        spell = None
        spawn = None
        if kind == "spell":
            spell = "nevada" if i % 2 == 0 else "ignite"
        elif kind == "spawn":
            spawn = "Ghoul"
        moves.append([kind, i % 8, (i * 3) % 8, (i + 1) % 8, (i * 5 + 1) % 8, spell, spawn])

    record = {
        "schema_version": 1,
        "game_id": f"fixture-{name}",
        "created_at": "2026-08-28T00:00:00+00:00",
        "metadata": {
            "engine_commit": "3e68bff103eb7d0d1d20085b9b5abc4db544e7f9",
            "rules_hash": "a" * 64,
            "hero_config_hash": "b" * 64,
            "mode": "local",
            "player_side": "brancas",
            "opponent": "Ares",
        },
        "initial": {"side_to_move": "brancas", "turns_without_capture": 0, "pieces": pieces, "effects": effects},
        "moves": moves,
        "result": {"winner": "Brancas", "termination_reason": "fixture", "plies": plies, "final_hash": 123456789},
    }
    return Case(name, record)


def timed(fn: Callable[[], Any], repetitions: int = 30) -> float:
    values = []
    for _ in range(repetitions):
        start = time.perf_counter()
        fn()
        values.append(time.perf_counter() - start)
    return statistics.median(values) * 1_000_000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    cases = [make_case("short", 12, False), make_case("medium", 80, True), make_case("long", 320, True)]
    results = []
    for case in cases:
        pretty = json.dumps(case.record, ensure_ascii=False, indent=2).encode("utf-8")
        compact = json.dumps(case.record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        compressed = gzip.compress(compact, compresslevel=9, mtime=0)
        row = {
            "case": case.name,
            "plies": case.record["result"]["plies"],
            "json_bytes": len(pretty),
            "compact_json_bytes": len(compact),
            "gzip_json_bytes": len(compressed),
            "json_to_gzip_ratio": len(compact) / len(compressed),
            "compact_json_dump_us": timed(lambda: json.dumps(case.record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))),
            "gzip_us": timed(lambda: gzip.compress(compact, compresslevel=9, mtime=0)),
            "gzip_decompress_us": timed(lambda: gzip.decompress(compressed)),
        }
        if msgpack is not None:
            packed = msgpack.packb(case.record, use_bin_type=True)
            row["msgpack_bytes"] = len(packed)
            row["msgpack_pack_us"] = timed(lambda: msgpack.packb(case.record, use_bin_type=True))
            row["msgpack_unpack_us"] = timed(lambda: msgpack.unpackb(packed, raw=False))
        results.append(row)

    if args.json:
        print(json.dumps({"optional_msgpack": msgpack is not None, "results": results}, indent=2))
        return

    print("RedWar replay representation benchmark")
    print("msgpack available:", msgpack is not None)
    print()
    for row in results:
        print(f"{row['case']:>6}: {row['plies']:>4} plies | JSON {row['json_bytes']:>7} B | compact {row['compact_json_bytes']:>7} B | gzip {row['gzip_json_bytes']:>6} B")
        if "msgpack_bytes" in row:
            print(f"         msgpack {row['msgpack_bytes']:>6} B")
        print(f"         bytes/ply (gzip): {row['gzip_json_bytes'] / row['plies']:.2f}")
        print(f"         dump/pack µs: JSON {row['compact_json_dump_us']:.2f} | gzip {row['gzip_us']:.2f} | gunzip {row['gzip_decompress_us']:.2f}")
        if "msgpack_bytes" in row:
            print(f"         msgpack µs: pack {row['msgpack_pack_us']:.2f} | unpack {row['msgpack_unpack_us']:.2f}")
        print()


if __name__ == "__main__":
    main()
