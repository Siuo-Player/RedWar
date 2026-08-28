"""Safe cleanup for developer replay junk produced by manual testing.

Only ``data/replays/dev_ui`` is touched. Canonical replay archives remain
append-only and are never rewritten by this cleanup.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _is_zero_ply_record(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and isinstance(value.get("moves"), list)
        and len(value["moves"]) == 0
        and isinstance(value.get("result"), dict)
        and int(value["result"].get("plies", -1)) == 0
    )


def cleanup_zero_ply_dev_replays(root: Path | str) -> int:
    """Remove zero-ply canonical records accidentally written to DEV replay files.

    Supports both a normal JSON object and newline-delimited replay records.
    Schema-v2 developer UI sessions are preserved unchanged.
    Returns the number of zero-ply records removed.
    """
    root = Path(root)
    if not root.exists():
        return 0

    removed = 0
    for path in root.glob("*.json"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue

        # Normal DEV UI schema-v2 file: preserve intact.
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = None

        if isinstance(payload, dict):
            if _is_zero_ply_record(payload):
                path.unlink(missing_ok=True)
                removed += 1
            continue

        kept: list[str] = []
        changed = False
        for line in text.splitlines(keepends=True):
            if not line.strip():
                kept.append(line)
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                kept.append(line)
                continue
            if _is_zero_ply_record(item):
                removed += 1
                changed = True
                continue
            kept.append(line)

        if changed:
            if any(line.strip() for line in kept):
                path.write_text("".join(kept), encoding="utf-8")
            else:
                path.unlink(missing_ok=True)

    return removed
