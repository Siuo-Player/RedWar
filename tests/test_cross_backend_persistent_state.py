from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from tests.test_cross_backend_make_unmake import actions_for, make_cases, move_text

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_make_unmake_bridge_test.exe" if os.name == "nt" else "cpp_make_unmake_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME


def _select_action_types(state: GameState) -> list[dict]:
    selected: dict[str, dict] = {}
    for action in actions_for(state):
        selected.setdefault(action["type"], action)
    return list(selected.values())


def test_python_cpp_targeted_action_taxonomy_roundtrip():
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --bridge-test."

    requests = []
    found: set[str] = set()
    for label, state in make_cases():
        for action in _select_action_types(state):
            action_type = action["type"]
            if action_type in found:
                continue
            before = state.to_rwen()
            after = state.fast_clone()
            after.execute_action(action)
            requests.append((label, action_type, before, move_text(action), after.to_rwen()))
            found.add(action_type)

    required = {"move", "attack", "spawn", "spell"}
    assert required.issubset(found), found
    assert "stun" in found or "nevada" in {r[1] for r in requests}

    payload = "".join(f"{rwen}\n{move}\n" for _label, _type, rwen, move, _expected in requests)
    result = subprocess.run([str(BRIDGE)], input=payload, text=True, capture_output=True, cwd=ROOT, check=False)
    assert result.returncode == 0, result.stderr or result.stdout

    lines = [line for line in result.stdout.splitlines() if line]
    assert len(lines) == len(requests) * 2
    for index, (label, action_type, rwen, move, expected_after) in enumerate(requests):
        actual_after = lines[index * 2]
        restored = lines[index * 2 + 1]
        context = f"{label} type={action_type} move={move}"
        assert actual_after.removeprefix("AFTER ") == expected_after, context
        assert restored.removeprefix("RESTORED ") == rwen, context


def test_python_cpp_persistent_state_fields_survive_transition_roundtrip():
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --bridge-test."

    crafted = GameState()
    label_state = [
        (6, 0, "Ghoul", "brancas", 0, 4, 0),
        (5, 3, "Ranger", "brancas", 0, 7, 2),
        (2, 4, "Bone", "pretas", 1, 12, 0),
    ]
    from engine.pieces import criar_peca_por_nome
    for r, c, name, team, stun, lifespan, cooldown in label_state:
        piece = criar_peca_por_nome(name, team)
        piece.stun_timer = stun
        piece.lifespan = lifespan
        piece.spawn_cooldown = cooldown
        crafted.board[r][c] = piece
    crafted.turns_without_capture = 7
    crafted.white_to_move = True

    legal = actions_for(crafted)
    assert legal
    action = legal[0]
    before = crafted.to_rwen()
    after = crafted.fast_clone()
    after.execute_action(action)

    result = subprocess.run(
        [str(BRIDGE)],
        input=f"{before}\n{move_text(action)}\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    lines = [line for line in result.stdout.splitlines() if line]
    assert len(lines) == 2
    assert lines[0].removeprefix("AFTER ") == after.to_rwen()
    assert lines[1].removeprefix("RESTORED ") == before
