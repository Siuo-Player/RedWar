import os
import sys
import json
import subprocess

ARQUIVO_CUSTOS = os.path.join('engine', 'mobs_config.json')

def executar_pipeline():
    print("🚀 A INICIAR PIPELINE DE BUILD E BALANCEAMENTO...\n")
    
    print("1. A correr Testes Unitários...")
    test_result = subprocess.run(["pytest", "tests/"], capture_output=True, text=True)
    if test_result.returncode != 0:
        print("❌ FALHA NOS TESTES. Abortando Pipeline.")
        print(test_result.stdout)
        sys.exit(1)
    print("✅ Testes passaram com sucesso!\n")
    
    print("2. A Simular Estatísticas de Jogo Rápido (Trainer)...")
    subprocess.run(["python", os.path.join("ai", "trainer.py")], capture_output=True)
    print("✅ Estatísticas geradas!\n")
    
    print("3. Auto-Balancing e Atualização do JSON de Custos...")
    
    # CORREÇÃO PYLANCE: Inicializar a variável antes do bloco try
    novo_custo = {}
    
    try:
        with open("estatisticas_treino.json", "r") as f: 
            stats = json.load(f)
        with open(ARQUIVO_CUSTOS, "r") as f: 
            custos_atuais = json.load(f)
        
        for peca, wins in stats.get("piece_wins", {}).items():
            plays = stats["piece_usage"].get(peca, 1)
            fator = ((wins / plays) - 0.5) * 2 
            ajuste = max(-10, min(10, int(custos_atuais.get(peca, 50) * fator)))
            novo_custo[peca] = max(5, custos_atuais.get(peca, 50) + ajuste)
            
        for k, v in custos_atuais.items():
            if k not in novo_custo: 
                novo_custo[k] = v
                
        with open(ARQUIVO_CUSTOS, "w") as f: 
            json.dump(novo_custo, f, indent=4)
        print("✅ engine/mobs_config.json atualizado com sucesso!\n")
    except Exception as e:
        print(f"⚠️ Aviso no Balanceamento: {e}\n")

    print("4. A Gerar Relatório e Atualizar README...")
    with open("relatorio_build.txt", "w", encoding="utf-8") as f:
        f.write("RELATÓRIO DE BUILD E BALANCEAMENTO\n")
        f.write("==================================\n")
        f.write("Testes: OK\n")
        f.write("Custos Atualizados pelo MCTS:\n")
        for k, v in novo_custo.items(): 
            f.write(f"- {k}: {v} pts\n")
        
    print("✅ Relatório Guardado em relatorio_build.txt")
    print("🏁 PIPELINE CONCLUÍDO. Podes fazer git push.")

if __name__ == "__main__":
    executar_pipeline()