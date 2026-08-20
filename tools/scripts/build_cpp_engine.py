# tools/scripts/build_cpp_engine.py
import argparse
import os
import subprocess
import sys
import platform
import glob

def get_vcvars_path():
    """Usa o vswhere (incluído no Windows/VS) para descobrir dinamicamente o compilador MSVC."""
    vswhere_path = r"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
    vswhere_cmd = f'"{vswhere_path}" -latest -property installationPath'
    try:
        vs_path = subprocess.check_output(vswhere_cmd, shell=True, text=True).strip()
        vcvars = os.path.join(vs_path, "VC", "Auxiliary", "Build", "vcvars64.bat")
        if os.path.exists(vcvars):
            return vcvars
    except subprocess.CalledProcessError:
        pass
    # Fallback comum
    fallback = r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
    return fallback if os.path.exists(fallback) else None

def compile_cpp_project(is_smoke_test=False):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cpp_dir = os.path.join(base_dir, "ai", "cpp_engine")
    os.chdir(cpp_dir)

    # Encontra todos os ficheiros .cpp
    all_cpp_files = glob.glob("*.cpp")

    if is_smoke_test:
        # Para o SmokeTest, removemos o main.cpp (evita 2 entrypoints) e o engine.cpp original
        cpp_files = [f for f in all_cpp_files if f not in ["main.cpp", "engine.cpp"]]
        if "SmokeTest.cpp" not in cpp_files:
            cpp_files.append("SmokeTest.cpp")
        exe_name = "SmokeTest.exe" if platform.system() == "Windows" else "SmokeTest"
    else:
        # Para o Motor normal, removemos o SmokeTest.cpp e o engine.cpp original
        cpp_files = [f for f in all_cpp_files if f not in ["SmokeTest.cpp", "engine.cpp"]]
        exe_name = "engine.exe" if platform.system() == "Windows" else "engine"

    files_str = " ".join(cpp_files)
    include_path = os.path.join(cpp_dir, 'nlohmann')

    print(f"🚀 A preparar compilação 64-bits ({exe_name}) com arquitetura modular...")
    print(f"📦 Módulos injetados: {files_str}")

    if platform.system() == "Windows":
        vcvars_path = get_vcvars_path()
        if not vcvars_path:
            print("❌ ERRO: Não foi possível localizar o vcvars64.bat do MSVC.")
            sys.exit(1)
        compile_cmd = f'"{vcvars_path}" && cl /EHsc /O2 /I"{include_path}" /Fe:{exe_name} {files_str}'
        print("⚙️ A executar o MSVC Optimizer (cl.exe)...")
    else:
        compile_cmd = f'g++ -O3 -std=c++17 -I"{include_path}" {files_str} -o {exe_name}'
        print("⚙️ A executar o GCC Optimizer (g++)...")

    result = subprocess.run(compile_cmd, shell=True)
    if result.returncode == 0:
        print(f"✅ SUCESSO: Compilado e guardado em {os.path.join(cpp_dir, exe_name)}")
    else:
        print("❌ ERRO: Falha na compilação do C++.")
        sys.exit(result.returncode)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compila o motor C++ modular.")
    parser.add_argument("--smoke", action="store_true", help="Compila os módulos em conjunto com SmokeTest.cpp")
    args = parser.parse_args()
    compile_cpp_project(is_smoke_test=args.smoke)