"""Developer entrypoint for instrumented manual RedWar games.

Run with:
    python tools/replay/dev_main.py

This imports the normal game and adds local observability plus the player-intent
interaction and hover-visualization policies. The ordinary ``python main.py``
path remains unchanged.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.replay.hover_visuals import install_hover_visuals
from main import JogoController
from tools.replay.cleanup import cleanup_zero_ply_dev_replays
from tools.replay.dev_ui import install_dev_replay
from tools.replay.interaction import install_intent_interaction


if __name__ == "__main__":
    removed = cleanup_zero_ply_dev_replays(ROOT / "data" / "replays" / "dev_ui")
    if removed:
        print(f"[DEV REPLAY] Removidos {removed} registos de 0 plies.")

    app = JogoController()
    install_hover_visuals(app)
    install_intent_interaction(app)
    install_dev_replay(app)
    app.run()
