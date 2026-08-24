from __future__ import annotations

import subprocess
from pathlib import Path

from engine.game_state import GameState
from engine.pieces import criar_peca_por_nome

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "cpp_make_unmake_bridge_test.exe"


def put(gs: GameState, row: int, col: int, name: str, team: str, *, stun: int = 0, lifespan=None, cooldown: int = 0) -> None:
    piece = criar_peca_por_nome(name, team)
    piece.stun_timer = stun
    piece.lifespan = lifespan
    piece.spawn_cooldown = cooldown
    gs.board[row][col] = piece


def actions_for(gs: GameState) -> list[dict]:
    actions: list[dict] = []
    current_team = "brancas" if gs.white_to_move else "pretas"

    for r in range(8):
        for c in range(8):
            piece = gs.board[r][c]
            if not piece or piece.team != current_team or not piece.can_act():
                continue

            for end in piece.get_valid_moves(r, c, gs.board, gs.tile_effects):
                actions.append({"type": "move", "start": (r, c), "end": end})
            for end in piece.get_valid_attacks(r, c, gs.board, gs.tile_effects):
                actions.append({"type": "attack", "start": (r, c), "end": end})

            for end, info in piece.get_valid_stuns(r, c, gs.board, gs.tile_effects).items():
                if info.get("has_enemy"):
                    actions.append({"type": "stun", "start": (r, c), "end": end, "area": info.get("aoe", [])})

            for spawn_r, spawn_c, spawn_name in piece.get_valid_spawns(r, c, gs.board, gs.tile_effects):
                actions.append(
                    {
                        "type": "spawn",
                        "start": (r, c),
                        "end": (spawn_r, spawn_c),
                        "spawn_name": spawn_name,
                    }
                )

            for spell in piece.get_valid_spells(r, c, gs.board, gs.tile_effects):
                if isinstance(spell, dict):
                    target = spell.get("target", (r, c))
                    spell_name = spell.get("spell_type")
                else:
                    target = spell[0:2]
                    spell_name = spell[2] if len(spell) >= 3 else None
                if spell_name:
                    actions.append(
                        {
                            "type": "spell",
                            "start": (r, c),
                            "end": tuple(target),
                            "spell_name": spell_name,
                        }
                    )

    return actions


def move_text(action: dict) -> str:
    sr, sc = action["start"]
    er, ec = action["end"]
    origin = f"{chr(ord('A') + sc)}{8 - sr}"
    target = f"{chr(ord('A') + ec)}{8 - er}"
    action_type = action["type"].upper()

    if action_type == "SPAWN":
        return f"SPAWN {action['spawn_name']} {origin} {target}"
    if action_type == "SPELL":
        return f"SPELL {action['spell_name']} {origin} {target}"
    return f"{action_type} {origin} {target}"


def make_cases() -> list[tuple[str, GameState]]:
    cases: list[tuple[str, GameState]] = []

    move = GameState()
    put(move, 6, 0, "Bone", "brancas")
    cases.append(("move", move))

    attack = GameState()
    put(attack, 4, 4, "Templar", "brancas")
    put(attack, 4, 5, "Bone", "pretas")
    cases.append(("attack", attack))

    stun = GameState()
    put(stun, 4, 4, "FrostMage", "brancas")
    put(stun, 3, 4, "Bone", "pretas")
    cases.append(("stun", stun))

    spawn = GameState()
    put(spawn, 4, 4, "Lich", "brancas")
    cases.append(("spawn", spawn))

    ignite = GameState()
    put(ignite, 4, 4, "Pyromancer", "brancas")
    cases.append(("spell", ignite))

    purify = GameState()
    put(purify, 4, 4, "Cleric", "brancas")
    put(purify, 3, 3, "Templar", "brancas", stun=2)
    cases.append(("spell-purify", purify))

    swap = GameState()
    put(swap, 4, 4, "Trickster", "brancas")
    put(swap, 2, 4, "Templar", "brancas")
    cases.append(("spell-swap", swap))

    barricade = GameState()
    put(barricade, 4, 4, "Geomancer", "brancas")
    cases.append(("spell-barricade", barricade))

    return cases


def test_python_cpp_make_unmake_equivalence():
    assert BRIDGE.exists(), f"C++ bridge binary missing: {BRIDGE}. Run build_cpp_engine.py --bridge-test."

    requests: list[tuple[str, str, str]] = []
    found_types: set[str] = set()

    for label, state in make_cases():
        legal_actions = actions_for(state)
        assert legal_actions, f"{label}: expected at least one legal action"

        preferred = [a for a in legal_actions if a["type"] not in found_types]
        action = preferred[0] if preferred else legal_actions[0]
        found_types.add(action["type"])

        python_after = state.fast_clone()
        python_after.execute_action(action)
        requests.append((label, state.to_rwen(), move_text(action)))
        expected_after = python_after.to_rwen()
        requests[-1] = (label, requests[-1][1], requests[-1][2] + "\n" + expected_after)

    payload = "".join(f"{rwen}\n{move}\n" for _, rwen, move_with_expected in requests for move, _ in [move_with_expected.split("\n", 1)])
    result = subprocess.run(
        [str(BRIDGE)],
        input=payload,
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    lines = [line for line in result.stdout.splitlines() if line]
    assert len(lines) == len(requests) * 2

    for index, (label, _rwen, move_with_expected) in enumerate(requests):
        _move, expected_after = move_with_expected.split("\n", 1)
        actual_after = lines[index * 2]
        restored = lines[index * 2 + 1]

        assert actual_after.startswith("AFTER "), f"{label}: malformed C++ output: {actual_after}"
        assert restored.startswith("RESTORED "), f"{label}: malformed C++ restore output: {restored}"
        assert actual_after.removeprefix("AFTER ") == expected_after, (
            f"{label}: Python/C++ state mismatch after {_move}\n"
            f"Python: {expected_after}\n"
            f"C++:    {actual_after.removeprefix('AFTER ')}"
        )

    assert {"move", "attack", "stun", "spawn", "spell"}.issubset(found_types), found_types
