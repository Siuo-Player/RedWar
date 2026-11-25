#!/usr/bin/env python3
"""Read-only inventory of RedWar pytest modules.

Classifications are heuristics, not proof of requirement coverage or quality.
Run:
    python tools/audit_test_portfolio.py --format markdown
    python tools/audit_test_portfolio.py --format json --output /tmp/test-portfolio.json
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any


def dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = dotted_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def classify_domain(path: str) -> str:
    name = Path(path).stem.lower()
    if any(token in name for token in ("strength", "arena", "sprt", "calibration", "promotion", "balance", "pricer", "holdout", "historical")):
        return "Ares / Arena / experiências"
    if any(token in name for token in ("web", "online", "multiplayer", "socket", "security", "identity", "server", "api", "pvp")):
        return "Web / servidor / segurança"
    if any(token in name for token in ("replay", "telemetry", "rwen", "history", "persistence")):
        return "Replay / persistência / telemetria"
    if any(token in name for token in ("cross_backend", "native", "perft", "engine", "ares", "nnue", "search", "bot", "ai", "tactical", "domain_specific")):
        return "Motor / Ares / Python-C++"
    if any(token in name for token in ("lite", "ui", "sidebar", "hover", "interaction", "manual", "launcher", "icon", "layout", "studio")):
        return "Desktop / UI / produto"
    if any(token in name for token in ("hero", "spell", "action", "moves", "rules", "game", "invariant", "mechanic", "terminal", "stun", "draft", "hazard", "puzzle", "clock")):
        return "Gameplay / regras"
    return "Tooling / governação"


def classify_level(path: str, flags: set[str]) -> str:
    name = Path(path).stem.lower()
    if "windows_display_acceptance" in name or "acceptance" in name:
        return "acceptance (heurístico)"
    if "browser" in flags or "e2e" in name or "journey" in name:
        return "system/E2E (heurístico)"
    if flags.intersection({"subprocess", "network", "threading"}) or any(
        token in name for token in ("integration", "differential", "parity", "bridge", "server", "sequence")
    ):
        return "integration (heurístico)"
    if any(token in name for token in ("model", "state", "contract", "invariant", "schema")):
        return "component/contract (heurístico)"
    return "unit/component (heurístico)"


def analyze_source(source: str, path: str) -> dict[str, Any]:
    """Analyze source without importing or executing it."""
    tree = ast.parse(source, filename=path)
    nodes = list(ast.walk(tree))
    test_functions = sorted(
        node.name for node in nodes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    )
    fixture_functions = sorted(
        node.name for node in nodes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any("fixture" in dotted_name(decorator) for decorator in node.decorator_list)
    )
    imports: set[str] = set()
    for node in nodes:
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])

    calls = {dotted_name(node.func) for node in nodes if isinstance(node, ast.Call)}
    decorators = {
        dotted_name(decorator.func) if isinstance(decorator, ast.Call) else dotted_name(decorator)
        for node in nodes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        for decorator in node.decorator_list
    }
    flags: set[str] = set()
    if "pytest.mark.parametrize" in decorators:
        flags.add("parametrized")
    if "hypothesis" in imports or "given" in decorators:
        flags.add("property-based")
    if "subprocess" in imports or any(call.startswith("subprocess.") for call in calls):
        flags.add("subprocess")
    if "playwright" in imports or any("playwright" in call.lower() for call in calls):
        flags.add("browser")
    if imports.intersection({"socket", "websocket", "http", "requests", "urllib"}):
        flags.add("network")
    if imports.intersection({"threading", "concurrent"}):
        flags.add("threading")
    if "asyncio" in imports or any(call.startswith("asyncio.") for call in calls):
        flags.add("async")
    if "random" in imports:
        flags.add("randomness")
    if "time.sleep" in calls:
        flags.add("wall-clock-sleep")
    if "asyncio.sleep" in calls:
        flags.add("async-sleep")
    if any(call.endswith(".read_text") or call in {"open", "Path.open"} for call in calls):
        flags.add("file/source-read")
    if "pytest.raises" in calls:
        flags.add("raises")
    if "tmp_path" in source or "tmp_path_factory" in source:
        flags.add("temporary-files")
    if any(isinstance(node, ast.Name) and node.id == "monkeypatch" for node in nodes):
        flags.add("monkeypatch")
    if "source" in Path(path).stem.lower() or "boundary" in Path(path).stem.lower():
        flags.add("possible-source-contract")

    return {
        "path": path.replace("\\", "/"),
        "domain": classify_domain(path),
        "level": classify_level(path, flags),
        "lines": len(source.splitlines()),
        "test_functions": test_functions,
        "test_function_count": len(test_functions),
        "fixture_functions": fixture_functions,
        "fixture_count": len(fixture_functions),
        "assert_count": sum(isinstance(node, ast.Assert) for node in nodes),
        "pytest_raises_count": sum(
            isinstance(node, ast.Call) and dotted_name(node.func) == "pytest.raises" for node in nodes
        ),
        "flags": sorted(flags),
    }


def scan_test_root(test_root: Path) -> list[dict[str, Any]]:
    """Inventory test_*.py modules in a given tests directory."""
    results: list[dict[str, Any]] = []
    for path in sorted(test_root.glob("test_*.py")):
        relative = path.as_posix()
        try:
            results.append(analyze_source(path.read_text(encoding="utf-8"), relative))
        except (OSError, UnicodeError, SyntaxError) as exc:
            results.append({
                "path": relative, "domain": classify_domain(relative), "level": "unclassified",
                "lines": None, "test_functions": [], "test_function_count": 0,
                "fixture_functions": [], "fixture_count": 0, "assert_count": 0,
                "pytest_raises_count": 0, "flags": ["parse-error"],
                "error": f"{type(exc).__name__}: {exc}",
            })
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    domains: dict[str, int] = {}
    levels: dict[str, int] = {}
    for item in results:
        domains[item["domain"]] = domains.get(item["domain"], 0) + 1
        levels[item["level"]] = levels.get(item["level"], 0) + 1
    return {
        "module_count": len(results),
        "test_function_count": sum(item["test_function_count"] for item in results),
        "fixture_count": sum(item["fixture_count"] for item in results),
        "parametrized_modules": sum("parametrized" in item["flags"] for item in results),
        "property_based_modules": sum("property-based" in item["flags"] for item in results),
        "modules_with_wall_clock_sleep": [item["path"] for item in results if "wall-clock-sleep" in item["flags"]],
        "modules_with_network": [item["path"] for item in results if "network" in item["flags"]],
        "parse_errors": [item["path"] for item in results if "parse-error" in item["flags"]],
        "domains": dict(sorted(domains.items())),
        "levels": dict(sorted(levels.items())),
    }


def render_markdown(results: list[dict[str, Any]]) -> str:
    summary = summarize(results)
    lines = [
        "# RedWar — inventário estrutural de testes", "",
        "> Gerado por `tools/audit_test_portfolio.py`. Áreas e níveis são heurísticos; esta tabela não demonstra cobertura de requisitos.",
        "",
        f"- Módulos `test_*.py`: **{summary['module_count']}**",
        f"- Funções de teste: **{summary['test_function_count']}**",
        f"- Fixtures: **{summary['fixture_count']}**",
        f"- Módulos parametrizados: **{summary['parametrized_modules']}**",
        f"- Módulos com Hypothesis/property-based detetado: **{summary['property_based_modules']}**",
        f"- Módulos com `time.sleep`: **{len(summary['modules_with_wall_clock_sleep'])}**",
        "", "## Por módulo", "",
        "| Módulo | Área (heurística) | Nível (heurística) | Testes | Fixtures | Sinais |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in results:
        flags = ", ".join(item["flags"]) or "—"
        lines.append(
            f"| `{item['path']}` | {item['domain']} | {item['level']} | "
            f"{item['test_function_count']} | {item['fixture_count']} | {flags} |"
        )
    lines.extend(["", "## Sinais de revisão", "", "### Uso de sleeps"])
    if summary["modules_with_wall_clock_sleep"]:
        lines.extend(f"- `{path}`" for path in summary["modules_with_wall_clock_sleep"])
    else:
        lines.append("- Nenhum detetado.")
    lines.extend(["", "### Erros de parsing"])
    if summary["parse_errors"]:
        lines.extend(f"- `{path}`" for path in summary["parse_errors"])
    else:
        lines.append("- Nenhum.")
    lines.extend(["", "A classificação automática é apenas um ponto de partida. A ligação requisito → risco → cenário → teste → gate → evidência necessita de curadoria humana."])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--output", type=Path, help="Ficheiro de saída; sem esta opção escreve no stdout.")
    parser.add_argument("--strict", action="store_true", help="Termina com erro se algum módulo não puder ser analisado.")
    args = parser.parse_args(argv)
    test_root = args.repo_root / "tests"
    if not test_root.is_dir():
        parser.error(f"tests directory not found: {test_root}")
    results = scan_test_root(test_root)
    content = render_markdown(results) if args.format == "markdown" else (
        json.dumps({"summary": summarize(results), "modules": results}, ensure_ascii=False, indent=2) + "\n"
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)
    return 1 if args.strict and any("parse-error" in item["flags"] for item in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
