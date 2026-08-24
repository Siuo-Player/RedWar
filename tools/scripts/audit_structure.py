"""Audit RedWar's repository layout without modifying files.

Large projects benefit from explicit, non-destructive structure checks. This
script reports known legacy paths and files that should live in the canonical
areas described by docs/Estrutura_Projeto.md.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

EXPECTED_TOP_LEVEL = {
    "ai",
    "data",
    "deploy",
    "docs",
    "engine",
    "logs",
    "online",
    "tests",
    "tools",
    "ui",
}

# These are legitimate local/generated directories, not project modules.
IGNORED_TOP_LEVEL = {
    ".git",
    ".github",
    ".vscode",
    ".venv",
    ".pytest_cache",
    "venv",
    "__pycache__",
    "build",
    "dist",
}

LEGACY_PATHS = {
    "tools/analytics/opening_tester.py": "usar tools/analytics/opening_book.py",
    "tools/analytics/calibrate_elo_chain.py": "usar Arena/medição estatística atual",
    "tools/scripts/reorganize.py": "usar alterações estruturais explícitas e revisadas",
}


def audit(root: Path = ROOT) -> list[str]:
    findings: list[str] = []

    actual = {path.name for path in root.iterdir() if path.is_dir()}
    missing = sorted(EXPECTED_TOP_LEVEL - actual)
    for name in missing:
        findings.append(f"MISSING-DIR: {name}/")

    unexpected = sorted(actual - EXPECTED_TOP_LEVEL - IGNORED_TOP_LEVEL)
    for name in unexpected:
        findings.append(f"UNEXPECTED-TOP-LEVEL: {name}/")

    for relative, replacement in LEGACY_PATHS.items():
        path = root / relative
        if path.exists():
            findings.append(f"LEGACY: {relative} -> {replacement}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita a estrutura sem mover/apagar ficheiros")
    parser.add_argument("--strict", action="store_true", help="falha se houver qualquer finding")
    args = parser.parse_args()

    findings = audit()
    if findings:
        print("Encontrados problemas estruturais:")
        for finding in findings:
            print(f"- {finding}")
    else:
        print("Estrutura sem findings conhecidos.")

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
