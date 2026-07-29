# ai/auto_pricer.py
import json
import os
import math

ARQUIVO_HEROES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'engine', 'heroes_config.json')
ARQUIVO_STATS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'estatisticas_treino.json')

def calcular_win_esperada(elo_a, elo_b):
    """Retorna a probabilidade de vitória da equipa A sobre a B (0.0 a 1.0)."""
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))

def executar_balanceamento_automatico():
    print("📈 A executar Avaliação Económica Ponderada por ELO...")
    
    if not os.path.exists(ARQUIVO_STATS):
        print("❌ Ficheiro estatisticas_treino.json não encontrado.")
        return
        
    with open(ARQUIVO_STATS, 'r') as f:
        stats = json.load(f)
        
    with open(ARQUIVO_HEROES, 'r', encoding='utf-8') as f:
        heroes = json.load(f)
    # map name -> cost for analysis
    custos_atuais = {name: data.get('cost', 0) for name, data in heroes.items()}
        
    matches = stats.get("matches", [])
    if not matches:
        print("⚠️ Sem partidas no histórico.")
        return

    # Acumuladores de Performance
    piece_score_delta = {peca: 0.0 for peca in custos_atuais.keys()}
    piece_volume = {peca: 0.0 for peca in custos_atuais.keys()}
    
    for match in matches:
        w_elo = match["white_elo"]
        b_elo = match["black_elo"]
        w_draft = match["white_draft"]
        b_draft = match["black_draft"]
        result = match["result"] # 1.0 para Brancas, 0.0 para Pretas, 0.5 Empate
        
        # Probabilidade de vitória das Brancas
        e_white = calcular_win_esperada(w_elo, b_elo)
        e_black = 1.0 - e_white
        
        # Delta para Brancas (W - E_A)
        delta_white = result - e_white
        # Delta para Pretas (W - E_A)
        delta_black = (1.0 - result) - e_black
        
        # Atribuir impacto às peças das Brancas multiplicando pela sua quantidade (Q)
        for peca, qtd in w_draft.items():
            if peca in piece_score_delta:
                piece_score_delta[peca] += (delta_white * qtd)
                piece_volume[peca] += qtd
                
        # Atribuir impacto às peças das Pretas multiplicando pela sua quantidade (Q)
        for peca, qtd in b_draft.items():
            if peca in piece_score_delta:
                piece_score_delta[peca] += (delta_black * qtd)
                piece_volume[peca] += qtd

    mudancas = False
    print("\n📊 Análise de Performance Absoluta (Impacto sobre ELO Base)")
    print("-" * 65)
    
    for peca in custos_atuais.keys():
        if piece_volume[peca] == 0: continue

        custo_antigo = custos_atuais[peca]
        
        # Média da Performance: O quão acima/abaixo das expectativas a peça jogou
        media_delta = piece_score_delta[peca] / piece_volume[peca]
        
        # Fator de Ajuste (K): Define a agressividade da mudança de preço.
        # Um K de 50 significa que se a peça for 10% melhor que o esperado (0.10), sobe 5 pontos.
        K = 50.0 
        ajuste = int(round(media_delta * K))
        
        novo_custo = max(5, min(200, custo_antigo + ajuste))
        
        if novo_custo != custo_antigo:
            custos_atuais[peca] = novo_custo
            # update heroes mapping
            if peca in heroes:
                heroes[peca]['cost'] = novo_custo
            mudancas = True
            sinal = "+" if media_delta > 0 else ""
            estado = "🔴 NERFADA" if media_delta > 0 else "🟢 BUFFADA"
            print(f"{peca.ljust(12)} | Performance: {sinal}{media_delta*100:.1f}% | {custo_antigo} -> {novo_custo} ({estado})")
        else:
            print(f"{peca.ljust(12)} | Performance: {media_delta*100:+.1f}% | {custo_antigo} (Estável)")

    if mudancas:
        with open(ARQUIVO_HEROES, 'w', encoding='utf-8') as f:
            json.dump(heroes, f, indent=4, ensure_ascii=False)
        print("\n✅ heroes_config.json atualizado com precisão matemática!")
    else:
        print("\n✅ Preços perfeitamente equilibrados. Sem mudanças.")

if __name__ == "__main__":
    executar_balanceamento_automatico()