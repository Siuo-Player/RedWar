import os
import sys
import subprocess

# Garante que o script corre sempre a partir da raiz do projeto
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT_DIR)

# Injetar ROOT_DIR no PYTHONPATH para os scripts encontrarem os módulos (engine, ai, etc)
env = os.environ.copy()
env["PYTHONPATH"] = ROOT_DIR

def executar_pipeline():
    print("🚀 A INICIAR PIPELINE DE BUILD E VALIDAÇÃO LOCAL...\n")
    
    # 1. Compilação do Motor C++ (Smoke Tests e Sintaxe)
    print("1. A compilar o Motor C++ (Cérebro da IA)...")
    build_result = subprocess.run([sys.executable, os.path.join("tools", "scripts", "build_cpp_engine.py")], capture_output=False, env=env)
    if build_result.returncode != 0:
        print("❌ FALHA NA COMPILAÇÃO C++. Abortando Pipeline.")
        sys.exit(1)
    print("✅ Motor C++ compilado com sucesso!\n")
    
    # 2. Testes de Unidade e Física do Python
    print("2. A correr Testes Unitários...")
    test_result = subprocess.run([sys.executable, "-m", "pytest", "tests/"], capture_output=True, text=True, env=env)
    if test_result.returncode != 0:
        print("❌ FALHA NOS TESTES. Abortando Pipeline.")
        print(test_result.stdout)
        sys.exit(1)
    print("✅ Testes passaram com sucesso!\n")
    
    # --- NOTA ARQUITETURAL ---
    # O Trainer e o Auto-Balancer foram removidos deste script.
    # Essas ferramentas vão correr EXCLUSIVAMENTE na Cloud (GitHub Actions)
    # para evitar conflitos locais nos ficheiros .json a cada git push.
    # -------------------------
    
    # 3. Relatório Simplificado
    print("\n3. A Gerar Relatório de Pipeline...")
    os.makedirs("logs", exist_ok=True)
    with open(os.path.join("logs", "relatorio_build.txt"), "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE BUILD E VALIDAÇÃO LOCAL\n")
        f.write("==================================\n")
        f.write("Compilação C++: OK\n")
        f.write("Testes Unitários: OK\n")
        f.write("Telemetria & Balanceamento: Delegados para a Cloud (GitHub Actions).\n")
        
    print("✅ Relatório Guardado em logs/relatorio_build.txt")
    print("🏁 PIPELINE LOCAL CONCLUÍDO. O teu git push vai arrancar em segurança.")

if __name__ == "__main__":
    executar_pipeline()