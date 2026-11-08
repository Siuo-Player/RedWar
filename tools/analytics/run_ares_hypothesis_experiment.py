"""CLI runner for empirical Ares hypothesis experiments (Stockfish Fishtest model).

Usage:
    python tools/analytics/run_ares_hypothesis_experiment.py [--pairs 4] [--output-dir docs/EXPERIMENTS]
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from ai.ares2 import AresEngine
from ai.ares_hypothesis_testing import AresHypothesisTester, Hypothesis
from ai.sprt import SPRTConfig


class AresBotWrapper:
    """Wrapper exposing standard .play(game_state) for Ares search engine."""

    def __init__(self, name: str, depth: int = 2, time_limit: float = 0.6):
        self.nome = name
        self.depth = depth
        self.time_limit = time_limit
        self.engine = AresEngine()

    def play(self, game_state):
        return self.engine.choose_best_move(game_state, max_depth=self.depth, time_limit=self.time_limit)


def main():
    parser = argparse.ArgumentParser(description="Run an automated hypothesis duel for Ares AI.")
    parser.add_argument("--pairs", type=int, default=4, help="Number of mirror pairs (default: 4 = 8 games)")
    parser.add_argument("--output-dir", type=str, default="docs/EXPERIMENTS", help="Output directory for reports")
    parser.add_argument("--id", type=str, default="H-20261108-ARES-COUNTERMOVE-TT-DELTAPRUNING", help="Hypothesis ID")
    parser.add_argument(
        "--title",
        type=str,
        default="Countermove Heuristic, Generational TT Replacement & Quiescence Delta Pruning",
        help="Hypothesis title",
    )
    parser.add_argument(
        "--bottleneck",
        type=str,
        default="Subtree search bloat on quiet refutations, collision evictions of deep TT entries across plies, and futile tactical captures in quiescence.",
        help="Hypothesis bottleneck",
    )
    parser.add_argument(
        "--proposed-heuristic",
        type=str,
        default="Countermove Heuristic (+19k priority), Generational TT Aging, Quiescence Delta Pruning (65 cp), Reverse Futility Pruning (depth 1-2), and Sniper Line-of-Sight Crosshairs.",
        help="Proposed heuristic",
    )
    args = parser.parse_args()

    hypothesis = Hypothesis(
        id=args.id,
        title=args.title,
        bottleneck=args.bottleneck,
        proposed_heuristic=args.proposed_heuristic,
        baseline_version="ares-depth1-baseline",
        candidate_version="ares-countermove-ttaging-d2",
        target_elo_gain=25.0,
    )

    print(f"🚀 Iniciando Experimento de Hipótese: {hypothesis.id}")
    print(f"📌 Título: {hypothesis.title}")
    print(f"🎯 Pares Pareados: {args.pairs} ({args.pairs * 2} partidas no total)")

    challenger = AresBotWrapper("Ares_Challenger_D2", depth=2, time_limit=0.60)
    baseline = AresBotWrapper("Ares_Baseline_D1", depth=1, time_limit=0.15)

    tester = AresHypothesisTester(SPRTConfig(elo0=0.0, elo1=15.0))

    def on_pair_done(idx, record):
        print(f"  ✅ Par #{idx + 1:02d} concluído: Seed={record['seed']} | LLR={record['current_llr']:+.2f} | Score={record['challenger_pair_score']}/2.0")

    result = tester.run_hypothesis_duel(
        hypothesis=hypothesis,
        challenger_bot=challenger,
        baseline_bot=baseline,
        num_pairs=args.pairs,
        on_pair_completed=on_pair_done,
        early_stopping=False,
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / f"{hypothesis.id}.json"
    md_path = out_dir / f"{hypothesis.id}.md"

    tester.save_report_json(result, json_path)
    md_report = tester.format_markdown_report(result)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    print("\n" + "=" * 60)
    print(f"📊 Relatório gerado: {md_path}")
    print(f"📁 JSON salvo: {json_path}")
    print(f"🏆 Veredito 3-Sigma: {result.verdict}")
    print(f"📈 Delta Elo: {result.delta_elo:+.1f} [95% CI: {result.ci_lower:+.1f}, {result.ci_upper:+.1f}]")
    print(f"🛡️ 3.0σ Lower Bound: {result.ci_lower_3sigma:+.1f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
