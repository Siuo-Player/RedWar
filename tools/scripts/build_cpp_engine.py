"""Build the RedWar C++ engine or its native smoke test.

The source list is explicit on purpose: adding a test/helper .cpp must never
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


def compile_cpp_project(is_smoke_test: bool = False) -> Path:
    sources = SMOKE_SOURCES if is_smoke_test else ENGINE_SOURCES
    missing = [name for name in sources if not (CPP_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Fontes C++ em falta: {', '.join(missing)}")

    exe_name = "SmokeTest.exe" if is_smoke_test and platform.system() == "Windows" else (
        "SmokeTest" if is_smoke_test else "engine.exe" if platform.system() == "Windows" else "engine"
    )
    output = CPP_DIR / exe_name

    print(f"🚀 A compilar {'SmokeTest' if is_smoke_test else 'engine'}: {' '.join(sources)}")

    if platform.system() == "Windows":
        vcvars = get_vcvars_path()
        if not vcvars:
            raise RuntimeError("Não foi possível localizar vcvars64.bat do MSVC.")
        command = f'"{vcvars}" && cl /nologo /EHsc /O2 /std:c++17 /I"{INCLUDE_DIR}" /Fe:"{output}" ' + " ".join(
            f'"{CPP_DIR / source}"' for source in sources
        )
        completed = subprocess.run(command, shell=True, cwd=CPP_DIR)
    else:
        command = [
            "g++",
            "-std=c++17",
            "-O3",
            "-march=native",
            "-mtune=native",
            "-flto",
            "-DNDEBUG",
            "-pipe",
            f"-I{INCLUDE_DIR}",
            *[str(CPP_DIR / source) for source in sources],
            "-o",
            str(output),
        ]
        completed = subprocess.run(command, cwd=CPP_DIR)

    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    print(f"✅ Compilado: {output}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Compila o motor C++ de RedWar")
    parser.add_argument("--smoke", action="store_true", help="Compila o SmokeTest em vez do executável da engine")
    args = parser.parse_args()
    compile_cpp_project(is_smoke_test=args.smoke)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
