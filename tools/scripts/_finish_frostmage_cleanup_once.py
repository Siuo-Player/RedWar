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
write_marker = "permissions:\n  contents: write\n"
step_marker = "      - name: One-off FrostMage cleanup\n"
next_step_marker = "      - name: Build C++ differential test helpers\n"
if workflow.count(write_marker) != 1:
    raise SystemExit("Temporary write permission not found exactly once")
if workflow.count(step_marker) != 1:
    raise SystemExit("Temporary cleanup step not found exactly once")
step_start = workflow.index(step_marker)
next_step = workflow.index(next_step_marker, step_start)
workflow = workflow[:step_start] + workflow[next_step:]
workflow = workflow.replace(write_marker, "permissions:\n  contents: read\n", 1)
WORKFLOW.write_text(workflow, encoding="utf-8")
HELPER.unlink()
