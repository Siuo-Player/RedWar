from pathlib import Path


WORKFLOW = Path(__file__).parents[1] / ".github" / "workflows" / "ai_strength_experiment.yml"


def test_strength_workflow_validates_arena_dataset():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "Validate experiment dataset" in text
    assert "from tools.analytics.arena_experiment_validation import validate_experiment_records" in text
    assert "validate_experiment_records(records, metadata)" in text
    assert "invalid_games" in text
    assert "incomplete_valid_pair_ids" in text


def test_strength_workflow_does_not_use_arena_exit_code_as_promotion_gate():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "--margem-vitorias 0" in text
    assert 'echo "$rc" > "${PREFIX}-arena.exitcode"' in text
    assert "exit 0" in text


def test_strength_workflow_publishes_validation_artifact():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "${PREFIX}-validation.json" in text
    assert "actions/upload-artifact@v" in text


def test_strength_workflow_auto_triggers_only_on_experiment_branches():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "  push:" in text
    assert "      - 'experiment/strength/**'" in text
    assert "branches:" in text
    assert "branches-ignore:" not in text


def test_strength_workflow_push_defaults_are_reproducible():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "GAMES: ${{ github.event_name == 'workflow_dispatch' && inputs.games || '100' }}" in text
    assert "NODES: ${{ github.event_name == 'workflow_dispatch' && inputs.nodes || '10000' }}" in text
    assert "BASELINE_REF: ${{ github.event_name == 'workflow_dispatch' && inputs.baseline_ref || 'origin/main' }}" in text
    assert "ares-dev-population-v1" in text
    assert "paired-fixed-openings" in text


def test_strength_workflow_carries_explicit_seed_controls():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "opening_seeds:" in text
    assert "seed_policy:" in text
    assert "seed_generation_rule:" in text
    assert "--opening-seeds \"$OPENING_SEEDS\"" in text
    assert "--seed-policy \"$SEED_POLICY\"" in text
    assert "--seed-generation-rule \"$SEED_GENERATION_RULE\"" in text
    assert "10091,10211,10307,10401,10503,10601,10709,10809,10907,11009,11103,11201,11301,11409,11501,11601" not in text


def test_strength_workflow_retains_raw_experiment_artifacts():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "path: /tmp/redwar-strength-results/" in text
    assert "name: ares-strength-experiment-${{ github.sha }}" in text
    assert "retention-days: 30" in text
