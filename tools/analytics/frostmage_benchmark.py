"""Adversarial Ares benchmark for FrostMage tactical recognition."""
from __future__ import annotations
import argparse, os, subprocess, sys, time
from pathlib import Path
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_ENGINE = os.path.join(ROOT, "ai", "cpp_engine", "engine.exe" if sys.platform == "win32" else "engine")
DEFAULT_NODES = [10, 100, 1_000, 10_000, 100_000, 1_000_000, 10_000_000]
FROST_CLUSTER = (
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,B_Bone_0_N_0:.,.:.,.:.,.:./"
    "W_FrostMage_0_N_0:.,.:.,B_Bone_0_N_0:.,B_Bone_0_N_0:.,B_Bone_0_N_0:.,.:.,.:./"
    ".:.,.:.,B_Bone_0_N_0:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:./"
    ".:.,.:.,.:.,.:.,.:.,.:.,.:.,.:. W 0"
)

def query(engine: str, nodes: int, trace_path: Path | None = None):
    env=os.environ.copy()
    if trace_path is not None:
        trace_path.parent.mkdir(parents=True, exist_ok=True); env["ARES_SEARCH_TRACE_PATH"]=str(trace_path)
    else: env.pop("ARES_SEARCH_TRACE_PATH", None)
    proc=subprocess.Popen([engine],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,cwd=ROOT,env=env)
    try:
        assert proc.stdin is not None and proc.stdout is not None
        proc.stdin.write("isready\n"); proc.stdin.write(f"position rwen {FROST_CLUSTER}\n"); proc.stdin.write(f"go nodes {nodes}\n"); proc.stdin.flush()
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            line=proc.stdout.readline()
            if not line: break
            line=line.strip()
            if line.startswith("bestmove"): return (line.split(" ",1)[1] if " " in line else "0000",trace_path)
        raise TimeoutError("engine did not return bestmove within 30 seconds")
    finally:
        try:
            assert proc.stdin is not None; proc.stdin.write("quit\n"); proc.stdin.flush()
        except Exception: pass
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)

def main():
    parser=argparse.ArgumentParser(description="Diagnóstico táctico do FrostMage para Ares")
    parser.add_argument("--engine",default=DEFAULT_ENGINE); parser.add_argument("--nodes",type=int,action="append",default=None); parser.add_argument("--trace",action="store_true")
    args=parser.parse_args(); budgets=args.nodes if args.nodes else DEFAULT_NODES
    if any(n<=0 for n in budgets): parser.error("--nodes deve conter apenas inteiros positivos")
    if not os.path.isfile(args.engine): raise FileNotFoundError(f"Engine não encontrada: {args.engine}")
    trace_dir=Path(ROOT)/"logs"/"benchmarks"/"frostmage" if args.trace else None
    print("FrostMage tactical benchmark\nposition: 5 clustered enemies within one 3-range stun area\nexpected tactical class: STUN\nscan: exponential node budgets; use --nodes for fine-grained follow-up")
    if args.trace: print(f"trace directory: {trace_dir}")
    print()
    failures=0
    for nodes in budgets:
        trace_path=trace_dir/f"trace_{nodes}.log" if trace_dir else None; bestmove,saved=query(args.engine,nodes,trace_path); ok=bestmove.startswith("STUN "); failures += int(not ok)
        print(f"nodes={nodes:>10} bestmove={bestmove:<24} {'PASS' if ok else 'FAIL'}")
        if saved: print(f"  trace={saved}")
    print(f"\nthreshold scan: {len(budgets)} node budgets tested")
    if failures:
        print(f"DIAGNOSTIC: Ares failed to select the immediate 5-target FrostMage stun at {failures}/{len(budgets)} tested budgets."); return 1
    print("DIAGNOSTIC: Ares recognised the 5-target FrostMage stun at all budgets."); return 0
if __name__ == "__main__": raise SystemExit(main())
