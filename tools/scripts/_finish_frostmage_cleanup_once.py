import ast
from pathlib import Path

PIECES = Path("engine/pieces.py")
WORKFLOW = Path(".github/workflows/test_suite.yml")
HELPER = Path("tools/scripts/_finish_frostmage_cleanup_once.py")

text = PIECES.read_text(encoding="utf-8")
tree = ast.parse(text)
frostmage = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "FrostMage")
method = next(node for node in frostmage.body if isinstance(node, ast.FunctionDef) and node.name == "get_valid_spells")
returns = [node for node in method.body if isinstance(node, ast.Return) and isinstance(node.value, ast.Name) and node.value.id == "spells"]
if len(returns) != 1:
    raise SystemExit(f"Expected one active return spells, got {len(returns)}")
return_node = returns[0]
lines = text.splitlines(keepends=True)
method_end = method.end_lineno
if return_node.end_lineno >= method_end:
    raise SystemExit("FrostMage method has no unreachable suffix to remove")
suffix = "".join(lines[return_node.end_lineno:method_end])
if "stuns = {}" not in suffix or "return stuns" not in suffix:
    raise SystemExit("Expected legacy unreachable FrostMage STUN suffix was not found")
PIECES.write_text("".join(lines[:return_node.end_lineno] + lines[method_end:]), encoding="utf-8")

TEST = Path("tests/test_frostmage_no_unreachable_stun_suffix.py")
TEST.write_text('''import ast
from pathlib import Path


def test_frostmage_get_valid_spells_ends_at_return_spells():
    source = Path("engine/pieces.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    frostmage = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "FrostMage"
    )
    method = next(
        node for node in frostmage.body
        if isinstance(node, ast.FunctionDef) and node.name == "get_valid_spells"
    )
    returns = [
        i for i, node in enumerate(method.body)
        if isinstance(node, ast.Return)
        and isinstance(node.value, ast.Name)
        and node.value.id == "spells"
    ]
    assert len(returns) == 1
    assert returns[0] == len(method.body) - 1
''', encoding="utf-8")

workflow = WORKFLOW.read_text(encoding="utf-8")
expected_workflow = """name: RedWar Test Suite

on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches-ignore: [main]
  workflow_dispatch:

concurrency:
  group: redwar-tests-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

permissions:
  contents: read

jobs:
  tests:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      PYTHONHASHSEED: '0'
    steps:
      - name: Checkout
        uses: actions/checkout@v7

      - name: Set up Python 3.12
        uses: actions/setup-python@v7
        with:
          python-version: '3.12'
          cache: pip

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Build C++ differential test helpers
        run: |
          python tools/scripts/build_cpp_engine.py --bridge-test
          python tools/scripts/build_cpp_engine.py --movegen-test
          python tools/scripts/build_cpp_engine.py --numeric-test
          python tools/scripts/build_cpp_engine.py --perft-test

      - name: Run Python test suite
        run: python -m pytest tests/
"""
cleanup_step = """      - name: One-off FrostMage cleanup
        if: hashFiles('tools/scripts/_finish_frostmage_cleanup_once.py') != ''
        shell: bash
        run: |
          python tools/scripts/_finish_frostmage_cleanup_once.py
          git diff --check
          python -m py_compile engine/pieces.py tests/test_frostmage_no_unreachable_stun_suffix.py
          python -m pytest -q tests/test_frostmage_no_unreachable_stun_suffix.py tests/test_frostmage_nevada_contract.py tests/test_cross_backend_movegen.py tests/test_cross_backend_make_unmake.py
          git add engine/pieces.py tests/test_frostmage_no_unreachable_stun_suffix.py .github/workflows/test_suite.yml
          git diff --cached --check
          git config user.name 'github-actions[bot]'
          git config user.email '41898282+github-actions[bot]@users.noreply.github.com'
          git commit -m 'fix: remove unreachable FrostMage stun code'
          git push
          exit 0

"""
if workflow.count(cleanup_step) != 1:
    raise SystemExit("Temporary cleanup step not found exactly once")
restored = workflow.replace(cleanup_step, "", 1)
if restored.replace("permissions:\n  contents: write\n", "permissions:\n  contents: read\n", 1) != expected_workflow:
    raise SystemExit("test_suite.yml differs from the known baseline beyond temporary changes")
WORKFLOW.write_text(expected_workflow, encoding="utf-8")
HELPER.unlink()
