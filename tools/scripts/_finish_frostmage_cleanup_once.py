from pathlib import Path

PIECES = Path("engine/pieces.py")
WORKFLOW = Path(".github/workflows/test_suite.yml")
HELPER = Path("tools/scripts/_finish_frostmage_cleanup_once.py")

text = PIECES.read_text(encoding="utf-8")
class_start = text.index("class FrostMage(DataPiece):")
method_start = text.index("    def get_valid_spells", class_start)
return_marker = "        return spells\n"
return_pos = text.index(return_marker, method_start)
next_class = text.index("\n\nclass ", return_pos)
dead = text[return_pos + len(return_marker):next_class]
if "        stuns = {}\n" not in dead or "return stuns" not in dead:
    raise SystemExit("Expected unreachable legacy FrostMage STUN suffix was not found")
new_text = text[:return_pos + len(return_marker)] + text[next_class + 2:]
PIECES.write_text(new_text, encoding="utf-8")

source = PIECES.read_text(encoding="utf-8")
if source.count("class FrostMage(DataPiece):") != 1:
    raise SystemExit("Unexpected FrostMage class count after cleanup")
class_start = source.index("class FrostMage(DataPiece):")
method_start = source.index("    def get_valid_spells", class_start)
return_positions = []
pos = method_start
while True:
    try:
        idx = source.index(return_marker, pos)
    except ValueError:
        break
    return_positions.append(idx)
    pos = idx + len(return_marker)
if len(return_positions) != 1:
    raise SystemExit(f"Expected one FrostMage return spells marker, got {len(return_positions)}")
return_pos = return_positions[0]
next_class = source.index("\n\nclass ", return_pos)
if source[return_pos + len(return_marker):next_class].strip():
    raise SystemExit("Unexpected executable suffix remains after return spells")

workflow = WORKFLOW.read_text(encoding="utf-8")
expected_workflow = """name: RedWar Test Suite\n\non:\n  pull_request:\n    types: [opened, synchronize, reopened]\n  push:\n    branches-ignore: [main]\n  workflow_dispatch:\n\nconcurrency:\n  group: redwar-tests-${{ github.event.pull_request.number || github.ref }}\n  cancel-in-progress: true\n\npermissions:\n  contents: read\n\njobs:\n  tests:\n    runs-on: ubuntu-latest\n    timeout-minutes: 10\n    env:\n      PYTHONHASHSEED: '0'\n    steps:\n      - name: Checkout\n        uses: actions/checkout@v7\n\n      - name: Set up Python 3.12\n        uses: actions/setup-python@v7\n        with:\n          python-version: '3.12'\n          cache: pip\n\n      - name: Install dependencies\n        run: |\n          python -m pip install --upgrade pip\n          pip install -r requirements.txt\n\n      - name: Build C++ differential test helpers\n        run: |\n          python tools/scripts/build_cpp_engine.py --bridge-test\n          python tools/scripts/build_cpp_engine.py --movegen-test\n          python tools/scripts/build_cpp_engine.py --numeric-test\n          python tools/scripts/build_cpp_engine.py --perft-test\n\n      - name: Run Python test suite\n        run: python -m pytest tests/\n"""
if workflow.count("permissions:\n  contents: write\n") != 1:
    raise SystemExit("Temporary write permission not found exactly once")
if workflow.replace("permissions:\n  contents: write\n", "permissions:\n  contents: read\n", 1) != expected_workflow:
    raise SystemExit("test_suite.yml differs from the known baseline beyond temporary permissions")
WORKFLOW.write_text(expected_workflow, encoding="utf-8")

TEST = Path("tests/test_frostmage_no_unreachable_stun_suffix.py")
TEST.write_text('''import ast\nfrom pathlib import Path\n\n\ndef test_frostmage_get_valid_spells_ends_at_return_spells():\n    source = Path("engine/pieces.py").read_text(encoding="utf-8")\n    tree = ast.parse(source)\n    frostmage = next(\n        node for node in tree.body\n        if isinstance(node, ast.ClassDef) and node.name == "FrostMage"\n    )\n    method = next(\n        node for node in frostmage.body\n        if isinstance(node, ast.FunctionDef) and node.name == "get_valid_spells"\n    )\n    returns = [\n        i for i, node in enumerate(method.body)\n        if isinstance(node, ast.Return)\n        and isinstance(node.value, ast.Name)\n        and node.value.id == "spells"\n    ]\n    assert len(returns) == 1\n    assert returns[0] == len(method.body) - 1\n''', encoding="utf-8")

HELPER.unlink()
