"""Hypothesis-Driven Engine Evolution & Elo Testing Framework for Ares AI.

Inspired by Stockfish Fishtest, this module provides the scientific lifecycle for
continuous, regression-proof evolution of Ares in RedWar:
1. Formulate hypothesis of weakness / bottleneck.
2. Implement proposed improvement in a Challenger candidate.
3. Duel against Baseline Champion across mirrored opening pairs (alternating colors).
4. Evaluate Bradley-Terry binary Elo gain, 95% confidence intervals (1.96-sigma),
   Six-Sigma Champion Promotion Gate (3.0-sigma), and Wald's SPRT.
5. If H1 is accepted (or 3-sigma lower bound > 0): PROMOTION (Candidate becomes new Champion).
   If H0 is accepted: REJECTION (Hypothesis is falsified and discarded).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from ai.sprt import SPRTConfig, SPRTStatus, SPRTTracker, calculate_elo_difference, elo_to_expected_score
from engine.game_state import GameState
from tools.analytics.arena_tournament import _winner_side, run_headless_match
from tools.analytics.opening_book import OPENING_SEEDS


@dataclass
class Hypothesis:
    """Explicit hypothesis of engine bottleneck and proposed improvement."""
    id: str
    title: str
    bottleneck: str
    proposed_heuristic: str
    baseline_version: str
    candidate_version: str
    target_elo_gain: float = 5.0
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class HypothesisTestResult:
    """Full empirical outcome of a Challenger vs Baseline hypothesis duel."""
    hypothesis: Hypothesis
    total_games: int
    pairs_played: int
    challenger_wins: int
    baseline_wins: int
    draws: int
    score: float
    delta_elo: float
    elo_margin_95: float
    ci_lower: float
    ci_upper: float
    llr: float
    sprt_bounds: Tuple[float, float]
    sprt_status: str  # "H1_ACCEPTED", "H0_ACCEPTED", "CONTINUE"
    verdict: str      # "PROMOTED", "REJECTED", "CONTINUE"
    verdict_reason: str
    elo_margin_3sigma: float = 0.0
    ci_lower_3sigma: float = 0.0
    ci_upper_3sigma: float = 0.0
    sigma_gate_passed: bool = False
    pair_outcomes: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AresHypothesisTester:
    """Orchestrates scientific hypothesis duels between Ares candidate and baseline."""

    def __init__(self, sprt_config: Optional[SPRTConfig] = None):
        self.sprt_config = sprt_config or SPRTConfig(elo0=0.0, elo1=5.0, alpha=0.05, beta=0.05)

    def run_hypothesis_duel(
        self,
        hypothesis: Hypothesis,
        challenger_bot: Any,
        baseline_bot: Any,
        num_pairs: int = 8,
        opening_seeds: Optional[Sequence[int]] = None,
        early_stopping: bool = True,
        on_pair_completed: Optional[Callable[[int, Dict[str, Any]], None]] = None,
    ) -> HypothesisTestResult:
        """Run a paired mirror-opening tournament testing the hypothesis.

        For each opening seed, two games are played:
        - Game 1: Challenger (White) vs Baseline (Black)
        - Game 2: Baseline (White) vs Challenger (Black)
        This cancels out white first-move bias and opening seed advantages.
        """
        tracker = SPRTTracker(self.sprt_config)
        seeds = list(opening_seeds or OPENING_SEEDS[:num_pairs])
        if len(seeds) < num_pairs:
            seeds.extend(range(1000, 1000 + num_pairs - len(seeds)))

        pair_outcomes = []
        challenger_total_wins = 0
        baseline_total_wins = 0
        draws_total = 0

        for pair_idx in range(num_pairs):
            seed = seeds[pair_idx]

            # Game 1: Challenger as White, Baseline as Black
            g1 = run_headless_match(challenger_bot, baseline_bot, opening_index=pair_idx, opening_seed=seed)
            w1 = _winner_side(g1["winner"])
            if w1 == "white":
                g1_challenger = 1
                g1_baseline = 0
            elif w1 == "black":
                g1_challenger = 0
                g1_baseline = 1
            else:
                g1_challenger = 0
                g1_baseline = 0

            # Game 2: Baseline as White, Challenger as Black (Mirrored color inversion)
            g2 = run_headless_match(baseline_bot, challenger_bot, opening_index=pair_idx, opening_seed=seed)
            w2 = _winner_side(g2["winner"])
            if w2 == "black":
                g2_challenger = 1
                g2_baseline = 0
            elif w2 == "white":
                g2_challenger = 0
                g2_baseline = 1
            else:
                g2_challenger = 0
                g2_baseline = 0

            pair_c_wins = g1_challenger + g2_challenger
            pair_b_wins = g1_baseline + g2_baseline
            pair_draws = 2 - (pair_c_wins + pair_b_wins)

            challenger_total_wins += pair_c_wins
            baseline_total_wins += pair_b_wins
            draws_total += pair_draws

            # Update SPRT tracker
            status = tracker.add_result(win=pair_c_wins, loss=pair_b_wins, draw=pair_draws)

            pair_record = {
                "pair_index": pair_idx,
                "seed": seed,
                "game1": {"challenger_color": "white", "winner": w1, "plies": g1.get("plies", 0)},
                "game2": {"challenger_color": "black", "winner": w2, "plies": g2.get("plies", 0)},
                "challenger_pair_score": pair_c_wins + 0.5 * pair_draws,
                "current_llr": round(tracker.llr, 3),
                "current_elo": tracker.estimate_elo()[0],
            }
            pair_outcomes.append(pair_record)

            if on_pair_completed:
                on_pair_completed(pair_idx, pair_record)

            if early_stopping and status in (SPRTStatus.H1_ACCEPTED, SPRTStatus.H0_ACCEPTED):
                break

        # Compute multi-tier statistics: 1.96-sigma (95% CI) and 3.0-sigma (99.73% CI)
        total_games = tracker.total_games
        score = tracker.score
        stats = tracker.estimate_elo_multitier()
        delta_elo = stats["delta_elo"]
        elo_margin = stats["margin_95"]
        ci_lower = stats["ci_95"][0]
        ci_upper = stats["ci_95"][1]
        elo_margin_3sigma = stats["margin_3sigma"]
        ci_lower_3sigma = stats["ci_3sigma"][0]
        ci_upper_3sigma = stats["ci_3sigma"][1]

        sigma_gate_passed = bool(delta_elo > 0 and ci_lower_3sigma >= 0.0)

        # Decision rule adapted for RedWar anti-involution governance
        sprt_status_str = tracker.status.value.upper()
        if tracker.status == SPRTStatus.H1_ACCEPTED or sigma_gate_passed:
            verdict = "PROMOTED"
            gate_label = " (3σ Champion Gate atingido)" if sigma_gate_passed else ""
            reason = f"Hipótese H1 comprovada com significância estatística{gate_label} (ΔElo: +{delta_elo:.1f} ± {elo_margin:.1f}, LLR: {tracker.llr:.2f} >= {tracker.upper_bound:.2f})."
        elif tracker.status == SPRTStatus.H0_ACCEPTED or (delta_elo < 0 and ci_upper <= 0.0):
            verdict = "REJECTED"
            reason = f"Hipótese H0 aceite; o candidato não superou o campeão (ΔElo: {delta_elo:.1f} ± {elo_margin:.1f}, LLR: {tracker.llr:.2f} <= {tracker.lower_bound:.2f})."
        elif delta_elo > 0:
            verdict = "CONTINUE"
            reason = f"Tendência positiva (+{delta_elo:.1f} Elo), mas requer mais partidas para confirmação formal (CI95%: [{ci_lower}, {ci_upper}], 3σ: [{ci_lower_3sigma}, {ci_upper_3sigma}])."
        else:
            verdict = "REJECTED"
            reason = f"Sem evidência de melhoria (Score: {score*100:.1f}%, ΔElo: {delta_elo:.1f})."

        return HypothesisTestResult(
            hypothesis=hypothesis,
            total_games=total_games,
            pairs_played=len(pair_outcomes),
            challenger_wins=challenger_total_wins,
            baseline_wins=baseline_total_wins,
            draws=draws_total,
            score=round(score, 4),
            delta_elo=delta_elo,
            elo_margin_95=elo_margin,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            llr=round(tracker.llr, 3),
            sprt_bounds=(round(tracker.lower_bound, 3), round(tracker.upper_bound, 3)),
            sprt_status=sprt_status_str,
            verdict=verdict,
            verdict_reason=reason,
            elo_margin_3sigma=elo_margin_3sigma,
            ci_lower_3sigma=ci_lower_3sigma,
            ci_upper_3sigma=ci_upper_3sigma,
            sigma_gate_passed=sigma_gate_passed,
            pair_outcomes=pair_outcomes,
        )

    @staticmethod
    def format_markdown_report(result: HypothesisTestResult) -> str:
        """Format a Fishtest-style markdown test report with multi-tiered sigma evaluation."""
        h = result.hypothesis
        status_emoji = "🏆 PROMOVIDO A NOVO CAMPEÃO" if result.verdict == "PROMOTED" else ("❌ REJEITADO (HIPÓTESE FALSIFICADA)" if result.verdict == "REJECTED" else "⏳ INCONCLUSIVO (CONTINUAR)")
        gate_status_str = "✅ APROVADO (Zero Risco de Involução, p < 0.0027)" if result.sigma_gate_passed else "⏳ PENDENTE / NÃO ATINGIDO"

        return f"""# Relatório de Teste de Hipótese Ares AI: {h.id}

