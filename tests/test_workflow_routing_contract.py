from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
TEMPLATES = ROOT / ".github" / "ISSUE_TEMPLATE"


def test_expensive_balance_and_nnue_workflows_are_manual_only():
    auto = (WORKFLOWS / "auto_balancer.yml").read_text(encoding="utf-8")
    nnue = (WORKFLOWS / "nnue_experimental_training.yml").read_text(encoding="utf-8")

    assert "schedule:" not in auto
    assert "schedule:" not in nnue
    assert "workflow_dispatch:" in auto
    assert "workflow_dispatch:" in nnue
    assert not (WORKFLOWS / "nnue_nightly.yml").exists()


def test_security_schedule_remains_separate_from_experiment_schedules():
    codeql = (WORKFLOWS / "codeql.yml").read_text(encoding="utf-8")
    assert "schedule:" in codeql
    assert "cron:" in codeql


def test_workflow_routing_guide_covers_every_current_workflow():
    guide = (WORKFLOWS / "README.md").read_text(encoding="utf-8")
    workflow_files = sorted(path.name for path in WORKFLOWS.glob("*.yml") if path.name != "README.yml")
    for filename in workflow_files:
        assert filename in guide


def test_issue_forms_require_governance_fields():
    config = (TEMPLATES / "config.yml").read_text(encoding="utf-8")
    assert "blank_issues_enabled: false" in config

    expected_forms = {
        "bug.yml": ["governing_issue", "dependencies", "evidence", "acceptance"],
        "planned-change.yml": ["governing_issue", "dependencies", "workflow", "acceptance"],
        "controlled-experiment.yml": [
            "governing_issue",
            "dependencies",
            "frozen_inputs",
            "workflow",
            "decision_rule",
        ],
    }

    for filename, required_ids in expected_forms.items():
        content = (TEMPLATES / filename).read_text(encoding="utf-8")
        for field_id in required_ids:
            assert f"id: {field_id}" in content
        assert content.count("required: true") >= len(required_ids)


def test_ci_documentation_points_to_routing_guide():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    development = (ROOT / "docs" / "DEVELOPMENT_WORKFLOW.md").read_text(encoding="utf-8")
    methodology = (ROOT / "docs" / "CI_WORKFLOW_METHODOLOGY.md").read_text(encoding="utf-8")
    for content in (readme, development, methodology):
        assert ".github/workflows/README.md" in content
