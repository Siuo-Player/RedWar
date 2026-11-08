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

    def __init__(self, name: str, depth: int = 2, time_limit: float = 0.3):
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
    args = parser.parse_args()

    hypothesis = Hypothesis(
        id="H-20261108-ARES-ASPIRATION-PV",
        title="Aspiration Windows & PV Ordering vs Shallow Baseline",
        bottleneck="Shallow search horizons without aspiration windows risk tactical blindspots in stun windows.",
        proposed_heuristic="Iterative deepening with aspiration window (score +- 60) and PV move ordering bonus.",
        baseline_version="ares-depth1-baseline",
        candidate_version="ares-depth2-aspiration-challenger",
        target_elo_gain=25.0,
    )

    print(f"🚀 Iniciando Experimento de Hipótese: {hypothesis.id}")
    print(f"📌 Título: {hypothesis.title}")
    print(f"🎯 Pares Pareados: {args.pairs} ({args.pairs * 2} partidas no total)")

    challenger = AresBotWrapper("Ares_Challenger_D2", depth=2, time_limit=0.25)
    baseline = AresBotWrapper("Ares_Baseline_D1", depth=1, time_limit=0.10)

    tester = AresHypothesisTester(SPRTConfig(elo0=0.0, elo1=15.0))

    def on_pair_done(idx, record):
        print(f"  ✅ Par #{idx + 1:02d} concluído: Seed={record['seed']} | LLR={record['current_llr']:+.2f} | Score={record['challenger_pair_score']}/2.0")

    result = tester.run_hypothesis_duel(
        hypothesis=hypothesis,
        challenger_bot=challenger,
        baseline_bot=baseline,
        num_pairs=args.pairs,
        on_pair_completed=on_pair_done,
        early_stopping=True,
    )

    print("\n" + "=" * 60)
    print(f"🏁 RESULTADO DO EXPERIMENTO: {result.verdict}")
    print(f"Placar: {result.challenger_wins}W - {result.baseline_wins}L - {result.draws}D (Score: {result.score * 100:.1f}%)")
    print(f"ΔElo: {result.delta_elo:+.1f} ± {result.elo_margin_95:.1f} (95% CI: [{result.ci_lower:+.1f}, {result.ci_upper:+.1f}])")
    print(f"LLR: {result.llr:+.2f} (Limites: [{result.sprt_bounds[0]:.2f}, {result.sprt_bounds[1]:.2f}])")
    print(f"Decisão: {result.verdict_reason}")
    print("=" * 60 + "\n")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    md_report = tester.format_markdown_report(result)
    md_path = out_dir / f"{hypothesis.id}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    print(f"📄 Relatório Markdown salvo em: {md_path}")

    json_path = out_dir / f"{hypothesis.id}.json"
    tester.save_report_json(result, json_path)
    print(f"💾 Relatório JSON salvo em: {json_path}")


if __name__ == "__main__":
    main()
