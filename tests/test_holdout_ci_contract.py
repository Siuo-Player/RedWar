from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "arena_experiments.yml"


def test_manual_workflow_exposes_protected_holdout_mode():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "mode:" in text
    assert "protected_holdout" in text
    assert "inputs.mode == 'protected_holdout'" in text
    assert "tools/analytics/holdout_arena.py" in text


def test_experiment_workflow_is_manual_only_and_holdout_is_not_promotion_authority():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert "promotion_authority': False" in text
    assert "PROMOTION_AUTHORITY: 'false'" in text


def test_holdout_mode_requires_canonical_main_and_full_candidate_sha():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Protected holdout must be dispatched from canonical main." in text
    assert 'CANDIDATE_SHA_INPUT" =~ ^[0-9a-fA-F]{40}$' in text
    assert 'git cat-file -e "${CANDIDATE_SHA_INPUT}^{commit}"' in text


def test_holdout_mode_passes_frozen_engine_provenance():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert '--challenger-version "$CANDIDATE_SHA"' in text
    assert '--baseline-version "$BASELINE_SHA"' in text
    assert '--rules-version "$RULES_VERSION"' in text
