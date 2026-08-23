from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

POSITIONS = [
    "B:Sentry_0_N_0,.,.,.,B:Ranger_0_N_0,.,.,./.,B:Phantom_0_N_0,.,.,.,.,B:FrostMage_0_N_0,./.,.,.,B:Templar_0_N_0,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,W:Templar_0_N_0,.,.,.,W:Phantom_0_N_0,./.,W:FrostMage_0_N_0,.,.,.,.,W:Ranger_0_N_0,./W:Sentry_0_N_0,.,.,.,W:Inquisitor_0_N_0,.,.,.,. W 0",
    "W:FrostMage_1_N_0,B:Bone_2_N_0,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,W:BoneLord_0_N_0,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,B:Phantom_0_N_0,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,. B 17",
    "W:Sentry_0_N_0,.,.,.,B:FrostMage_0_N_0,.,.,.,./.,W:Templar_2_N_0,.,.,.,.,.,./.,.,B:Phantom_0_N_0,.,.,.,.,./.,.,.,.,W:Lich_0_N_0,.,.,.,./.,.,.,.,.,B:BoneLord_0_N_0,.,.,./.,W:Ranger_0_N_0,.,.,.,.,.,.,./.,.,.,.,.,.,.,./B:Sentry_0_N_0,.,.,.,W:Inquisitor_0_N_0,.,.,.,. W 23",
]

def classical_eval(engine: Path, rwen: str) -> int:
    proc = subprocess.run([str(engine)], input=f"position rwen {rwen}\neval classical\nquit\n", text=True, capture_output=True, cwd=engine.parent, check=True)
    for line in proc.stdout.splitlines():
        if line.startswith("info score classical "):
            return int(line.rsplit(" ", 1)[1])
    raise RuntimeError(f"engine did not return a classical score: {proc.stdout!r}")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    engine = args.engine.resolve()
    rows = [{"rwen": rwen, "score": classical_eval(engine, rwen), "source": "classical-v1"} for rwen in POSITIONS]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    print(f"teacher_rows={len(rows)}")
    print(f"teacher_output={args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
