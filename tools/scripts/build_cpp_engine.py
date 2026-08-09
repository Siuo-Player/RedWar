# tools/scripts/build_cpp_engine.py
import argparse
import os
import subprocess
import sys

def get_vcvars_path():
    """Usa o vswhere (incluído no Windows/VS) para descobrir dinamicamente o compilador."""
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

def compile_cpp_source(source_file: str, exe_file: str):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    cpp_dir = os.path.join(base_dir, "ai", "cpp_engine")
    source_path = os.path.join(cpp_dir, source_file) if not os.path.isabs(source_file) else source_file
    exe_path = os.path.join(cpp_dir, exe_file) if not os.path.isabs(exe_file) else exe_file
    print(f"🚀 A preparar compilação 64-bits do Cérebro C++ ({os.path.basename(source_path)})...")
    if not os.path.exists(source_path):
        print(f"❌ ERRO: Ficheiro fonte não encontrado em {source_path}")
        sys.exit(1)
    vcvars_path = get_vcvars_path()
    if not vcvars_path:
        print("❌ ERRO: Não foi possível localizar o vcvars64.bat do MSVC.")
        sys.exit(1)
    include_path = os.path.join(cpp_dir, 'nlohmann')
    compile_cmd = f'"{vcvars_path}" && cl /EHsc /O2 /I"{include_path}" /Fe:{exe_path} {source_path}'
    print("⚙️ A executar o MSVC Optimizer (cl.exe)...")
    result = subprocess.run(compile_cmd, shell=True, cwd=cpp_dir)
    if result.returncode == 0:
        print(f"✅ SUCESSO: Compilado e guardado em {exe_path}")
        return
    else:
        print("❌ ERRO: Falha na compilação do C++.")
        sys.exit(result.returncode)

def compile_engine():
    compile_cpp_source("engine.cpp", "engine.exe")

def compile_smoke_test():
    compile_cpp_source("SmokeTest.cpp", "SmokeTest.exe")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compila o motor C++ ou testes auxiliares.")
    parser.add_argument("--smoke", action="store_true", help="Compila ai/cpp_engine/SmokeTest.cpp para SmokeTest.exe")
    parser.add_argument("--source", type=str, help="Ficheiro fonte relativo a ai/cpp_engine ou caminho absoluto para compilar.")
    parser.add_argument("--exe", type=str, help="Nome do executável de saída ou caminho absoluto.")
    args = parser.parse_args()
    if args.smoke:
        compile_smoke_test()
    elif args.source and args.exe:
        compile_cpp_source(args.source, args.exe)
    else:
        compile_engine()