## 📌 Sumário da Hipótese
- **ID**: `{h.id}`
- **Título**: {h.title}
- **Data**: {h.created_at}
- **Gargalo Observado**: {h.bottleneck}
- **Melhoria Implementada**: {h.proposed_heuristic}
- **Candidato (*Challenger*)**: `{h.candidate_version}`
- **Campeão Atual (*Baseline*)**: `{h.baseline_version}`

---

## 📊 Veredito e Resultados Estatísticos
> ### **Decisão Final: {status_emoji}**
> **Justificação**: {result.verdict_reason}

| Métrica | Valor Obtido |
|---|---|
| **Total de Partidas (Pares Espelhados)** | {result.total_games} partidas ({result.pairs_played} pares) |
| **Placar (Candidato vs Baseline)** | **+{result.challenger_wins}** / **-{result.baseline_wins}** / ={result.draws} |
| **Taxa de Pontuação (Score)** | **{result.score * 100:.1f}%** |
| **Diferença de Elo ($\\Delta$ Elo)** | **{'+' if result.delta_elo >= 0 else ''}{result.delta_elo:.1f}** |
| **Margem de Erro (95% CI)** | **± {result.elo_margin_95:.1f}** (`[{result.ci_lower:+.1f}, {result.ci_upper:+.1f}]`, 1.96σ) |
| **Portão de Campeão (99.73% CI)** | **± {result.elo_margin_3sigma:.1f}** (`[{result.ci_lower_3sigma:+.1f}, {result.ci_upper_3sigma:+.1f}]`, 3.0σ) |
| **Status do Portão 3-Sigma** | `{gate_status_str}` |
| **Razão de Log-Verossimilhança (LLR)** | **{result.llr:+.2f}** (Limites: [{result.sprt_bounds[0]:.2f}, {result.sprt_bounds[1]:.2f}]) |
| **Estado SPRT de Wald** | `{result.sprt_status}` |

