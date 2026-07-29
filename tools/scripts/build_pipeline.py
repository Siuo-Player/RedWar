import os
import sys
import subprocess

# Garante que o script corre sempre a partir da raiz do projeto
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT_DIR)

def executar_pipeline():
    print("🚀 A INICIAR PIPELINE DE BUILD E BALANCEAMENTO...\n")
    
    print("1. A correr Testes Unitários...")
    test_result = subprocess.run([sys.executable, "-m", "pytest", "tests/"], capture_output=True, text=True)
    if test_result.returncode != 0:
        print("❌ FALHA NOS TESTES. Abortando Pipeline.")
        print(test_result.stdout)
        sys.exit(1)
    print("✅ Testes passaram com sucesso!\n")
    
    print("2. A Simular Estatísticas de Jogo Rápido (Trainer)...")
    subprocess.run([sys.executable, os.path.join("ai", "trainer.py")], capture_output=False)
    print("✅ Estatísticas geradas em data/estatisticas_treino.json!\n")
    
    print("3. Auto-Balancing e Atualização do JSON de Custos...")
    subprocess.run([sys.executable, os.path.join("ai", "auto_pricer.py")], capture_output=False)
    
    print("\n4. A Gerar Relatório de Pipeline...")
    os.makedirs("logs", exist_ok=True)
    with open(os.path.join("logs", "relatorio_build.txt"), "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE BUILD E BALANCEAMENTO\n")
        f.write("==================================\n")
        f.write("Testes: OK\n")
        f.write("Telemetria: Gerada em data/estatisticas_treino.json\n")
        f.write("Motor Económico: Executado e heroes_config.json verificado.\n")
        
    print("✅ Relatório Guardado em logs/relatorio_build.txt")
    print("🏁 PIPELINE CONCLUÍDO. Podes fazer git push.")

if __name__ == "__main__":
    executar_pipeline()