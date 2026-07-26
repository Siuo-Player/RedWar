# ai/auto_balancer.py
import json
import os

def balancear_custos(ficheiro_stats="estatisticas_treino.json"):
    if not os.path.exists(ficheiro_stats):
        print(f"Ficheiro {ficheiro_stats} não encontrado. Corre o trainer.py primeiro.")
        return

    with open(ficheiro_stats, "r", encoding="utf-8") as f:
        stats = json.load(f)

    # Custos base originais que definiste
    custos_atuais = {
        "Bone": 10, "Ghoul": 30, "Obelisk": 40, 
        "Sentry": 50, "FrostMage": 60, "BoneLord": 100
    }
    
    print("--- AUTO-BALANCER (Baseado em Taxa de Vitória) ---\n")
    
    novos_custos = {}
    for peca, wins in stats.get("piece_wins", {}).items():
        plays = stats["piece_usage"].get(peca, 1)
        win_rate = wins / plays
        
        custo_antigo = custos_atuais.get(peca, 50)
        
        # Fórmula de Ajuste:
        # Se win rate > 55%, a peça está OP -> Aumentar o custo
        # Se win rate < 45%, a peça é fraca -> Baixar o custo
        fator = (win_rate - 0.5) * 2 # Ex: WR 0.6 = +0.2; WR 0.4 = -0.2
        ajuste = int(custo_antigo * fator) 
        
        # Prevenir ajustes demasiado drásticos numa só iteração
        ajuste = max(-15, min(15, ajuste))
        
        novo_custo = max(5, custo_antigo + ajuste) # Nunca pode custar menos de 5
        
        novos_custos[peca] = novo_custo
        estado = "OP (NERFAR)" if win_rate > 0.55 else ("FRACA (BUFFAR)" if win_rate < 0.45 else "EQUILIBRADA")
        print(f"[{peca.upper():<10}] WR: {win_rate*100:5.1f}% | Custo: {custo_antigo:3d} -> Sugerido: {novo_custo:3d} | Estado: {estado}")
        
    print("\nPara aplicar estas alterações:")
    print("1. Atualiza o custo no __init__ de cada peça em 'engine/pieces.py'.")
    print("2. Atualiza a lista de opções na UI e no Auto-Draft.")

if __name__ == "__main__":
    balancear_custos()