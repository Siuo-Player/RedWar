from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from tests.test_cross_backend_make_unmake import BRIDGE, actions_for, move_text, put

ROOT = Path(__file__).resolve().parents[1]


def _run_bridge(requests: list[tuple[str, str, str, str]]) -> list[str]:
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --bridge-test."
    payload = "".join(f"{rwen}\n{move}\n" for _label, rwen, move, _expected in requests)
    result = subprocess.run(
        [str(BRIDGE)],
        input=payload,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return [line for line in result.stdout.splitlines() if line]


def test_dragoon_jump_round_trips_through_both_backends():
    state = GameState()
    put(state, 4, 4, "Dragoon", "brancas")
    put(state, 4, 5, "Bone", "brancas")
    put(state, 2, 4, "Bone", "pretas")

    actions = [a for a in actions_for(state) if a["type"] == "spell" and a.get("spell_name") == "jump"]
    assert actions, "Dragoon fixture must expose a jump spell"
    action = actions[0]

    after = state.fast_clone()
    after.execute_action(action)
    requests = [("dragoon-jump", state.to_rwen(), move_text(action), after.to_rwen())]
    lines = _run_bridge(requests)

    assert len(lines) == 2
    assert lines[0].removeprefix("AFTER ") == after.to_rwen()
    assert lines[1].removeprefix("RESTORED ") == state.to_rwen()


def test_bonelord_on_kill_passive_round_trips_through_both_backends():
    state = GameState()
    put(state, 4, 4, "BoneLord", "brancas")
    put(state, 4, 5, "Bone", "pretas")

    actions = [a for a in actions_for(state) if a["type"] == "attack"]
    assert actions, "BoneLord fixture must expose an attack"
    action = actions[0]

    after = state.fast_clone()
    after.execute_action(action)
    spawned = after.board[4][5]
    assert spawned is not None and spawned.name == "Bone"
    requests = [("bonelord-on-kill", state.to_rwen(), move_text(action), after.to_rwen())]
    lines = _run_bridge(requests)

    assert len(lines) == 2
    assert lines[0].removeprefix("AFTER ") == after.to_rwen()
    assert lines[1].removeprefix("RESTORED ") == state.to_rwen()


def test_berserker_aoe_passive_round_trips_through_both_backends():
    state = GameState()
    put(state, 4, 4, "Berserker", "brancas")
    put(state, 4, 5, "Bone", "pretas")
    put(state, 3, 5, "Bone", "pretas")

    actions = [a for a in actions_for(state) if a["type"] == "attack"]
    assert actions, "Berserker fixture must expose an attack"
    action = actions[0]

    after = state.fast_clone()
    after.execute_action(action)
    assert after.board[3][5] is None, "Berserker AOE must hit the adjacent enemy"
    requests = [("berserker-aoe", state.to_rwen(), move_text(action), after.to_rwen())]
    lines = _run_bridge(requests)

    assert len(lines) == 2
    assert lines[0].removeprefix("AFTER ") == after.to_rwen()
    assert lines[1].removeprefix("RESTORED ") == state.to_rwen()
