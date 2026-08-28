"""Developer entrypoint for instrumented manual RedWar games.

Run with:
    python tools/replay/dev_main.py

This imports the normal game and adds local observability plus the player-intent
interaction policy. The ordinary ``python main.py`` path remains unchanged.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import JogoController
from tools.replay.dev_ui import install_dev_replay
from tools.replay.interaction import install_intent_interaction


if __name__ == "__main__":
    app = JogoController()
    install_intent_interaction(app)
    install_dev_replay(app)
    app.run()
