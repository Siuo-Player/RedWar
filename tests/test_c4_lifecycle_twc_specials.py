from __future__ import annotations

import os
import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

ROOT = Path(__file__).resolve().parents[1]
BRIDGE_NAME = "cpp_make_unmake_bridge_test.exe" if os.name == "nt" else "cpp_make_unmake_bridge_test"
BRIDGE = ROOT / BRIDGE_NAME


def put(gs: GameState, row: int, col: int, name: str, team: str, *, stun: int = 0, lifespan=None, cooldown: int = 0) -> None:
    piece = criar_peca_por_nome(name, team)
    piece.stun_timer = stun
    piece.lifespan = lifespan
    piece.spawn_cooldown = cooldown
    gs.board[row][col] = piece


def run_bridge(rwen: str, move: str) -> tuple[str, str]:
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}"
    result = subprocess.run(
        [str(BRIDGE)],
        input=f"{rwen}\n{move}\n",
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    lines = [line for line in result.stdout.splitlines() if line]
    assert len(lines) == 2, lines
    return lines[0], lines[1]


def move_text(action: dict) -> str:
    sr, sc = action["start"]
    er, ec = action["end"]
    origin = f"{chr(ord('A') + sc)}{8 - sr}"
    target = f"{chr(ord('A') + ec)}{8 - er}"
    action_type = action["type"].upper()
    if action_type == "SPELL":
        return f"SPELL {action['spell_name']} {origin} {target}"
    return f"{action_type} {origin} {target}"


def test_attack_capture_of_temporary_piece_preserves_twc():
    state = GameState()
    put(state, 4, 4, "Templar", "brancas")
    put(state, 4, 5, "Bone", "pretas", lifespan=5)
    state.turns_without_capture = 7
    state.compute_initial_hash()

    action = {"type": "attack", "start": (4, 4), "end": (4, 5)}
    after = state.fast_clone()
    after.execute_action(action)

    assert after.turns_without_capture == 8
    assert after.board[4][5] is not None and after.board[4][5].name == "Templar"

    actual, restored = run_bridge(state.to_rwen(), move_text(action))
    assert actual.removeprefix("AFTER ") == after.to_rwen()
    assert restored.removeprefix("RESTORED ") == state.to_rwen()


def test_stun_capture_of_temporary_piece_preserves_twc():
    state = GameState()
    put(state, 4, 4, "FrostMage", "brancas")
    put(state, 3, 4, "Bone", "pretas", stun=1, lifespan=5)
    state.turns_without_capture = 7
    state.compute_initial_hash()

    action = {
        "type": "stun",
        "start": (4, 4),
        "end": (3, 4),
        "area": [(3, 4)],
    }

    after = state.fast_clone()
    after.execute_action(action)
    assert after.turns_without_capture == 8
    assert after.board[3][4] is None

    actual, restored = run_bridge(state.to_rwen(), move_text(action))
    assert actual.removeprefix("AFTER ") == after.to_rwen()
    assert restored.removeprefix("RESTORED ") == state.to_rwen()


def test_timer_lifecycle_and_effect_expiry_match():
    state = GameState()
    put(state, 6, 0, "Bone", "brancas")
    put(state, 1, 7, "Ranger", "pretas", stun=2, lifespan=2, cooldown=3)
    state.tile_effects[1][6] = {"type": "fire", "timer": 1, "team": "pretas"}
    state.tile_effects[1][5] = {"type": "ice", "timer": 2, "team": "brancas"}
    state.turns_without_capture = 11
    state.compute_initial_hash()

    action = {"type": "move", "start": (6, 0), "end": (5, 0)}
    after = state.fast_clone()
    after.execute_action(action)

    ranger = after.board[1][7]
    assert ranger is not None
    assert ranger.stun_timer == 1
    assert ranger.lifespan == 1
    assert ranger.spawn_cooldown == 2
    assert after.tile_effects[1][6] is None
    assert after.tile_effects[1][5] == {"type": "ice", "timer": 2, "team": "brancas"}

    actual, restored = run_bridge(state.to_rwen(), move_text(action))
    assert actual.removeprefix("AFTER ") == after.to_rwen()
    assert restored.removeprefix("RESTORED ") == state.to_rwen()


def test_lifespan_expiry_can_create_python_terminal_state_and_matches_cpp_state():
    state = GameState()
    put(state, 6, 0, "Bone", "brancas")
    put(state, 1, 7, "StoneWall", "pretas", lifespan=1)
    state.compute_initial_hash()

    action = {"type": "move", "start": (6, 0), "end": (5, 0)}
    after = state.fast_clone()
    after.execute_action(action)

    assert all(piece is None or piece.team != "pretas" for row in after.board for piece in row)
    assert after.game_over
    assert after.winner == "Aniquilação (Brancas Vencem)"

    actual, restored = run_bridge(state.to_rwen(), move_text(action))
    assert actual.removeprefix("AFTER ") == after.to_rwen()
    assert restored.removeprefix("RESTORED ") == state.to_rwen()


def test_special_attack_spells_round_trip():
    cases = [
        ("Phantom", (2, 5), "spectral_strike"),
        ("Ranger", (4, 6), "aimed_shot"),
        ("Sentry", (4, 5), "sentinel_shot"),
    ]

    for index, (hero, target, spell_name) in enumerate(cases):
        state = GameState()
        put(state, 4, 4, hero, "brancas")
        put(state, target[0], target[1], "Bone", "pretas")
        state.turns_without_capture = 4 + index
        state.compute_initial_hash()

        action = {"type": "spell", "start": (4, 4), "end": target, "spell_name": spell_name}
        after = state.fast_clone()
        after.execute_action(action)

        assert after.board[target[0]][target[1]] is None
        actual, restored = run_bridge(state.to_rwen(), move_text(action))
        assert actual.removeprefix("AFTER ") == after.to_rwen(), spell_name
        assert restored.removeprefix("RESTORED ") == state.to_rwen(), spell_name
