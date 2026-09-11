from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENGINE = ROOT / "ai" / "cpp_engine" / "engine.exe"
DEFAULT_NODES = [100000]
_EMPTY = ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:."


@dataclass(frozen=True)
class TacticalCase:
    name: str
    description: str
    rwen: str
    expected: str
    category: str


CASES = {
    "capture": TacticalCase(
        "capture",
        "A basic adjacent capture must remain represented in the capability corpus.",
        f"{_EMPTY}/W_Ranger_0_N_0:.,.:.,.:.,.:.,.:.,.:.,.:./{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY} W 0",
        "MOVE A2 B2",
        "CAPTURE",
    ),
    "stun": TacticalCase(
        "stun",
        "A FrostMage must expose a legal STUN capability against an adjacent target.",
        f"{_EMPTY}/{_EMPTY}/W_FrostMage_0_N_0:.,B_Bone_1_N_0:.,.:.,.:.,.:.,.:./{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY} W 0",
        "STUN A3 B3",
        "STUN",
    ),
    "second-stun-lethal": TacticalCase(
        "second-stun-lethal",
        "A stunned enemy occupies FrostMage's D5 target square, making the next STUN lethal under the two-stun rule.",
        f"{_EMPTY}/{_EMPTY}/{_EMPTY}/W_FrostMage_0_N_0:.,.:.,B_Bone_1_N_0:.,.:.,.:.,.:.,.:./{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY} W 0",
        "STUN A5 D5",
        "SECOND_STUN_LETHAL",
    ),
    "fire-ice": TacticalCase(
        "fire-ice",
        "Fire and ice interaction remains represented as capability evidence.",
        f"{_EMPTY}/W_FrostMage_0_N_0:.,.:.,B_Bone_1_N_0:.,.:.,.:.,.:.,.:./{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY} W 0",
        "STUN A2 C2",
        "ELEMENTAL",
    ),
    "passive": TacticalCase(
        "passive",
        "Passive-driven board state remains in the corpus.",
        f"{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY}/W_Templar_2_N_0:.,.:.,B_Obelisk_0_N_0:.,.:.,.:.,.:.,.:./{_EMPTY}/{_EMPTY}/{_EMPTY} W 0",
        "MOVE A5 B5",
        "PASSIVE",
    ),
    "lifespan-cooldown": TacticalCase(
        "lifespan-cooldown",
        "Lifespan and cooldown state remain represented in tactical capability evidence.",
        f"{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY}/{_EMPTY}/W_Ranger_0_N_0:.,.:.,.:.,.:.,.:.,.:.,.:./{_EMPTY}/{_EMPTY} W 0",
        "WAIT",
        "STATE",
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
}


def run_case(case: TacticalCase, engine: Path, budgets: list[int], trace: bool, strict_choice: bool) -> int:
    failures = 0
    for nodes in budgets:
        cmd = [str(engine), "--rwen", case.rwen, "--nodes", str(nodes), "--bestmove"]
        if trace:
            cmd.append("--trace")
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[{case.name}] engine failed at {nodes} nodes", file=sys.stderr)
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            failures += 1
            continue
        bestmove = next((line.split(":", 1)[1].strip() for line in result.stdout.splitlines() if line.startswith("bestmove:")), "")
        if not bestmove:
            print(f"[{case.name}] missing bestmove", file=sys.stderr)
            failures += 1
            continue
        if strict_choice and bestmove != case.expected:
            print(f"[{case.name}] expected {case.expected}, got {bestmove}", file=sys.stderr)
            failures += 1
    return failures


def run_complete_game_probe(engine: Path, nodes: int, trace: bool) -> int:
    cmd = [str(engine), "--self-play", "--nodes", str(nodes)]
    if trace:
        cmd.append("--trace")
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print("[complete-game] probe failed", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        return 1
    return 0


def _validate_rwen(rwen: str) -> None:
    rows = rwen.split("/")
    if len(rows) < 2:
        raise ValueError("RWEN must contain board rows and metadata")
    for index, row in enumerate(rows[:-1]):
        cells = row.split(",")
        if len(cells) != 8:
            raise ValueError(f"RWEN row {index} must contain 8 cells, got {len(cells)}")


def validate_cases() -> None:
    for case in CASES.values():
        _validate_rwen(case.rwen)


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic tactical capability benchmark suite.")
    parser.add_argument("--engine", type=Path, default=DEFAULT_ENGINE)
    parser.add_argument("--nodes", type=int, nargs="+")
    parser.add_argument("--case", action="append")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--strict-choice", action="store_true")
    parser.add_argument("--complete-game-probe", action="store_true")
    parser.add_argument("--complete-game-nodes", type=int, default=250000)
    args = parser.parse_args()

    try:
        validate_cases()
    except ValueError as exc:
        parser.error(str(exc))

    engine = args.engine if args.engine.is_absolute() else ROOT / args.engine
    budgets = args.nodes if args.nodes else DEFAULT_NODES
    if any(value <= 0 for value in budgets):
        parser.error("--nodes deve conter apenas inteiros positivos")
    selected = args.case if args.case else sorted(CASES)
    unknown = sorted(set(selected) - set(CASES))
    if unknown:
        parser.error(f"casos desconhecidos: {', '.join(unknown)}")
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
