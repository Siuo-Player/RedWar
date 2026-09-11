"""Deterministic Ares tactical capability benchmark for Sprint 20."""
from __future__ import annotations

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.action_parser import ActionParser
from engine.actions import GameAction
from engine.game_state import GameState
from engine.legal_actions import resolve_legal_action
from engine.pieces import criar_peca_por_nome
from tools.analytics.frostmage_benchmark import FROST_CLUSTER

DEFAULT_ENGINE = ROOT / "ai" / "cpp_engine" / ("engine.exe" if sys.platform == "win32" else "engine")
DEFAULT_NODES = [10, 100, 1_000, 10_000, 100_000, 1_000_000]
REAL_GAME_ROOT = ROOT / "data" / "arena" / "strength"
REAL_GAME_FIXTURE = ROOT / "tests" / "fixtures" / "foundation-real-game-initial-rwen.txt"


@dataclass(frozen=True)
class TacticalCase:
    name: str
    description: str
    rwen: str
    expected_prefix: str
    coverage: str


_EMPTY = ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:."

CASES = {
    "frostmage-5-target": TacticalCase(
        "frostmage-5-target",
        "Five clustered enemies exercise the FrostMage STUN-capable tactical state.",
        FROST_CLUSTER,
        "STUN ",
        "STUN",
    ),
    "second-stun-lethal": TacticalCase(
        "second-stun-lethal",
        "A stunned enemy occupies FrostMage's D5 target square, making the next STUN lethal under the two-stun rule.",
        f"{_EMPTY}/{_EMPTY}/{_EMPTY}/W_FrostMage_0_N_0:.,.:.,B_Bone_1_N_0:.,.:.,.:.,.:.,.:./{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY} W 0",
        "STUN A5 D5",
        "SECOND_STUN_LETHAL",
    ),
    "high-value-capture": TacticalCase(
        "high-value-capture",
        "A Templar has an immediate high-value capture opportunity.",
        f"{_EMPTY}/{_EMPTY}/{_EMPTY}/.:.,.:.,.:.,.:.,B_Lich_0_N_0:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,W_Templar_0_N_0:.,.:.,.:.,.:./{_EMPTY}/{_EMPTY}/{_EMPTY} W 0",
        "ATTACK E4 E5",
        "HIGH_VALUE_CAPTURE",
    ),
    "ranged-spell": TacticalCase(
        "ranged-spell",
        "A Ranger has a declared aimed-shot spell against a distant target.",
        f"{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY}/.:.,.:.,.:.,.:.,W_Ranger_0_N_0:.,.:.,B_Obelisk_0_N_0:.,.:./{_EMPTY}/{_EMPTY}/{_EMPTY} W 0",
        "SPELL aimed_shot E4 G4",
        "SPELL",
    ),
    "defensive-purify": TacticalCase(
        "defensive-purify",
        "A Cleric can purge a stunned allied Templar; the reference action is capability evidence, not a strength claim.",
        f"{_EMPTY}/.:.,B_Obelisk_0_N_0:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./{_EMPTY}/.:.,.:.,.:.,W_Templar_2_N_0:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,W_Cleric_0_N_0:.,.:.,.:.,.:./{_EMPTY}/{_EMPTY}/{_EMPTY} W 0",
        "SPELL purify E4 D5",
        "DEFENSE",
    ),
    "lifespan-cooldown": TacticalCase(
        "lifespan-cooldown",
        "A Lich with an available spawn path exercises lifecycle/cooldown state handling.",
        f"{_EMPTY}/.:.,.:.,.:.,B_Bone_1_1_3:.,.:.,.:.,.:.,.:./{_EMPTY}/.:.,.:.,.:.,.:.,W_Lich_0_N_0:.,.:.,.:.,.:./{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY} W 0",
        "SPAWN Ghoul E5 ",
        "LIFESPAN_COOLDOWN",
    ),
    "twc-capture": TacticalCase(
        "twc-capture",
        "A capture is available immediately before the TWC terminal boundary.",
        f"{_EMPTY}/{_EMPTY}/{_EMPTY}/.:.,.:.,.:.,B_Lich_0_N_0:.,.:.,.:.,.:.,.:./.:.,.:.,.:.,.:.,W_Templar_0_N_0:.,.:.,.:.,.:./{_EMPTY}/{_EMPTY}/{_EMPTY} W 49",
        "ATTACK E4 D5",
        "TWC",
    ),
}


