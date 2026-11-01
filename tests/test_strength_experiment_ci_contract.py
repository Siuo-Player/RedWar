from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "arena_experiments.yml"


def test_experiment_workflow_validates_arena_dataset():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Validate experiment dataset" in text
    assert "from tools.analytics.arena_experiment_validation import validate_experiment_records" in text
    assert "validate_experiment_records(records, metadata)" in text
    assert "invalid_games" in text
    assert "incomplete_valid_pair_ids" in text


def test_experiment_workflow_is_manual_only_and_not_authoritative():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert "PROMOTION_AUTHORITY: 'false'" in text
    assert "promotion_authority': False" in text
    assert "--margem-vitorias 0" in text
    assert 'echo "$rc" > "${PREFIX}-arena.exitcode"' in text


def test_experiment_workflow_publishes_validation_and_context_artifacts():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "${PREFIX}-validation.json" in text
    assert "${PREFIX}-games.context.jsonl" in text
    assert "actions/upload-artifact@v7" in text
    assert "retention-days: 30" in text


def test_experiment_workflow_carries_explicit_seed_and_population_controls():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "opening_seeds:" in text
    assert "seed_policy:" in text
    assert "seed_generation_rule:" in text
    assert "--opening-seeds \"$OPENING_SEEDS\"" in text
    assert "--seed-policy \"$SEED_POLICY\"" in text
    assert "--seed-generation-rule \"$SEED_GENERATION_RULE\"" in text
    assert "population_id:" in text
    assert "selection_policy:" in text
    assert "controller_population:" in text
    assert "skill_context:" in text


def test_experiment_workflow_uses_python_312_for_current_dependencies():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "python-version: '3.12'" in text
    assert "python-version: '3.10'" not in text
