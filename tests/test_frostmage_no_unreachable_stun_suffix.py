import ast
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
