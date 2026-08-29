"""Developer entrypoint for instrumented manual RedWar games.

Run with:
    python tools/replay/dev_main.py

This imports the normal game and adds local observability plus the player-intent
interaction, hover-visualization and derived player telemetry policies. The
ordinary ``python main.py`` path remains unchanged.
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import JogoController
from tools.replay.cleanup import cleanup_zero_ply_dev_replays
from tools.replay.dev_ui import install_dev_replay
from tools.replay.dev_telemetry import install_runtime_telemetry
from tools.replay.hover_visuals import install_hover_visuals
from tools.replay.interaction import install_intent_interaction
from tools.telemetry.runtime import TelemetryRecorder
from tools.telemetry import TelemetryStore


def _build_commit() -> str:
    value = os.environ.get("GITHUB_SHA")
    if value:
        return value
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


if __name__ == "__main__":
    removed = cleanup_zero_ply_dev_replays(ROOT / "data" / "replays" / "dev_ui")
    if removed:
        print(f"[DEV REPLAY] Removidos {removed} registos de 0 plies.")

    app = JogoController()
    install_hover_visuals(app)
    install_intent_interaction(app)
    install_dev_replay(app)

    session_id = uuid.uuid4().hex
    telemetry_path = ROOT / "data" / "replays" / "telemetry" / f"{session_id}.jsonl"
    build_commit = _build_commit()
    recorder = TelemetryRecorder(
        TelemetryStore(telemetry_path),
        session_id=session_id,
        provenance={
            "rules_version": build_commit,
            "engine_version": build_commit,
            "ui_schema_version": "battle-sidebar-v1",
            "build_commit": build_commit,
        },
    )
    install_runtime_telemetry(app, recorder)

    try:
        app.run()
    finally:
        game_id = getattr(app.gs, "game_id", None)
        if getattr(app, "fase_atual", None) == "BATALHA" and game_id is not None:
            recorder.battle_finished(
                game_id=game_id,
                result=getattr(app.gs, "winner", None),
            )
        recorder.session_finished()
