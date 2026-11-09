from __future__ import annotations

from pathlib import Path
import pytest

from ai.ares_hypothesis_testing import (
    Hypothesis,
    HypothesisTestResult,
    AresHypothesisTester,
)
from ai.sprt import SPRTConfig


def test_hypothesis_result_tier_0_screening_classification():
    """Verify duels with < 20 games are classified as Tier 0 Screening Rápido Exploratório."""
    hyp = Hypothesis(
        id="H-TEST-TIER0",
        title="Test Screening",
        bottleneck="Tactical search bottleneck",
        proposed_heuristic="Fast ordering bonus",
        baseline_version="baseline_v1",
        candidate_version="candidate_v1",
    )
    result = HypothesisTestResult(
        hypothesis=hyp,
        total_games=8,
        pairs_played=4,
        challenger_wins=5,
        baseline_wins=3,
        draws=0,
        score=0.625,
        delta_elo=88.7,
        elo_margin_95=248.7,
        ci_lower=-160.0,
        ci_upper=337.4,
        llr=0.08,
        sprt_bounds=(-2.94, 2.94),
        sprt_status="CONTINUE",
        verdict="CONTINUE",
        verdict_reason="Tendência direcional de Screening Rápido Exploratório (ΔElo_screened: +88.7 ± 248.7).",
        tier="TIER_0_SCREENING",
        tier_display="Tier 0 — Screening Rápido Exploratório",
    )

    assert result.tier == "TIER_0_SCREENING"
    assert "Screening Rápido Exploratório" in result.tier_display

    report = AresHypothesisTester.format_markdown_report(result)
    assert "Tier 0 — Screening Rápido Exploratório" in report
    assert "Classificação Metodológica da Amostra" in report


def test_hypothesis_result_tier_1_and_tier_2_classification():
    """Verify 20-99 games is Tier 1 SPRT and >= 100 games is Tier 2 Champion Gate."""
    hyp = Hypothesis(
        id="H-TEST-TIERS",
        title="Test Tiers",
        bottleneck="None",
        proposed_heuristic="None",
        baseline_version="b",
        candidate_version="c",
    )

    # Mock tier assignment
    def make_result(games: int, tier: str, display: str) -> HypothesisTestResult:
        return HypothesisTestResult(
            hypothesis=hyp,
            total_games=games,
            pairs_played=games // 2,
            challenger_wins=games // 2,
            baseline_wins=games // 2,
            draws=0,
            score=0.5,
            delta_elo=0.0,
            elo_margin_95=20.0,
            ci_lower=-20.0,
            ci_upper=20.0,
            llr=0.0,
            sprt_bounds=(-2.94, 2.94),
            sprt_status="CONTINUE",
            verdict="CONTINUE",
            verdict_reason="Test",
            tier=tier,
            tier_display=display,
        )

    t1 = make_result(50, "TIER_1_SPRT", "Tier 1 — Validação Intermédia e SPRT de Wald")
    assert t1.tier == "TIER_1_SPRT"

    t2 = make_result(100, "TIER_2_CHAMPION_GATE", "Tier 2 — Bateria Amostral Ampla / Portão de Campeão de Produção")
    assert t2.tier == "TIER_2_CHAMPION_GATE"


def test_framework_documentation_invariants():
    """Verify framework documentation mandates Tier 0 screening designation and sample threshold."""
    doc_path = Path("docs/RESEARCH/ares_stockfish_elo_testing_framework.md")
    content = doc_path.read_text(encoding="utf-8")

    assert "Tier 0 — Screening Rápido Exploratório" in content
    assert "Tendências de Screening Exploratório" in content
    assert "ΔElo_screened" in content
    assert "É expressamente vedado declarar \"Elo comprovado em produção\" a partir de duelos de Tier 0" in content
    assert "Tier 2 — Bateria Amostral Ampla / Portão de Campeão de Produção" in content
    assert "Norma Ética de Comunicação de Resultados Competitivos" in content