def _validate_rwen(rwen: str) -> None:
    parts = rwen.split()
    if len(parts) != 3:
        raise ValueError("RWEN must contain board, side-to-move and TWC fields")
    board_text, turn, twc = parts
    rows = board_text.split("/")
    if len(rows) != 8:
        raise ValueError(f"RWEN must contain 8 rows, got {len(rows)}")
    for index, row in enumerate(rows):
        cells = row.split(",")
        if len(cells) != 8:
            raise ValueError(f"RWEN row {index} must contain 8 cells, got {len(cells)}")
        for cell in cells:
            if ":" not in cell:
                raise ValueError(f"RWEN cell {cell!r} is missing piece:effect encoding")
    if turn not in {"W", "B"}:
        raise ValueError(f"Invalid side to move: {turn!r}")
    int(twc)


def _looks_like_rwen(value: str) -> bool:
    try:
        _validate_rwen(value)
    except (TypeError, ValueError):
        return False
    return True


def _iter_strings(value: Any):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _iter_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_strings(nested)
    elif isinstance(value, str) and _looks_like_rwen(value):
        yield value


def find_complete_game_rwen() -> str | None:
    """Find a valid RWEN actually preserved by the real-game evidence corpus."""
    if REAL_GAME_ROOT.is_dir():
        for path in sorted(REAL_GAME_ROOT.rglob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for candidate in _iter_strings(payload):
                return candidate
    if REAL_GAME_FIXTURE.is_file():
        for line in REAL_GAME_FIXTURE.read_text(encoding="utf-8").splitlines():
            candidate = line.strip()
            if candidate and not candidate.startswith("#") and _looks_like_rwen(candidate):
                return candidate
    return None


def _game_state_from_rwen(rwen: str) -> GameState:
    """Reconstruct enough Python state to validate an engine bestmove canonically."""
    _validate_rwen(rwen)
    board_text, turn, twc_text = rwen.split()
    state = GameState()
    state.white_to_move = turn == "W"
    state.turns_without_capture = int(twc_text)

    for row, row_text in enumerate(board_text.split("/")):
        for col, cell in enumerate(row_text.split(",")):
            token, _, effect_text = cell.partition(":")
            if token != ".":
                fields = token.split("_")
                if len(fields) != 5:
                    raise ValueError(f"Invalid piece token at {(row, col)}: {token!r}")
                team_code, hero_name, stun_text, lifespan_text, cooldown_text = fields
                team = "brancas" if team_code == "W" else "pretas"
                piece = criar_peca_por_nome(hero_name, team)
                piece.stun_timer = int(stun_text)
                piece.lifespan = 999 if lifespan_text == "N" else int(lifespan_text)
                piece.spawn_cooldown = int(cooldown_text)
                state.board[row][col] = piece

            if effect_text and effect_text != ".":
                effect_fields = effect_text.split("_")
                if len(effect_fields) != 3:
                    raise ValueError(f"Invalid effect token at {(row, col)}: {effect_text!r}")
                effect_team = "brancas" if effect_fields[0] == "W" else "pretas"
                state.tile_effects[row][col] = {
                    "team": effect_team,
                    "type": effect_fields[1],
                    "timer": int(effect_fields[2]),
                }

    state.compute_initial_hash()
    return state


def _canonical_bestmove(rwen: str, bestmove: str) -> GameAction:
    parsed = ActionParser.parse(bestmove)
    if parsed is None:
        raise ValueError(f"engine returned unparseable bestmove {bestmove!r}")

    state = _game_state_from_rwen(rwen)
    action_data: dict[str, Any] = {
        "type": parsed["action"].lower(),
        "start": ActionParser.alg_to_coords(parsed["origin"], 8),
        "end": ActionParser.alg_to_coords(parsed["target"], 8),
    }
    if "spell" in parsed:
        action_data["spell_name"] = parsed["spell"]
    if "hero" in parsed:
        action_data["spawn_name"] = parsed["hero"]

    action = GameAction.from_dict(action_data)
    return resolve_legal_action(state, action)


def query(engine: Path, rwen: str, nodes: int, trace_path: Path | None) -> tuple[str, float]:
    env = os.environ.copy()
    if trace_path is not None:
        trace_path.parent.mkdir(parents=True, exist_ok=True)
        env["ARES_SEARCH_TRACE_PATH"] = str(trace_path)
    else:
        env.pop("ARES_SEARCH_TRACE_PATH", None)
    proc = subprocess.Popen(
        [str(engine)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, cwd=ROOT, env=env,
    )
    start = time.perf_counter()
    responses: queue.Queue[str | None] = queue.Queue()

    def _read_stdout() -> None:
        assert proc.stdout is not None
        try:
            for raw_line in proc.stdout:
                responses.put(raw_line.strip())
        finally:
            responses.put(None)

    reader = threading.Thread(target=_read_stdout, name="tactical-engine-reader", daemon=True)
    reader.start()
    try:
        assert proc.stdin is not None
        proc.stdin.write("isready\n")
        proc.stdin.write(f"position rwen {rwen}\n")
        proc.stdin.write(f"go nodes {nodes}\n")
        proc.stdin.flush()
        deadline = time.monotonic() + 30.0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("engine did not return bestmove within 30 seconds")
            try:
                line = responses.get(timeout=min(remaining, 0.25))
            except queue.Empty:
                if proc.poll() is not None:
                    raise RuntimeError(f"engine exited before bestmove (returncode={proc.returncode})")
                continue
            if line is None:
                raise RuntimeError(f"engine stdout closed before bestmove (returncode={proc.poll()})")
            if line.startswith("bestmove"):
                return (line.split(" ", 1)[1] if " " in line else "0000", time.perf_counter() - start)
    finally:
        try:
            if proc.stdin is not None and proc.poll() is None:
                proc.stdin.write("quit\n")
                proc.stdin.flush()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def run_case(case: TacticalCase, engine: Path, budgets: list[int], trace: bool, strict_choice: bool) -> int:
    _validate_rwen(case.rwen)
    print(f"case={case.name} coverage={case.coverage}")
    print(f"description={case.description}")
    print(f"capability_reference={case.expected_prefix.rstrip()}")
    failures = 0
    trace_dir = ROOT / "logs" / "benchmarks" / "tactical" / case.name if trace else None
    for nodes in budgets:
        trace_path = trace_dir / f"trace_{nodes}.log" if trace_dir else None
        bestmove, elapsed = query(engine, case.rwen, nodes, trace_path)
        ok = bestmove != "0000"
        legality = "not-tested"
        if ok:
            try:
                canonical = _canonical_bestmove(case.rwen, bestmove)
                legality = canonical.type.value
            except (TypeError, ValueError) as exc:
                ok = False
                legality = f"invalid: {exc}"
        if strict_choice:
            ok = ok and bestmove.startswith(case.expected_prefix)
        failures += int(not ok)
        mode = "strict-choice" if strict_choice else "capability"
        print(
            f"nodes={nodes:>9} bestmove={bestmove:<28} time={elapsed:.3f}s "
            f"legal={legality} mode={mode} {'PASS' if ok else 'FAIL'}"
        )
        if trace_path is not None:
            print(f"  trace={trace_path}")
    print(f"failure_threshold: {failures}/{len(budgets)} tested budgets failed")
    return failures


def run_complete_game_probe(engine: Path, nodes: int, trace: bool) -> int:
    rwen = find_complete_game_rwen()
    if rwen is None:
        raise RuntimeError("No valid RWEN state was found in data/arena/strength or its preserved real-game fixture")
    trace_path = ROOT / "logs" / "benchmarks" / "tactical" / "complete-game-corpus" / f"trace_{nodes}.log" if trace else None
    bestmove, elapsed = query(engine, rwen, nodes, trace_path)
    ok = bestmove != "0000"
    legality = "not-tested"
    if ok:
        try:
            canonical = _canonical_bestmove(rwen, bestmove)
            legality = canonical.type.value
        except (TypeError, ValueError) as exc:
            ok = False
            legality = f"invalid: {exc}"
    print("case=complete-game-corpus coverage=COMPLETE_GAME_STATE")
    print(f"nodes={nodes:>9} bestmove={bestmove:<28} time={elapsed:.3f}s legal={legality} {'PASS' if ok else 'FAIL'}")
    if trace_path is not None:
        print(f"  trace={trace_path}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic Ares tactical capability benchmark")
    parser.add_argument("--engine", default=str(DEFAULT_ENGINE))
    parser.add_argument("--case", action="append", choices=sorted(CASES), default=None)
    parser.add_argument("--nodes", type=int, action="append", default=None)
    parser.add_argument("--complete-game-probe", action="store_true")
    parser.add_argument("--complete-game-nodes", type=int, default=1_000)
    parser.add_argument("--strict-choice", action="store_true", help="Require the reference bestmove; this is strength-style evidence and is not enabled by default")
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    engine = Path(args.engine).resolve()
    if not engine.is_file():
        raise FileNotFoundError(f"Engine não encontrada: {engine}")
    budgets = args.nodes if args.nodes else DEFAULT_NODES
    if any(value <= 0 for value in budgets):
        parser.error("--nodes deve conter apenas inteiros positivos")
    selected = args.case if args.case else sorted(CASES)
    failures = sum(run_case(CASES[name], engine, budgets, args.trace, args.strict_choice) for name in selected)
    if args.complete_game_probe:
        failures += run_complete_game_probe(engine, args.complete_game_nodes, args.trace)
    print(f"suite: {len(selected)} tactical case(s), {len(budgets)} budget(s) each")
    if args.complete_game_probe:
        print("complete-game probe: enabled")
    print(f"choice mode: {'strict' if args.strict_choice else 'capability'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
