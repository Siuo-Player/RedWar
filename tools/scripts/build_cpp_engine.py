"""Build the RedWar C++ engine or native regression binaries.

The source lists are explicit on purpose: adding a helper .cpp must never
silently change the production engine link step.
"""
from __future__ import annotations

import argparse
import os
import platform
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CPP_DIR = ROOT / "ai" / "cpp_engine"
INCLUDE_DIR = CPP_DIR / "nlohmann"
TESTS_DIR = ROOT / "tests"

ENGINE_SOURCES = [
    "board.cpp",
    "evaluate.cpp",
    "main.cpp",
    "movegen.cpp",
    "search.cpp",
    "nnue.cpp",
]
SMOKE_SOURCES = [
    "board.cpp",
    "evaluate.cpp",
    "movegen.cpp",
    "search.cpp",
    "nnue.cpp",
    "SmokeTest.cpp",
]
NUMERIC_SOURCES = [
    "board.cpp",
    "evaluate.cpp",
    "movegen.cpp",
    "search.cpp",
    "nnue.cpp",
]
BRIDGE_SOURCES = [
    "board.cpp",
    "evaluate.cpp",
    "movegen.cpp",
    "search.cpp",
    "nnue.cpp",
]
MOVEGEN_SOURCES = [
    "board.cpp",
    "evaluate.cpp",
    "movegen.cpp",
    "search.cpp",
    "nnue.cpp",
]


def get_vcvars_path() -> Path | None:
    if platform.system() != "Windows":
        return None

    candidates: list[Path] = []
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if program_files_x86:
        candidates.append(Path(program_files_x86) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe")

    candidates.append(Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe"))

    for vswhere in candidates:
        if not vswhere.exists():
            continue
        try:
            result = subprocess.run(
                [str(vswhere), "-latest", "-property", "installationPath"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            continue

        installation = Path(result.stdout.strip())
        vcvars = installation / "VC" / "Auxiliary" / "Build" / "vcvars64.bat"
        if vcvars.exists():
            return vcvars

    fallback = Path(
        r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
    )
    return fallback if fallback.exists() else None


def _windows_compile(sources: list[str], output: Path) -> int:
    vcvars = get_vcvars_path()
    if not vcvars:
        raise RuntimeError("Não foi possível localizar vcvars64.bat do MSVC.")
    command = f'"{vcvars}" && cl /nologo /EHsc /O2 /std:c++17 /I"{INCLUDE_DIR}" /Fe:"{output}" ' + " ".join(
        f'"{path}"' for path in sources
    )
    completed = subprocess.run(command, shell=True, cwd=CPP_DIR)
    return completed.returncode


def _unix_compile(sources: list[str], output: Path) -> int:
    command = [
        "g++",
        "-std=c++17",
        "-O2",
        "-pipe",
        f"-I{INCLUDE_DIR}",
        *sources,
        "-o",
        str(output),
    ]
    completed = subprocess.run(command, cwd=CPP_DIR)
    return completed.returncode


def compile_cpp_project(mode: str = "engine") -> Path:
    if mode == "engine":
        sources = ENGINE_SOURCES
        suffix = ".exe" if platform.system() == "Windows" else ""
        output = CPP_DIR / f"engine{suffix}"
    elif mode == "smoke":
        sources = SMOKE_SOURCES
        suffix = ".exe" if platform.system() == "Windows" else ""
        output = CPP_DIR / f"SmokeTest{suffix}"
    elif mode == "numeric":
        sources = NUMERIC_SOURCES
        test_path = TESTS_DIR / "cpp_numeric_bounds_test.cpp"
        if not test_path.is_file():
            raise FileNotFoundError(f"Teste C++ em falta: {test_path}")
        sources = [*sources, str(test_path)]
        suffix = ".exe" if platform.system() == "Windows" else ""
        output = ROOT / f"cpp_numeric_bounds_test{suffix}"
    elif mode == "bridge":
        sources = BRIDGE_SOURCES
        test_path = TESTS_DIR / "cpp_make_unmake_bridge_test.cpp"
        if not test_path.is_file():
            raise FileNotFoundError(f"Teste C++ em falta: {test_path}")
        sources = [*sources, str(test_path)]
        suffix = ".exe" if platform.system() == "Windows" else ""
        output = ROOT / f"cpp_make_unmake_bridge_test{suffix}"
    elif mode == "movegen":
        sources = MOVEGEN_SOURCES
        test_path = TESTS_DIR / "cpp_movegen_bridge_test.cpp"
        if not test_path.is_file():
            raise FileNotFoundError(f"Teste C++ em falta: {test_path}")
        sources = [*sources, str(test_path)]
        suffix = ".exe" if platform.system() == "Windows" else ""
        output = ROOT / f"cpp_movegen_bridge_test{suffix}"
    else:
        raise ValueError(f"Modo desconhecido: {mode}")

    missing = [name for name in sources if not (CPP_DIR / name).is_file()]
    if mode in {"numeric", "bridge", "movegen"}:
        missing = [name for name in missing if not Path(name).is_file()]
    if missing:
        raise FileNotFoundError(f"Fontes C++ em falta: {', '.join(missing)}")

    print(f"🚀 A compilar {mode}: {' '.join(sources)}")

    if platform.system() == "Windows":
        return_code = _windows_compile(sources, output)
    else:
        relative_sources = [
            str(Path(source).relative_to(CPP_DIR)) if Path(source).is_relative_to(CPP_DIR) else source
            for source in sources
        ]
        return_code = _unix_compile(relative_sources, output)

    if return_code != 0:
        raise SystemExit(return_code)

    print(f"✅ Compilado: {output}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Compila o motor C++ de RedWar")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--smoke", action="store_true", help="Compila o SmokeTest")
    group.add_argument("--numeric-test", action="store_true", help="Compila a regressão de limites numéricos")
    group.add_argument("--bridge-test", action="store_true", help="Compila o helper de equivalência make/unmake")
    group.add_argument("--movegen-test", action="store_true", help="Compila o helper de equivalência da geração de ações")
    args = parser.parse_args()

    if args.numeric_test:
        compile_cpp_project("numeric")
    elif args.bridge_test:
        compile_cpp_project("bridge")
    elif args.movegen_test:
        compile_cpp_project("movegen")
    elif args.smoke:
        compile_cpp_project("smoke")
    else:
        compile_cpp_project("engine")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