---

## 🔬 Protocolo Científico Stockfish & Governança de Sigmas
1. **Duelos Espelhados**: Cada abertura foi jogada de Brancas e de Pretas para eliminar viés de cor e assimetrias de tabuleiro.
2. **Modelo Bradley-Terry Binário**: Ausência de empates artificiais de xadrez; a pontuação reflete pura dominância tática por stun.
3. **Por que 3-Sigma ($3\\sigma$) e não 5-Sigma ($5\\sigma$)?**:
   - No CERN/LHC, $5\\sigma$ ($p < 3 \\times 10^{{-7}}$) é obrigatório devido ao *Look-Elsewhere Effect* (varredura de milhões de canais energéticos).
   - Em motores de jogo, requerer $5\\sigma$ aumentaria o número de partidas necessárias por $(5.0/1.96)^2 \\approx 6.5\\times$, gerando fadiga amostral extrema e alto erro Tipo II (rejeição de melhorias reais de +3 Elo).
   - O padrão **3-Sigma ($3\\sigma$, 99.73% de confiança, $p < 0.0027$)** é o ponto ideal da engenharia de alta confiabilidade (*Six Sigma*), garantindo que a probabilidade de um falso positivo na promoção de um campeão seja inferior a 0.14%.
4. **Proteção Anti-Involução**: O motor campeão só é substituído perante prova estatística conclusiva ($H_1$ ou $3\\sigma$ com limite inferior positivo).
"""

    @staticmethod
    def save_report_json(result: HypothesisTestResult, path: Path | str) -> None:
        """Persist structured report to disk for experiment provenance."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
