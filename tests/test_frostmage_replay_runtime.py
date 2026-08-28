import json

from engine.game_state import GameState
from engine.pieces import FrostMage, Ranger
from tools.replay.storage import ReplayStore


def test_frostmage_nevada_does_not_require_enemy_and_ice_is_the_only_center_blocker():
    mage = FrostMage("brancas")
    board = [[None for _ in range(8)] for _ in range(8)]
    effects = [[None for _ in range(8)] for _ in range(8)]

    targets = {entry["target"] for entry in mage.get_valid_spells(4, 4, board, effects)}
    assert (4, 4) in targets
    assert (1, 4) in targets
    assert (0, 0) not in targets

    effects[5][4] = {"type": "ice", "timer": 3, "team": "brancas"}
    targets = {entry["target"] for entry in mage.get_valid_spells(4, 4, board, effects)}
    assert (5, 4) not in targets
    assert (4, 5) in targets


def test_live_completed_game_creates_replay_and_attempt_sidecar(tmp_path, monkeypatch):
    monkeypatch.setenv("REDWAR_REPLAY_DIR", str(tmp_path))

    gs = GameState()
    gs.board[7][0] = Ranger("brancas")
    gs.board[6][0] = Ranger("pretas")
    gs.compute_initial_hash()

    # This accepted real action captures the opponent and ends the game.
    gs.execute_action({"type": "attack", "start": (7, 0), "end": (6, 0)})

    recent = ReplayStore(tmp_path).recent()
    assert len(recent) == 1
    replay = recent[0]
    assert replay["result"]["winner"] is not None
    assert replay["moves"]

    sidecar = tmp_path / "diagnostics" / f"{replay['game_id']}.attempts.json"
    assert sidecar.is_file()
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["game_id"] == replay["game_id"]
    assert payload["attempts"]
    assert payload["attempts"][0]["outcome"] == "accepted"
