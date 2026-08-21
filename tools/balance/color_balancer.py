import sys
import os
import random
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.game_state import GameState
from engine.pieces import obter_catalogo_pecas
from ai.bot import BOT_INICIANTE
from engine.config import ORCAMENTO_BRANCAS, LINHAS, COLUNAS

def formatar_tempo(segundos):
    segundos = max(0, int(segundos))
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    return f"{minutos}m {segs}s"

def preencher_draft_aleatorio(gs, team, linhas_validas, orcamento):
    pontos = orcamento
    catalogo = obter_catalogo_pecas()
    
    for r in linhas_validas:
        for c in range(COLUNAS):
            if gs.board[r][c] is not None: continue 
            validas = [p for p in catalogo if p["cost"] <= pontos]
            if not validas: break
            escolha = random.choice(validas)
            gs.board[r][c] = escolha["class"](team)
            pontos -= escolha["cost"]

def jogar_batalha_simulada(orcamento_brancas, orcamento_pretas):
    gs = GameState(time_limit_seconds=99999)
    preencher_draft_aleatorio(gs, 'pretas', [0, 1], orcamento_pretas)
    preencher_draft_aleatorio(gs, 'brancas', [LINHAS - 2, LINHAS - 1], orcamento_brancas)
    
    while not gs.game_over:
        best_move = BOT_INICIANTE.play(gs)
        if best_move:
            gs.execute_action(best_move)
        else:
            gs.check_game_over()
            if not gs.game_over:
                gs.game_over = True
                gs.winner = "Bloqueio"

    return gs.winner

def testar_equilibrio_de_cor(jogos_por_teste=200):
    print("🧠 BALANÇO INTELIGENTE: ESCALA POSITIVA DE ORÇAMENTO 🧠\n")
    
    margem_erro = 4.0 
    step = 10         
    
    # Handicap: > 0 ajuda as Pretas, < 0 ajuda as Brancas
    handicap = 0 
    
    historico = {}
    iteracao = 1
    max_iteracoes = 15
    handicap_anterior = None
    
    while iteracao <= max_iteracoes:
        # Define os orçamentos com base no handicap (Mínimo de 200 sempre)
        if handicap >= 0:
            orc_b = 200
            orc_p = 200 + handicap
        else:
            orc_b = 200 + abs(handicap)
            orc_p = 200
            
        if handicap not in historico:
            historico[handicap] = {"b": 0, "p": 0, "e": 0, "rondas": 0, "orc_b": orc_b, "orc_p": orc_p}
            
        print(f"🔄 Ronda {iteracao} | Brancas [{orc_b} pts] vs Pretas [{orc_p} pts]")
        start_time = time.time()
        
        v_b, v_p, e_m = 0, 0, 0
        
        for i in range(jogos_por_teste):
            resultado = jogar_batalha_simulada(orc_b, orc_p)
            if "Brancas" in str(resultado): v_b += 1
            elif "Pretas" in str(resultado): v_p += 1
            else: e_m += 1
            
            decorrido = time.time() - start_time
            t_medio = decorrido / max(1, i + 1)
            restantes = jogos_por_teste - (i + 1)
            eta = formatar_tempo(restantes * t_medio)
            
            sys.stdout.write(f"\r   Progresso: {i+1}/{jogos_por_teste} | ETA da Ronda: {eta}   ")
            sys.stdout.flush()
        
        historico[handicap]["b"] += v_b
        historico[handicap]["p"] += v_p
        historico[handicap]["e"] += e_m
        historico[handicap]["rondas"] += 1
        
        total_jogos = historico[handicap]["b"] + historico[handicap]["p"] + historico[handicap]["e"]
        taxa_b = (historico[handicap]["b"] / total_jogos) * 100
        taxa_p = (historico[handicap]["p"] / total_jogos) * 100
        delta_atual = taxa_b - taxa_p
        
        print(f"\n   -> Médias ({total_jogos} jogos): Brancas {taxa_b:.1f}% | Pretas {taxa_p:.1f}% | Empates: {historico[handicap]['e']}")
        print(f"   -> Diferença solidificada: {abs(delta_atual):.1f}% (Objetivo: <= {margem_erro}%)\n")
        
        # 1. VALIDAÇÃO DE SUCESSO
        if abs(delta_atual) <= margem_erro:
            if historico[handicap]["rondas"] < 3:
                print(f"   [?] Bom candidato encontrado! A executar ronda de validação ({historico[handicap]['rondas']}/3)...")
                iteracao += 1
                continue 
            else:
                print(f"🎯 PONTO DE EQUILÍBRIO CONFIRMADO! Brancas: {orc_b} pts | Pretas: {orc_p} pts.")
                return
        
        # 2. DETETAR OVERSHOOT ou DIVERGÊNCIA
        if handicap_anterior is not None and handicap_anterior != handicap:
            tot_ant = historico[handicap_anterior]["b"] + historico[handicap_anterior]["p"] + historico[handicap_anterior]["e"]
            delta_anterior = (historico[handicap_anterior]["b"] / tot_ant * 100) - (historico[handicap_anterior]["p"] / tot_ant * 100)
            
            if (delta_anterior > 0 and delta_atual < 0) or (delta_anterior < 0 and delta_atual > 0):
                if historico[handicap]["rondas"] < 2:
                    print("   [!] Possível overshoot detetado! A re-testar o orçamento atual...")
                    iteracao += 1
                    continue
                else:
                    if step == 1:
                        print("   [!] Fundo da curva atingido (salto mínimo). A parar pesquisa.")
                        break 
                    else:
                        step = max(1, step // 2)
                        print(f"   [!] Overshoot validado. A reduzir o salto para {step} pts e a inverter marcha.")
            
            elif abs(delta_atual) > abs(delta_anterior) + 2.0:
                if historico[handicap]["rondas"] < 2:
                    print("   [!] A diferença aumentou. A re-testar para descartar ruído estatístico...")
                    iteracao += 1
                    continue
                else:
                    print("   [!] Anomalia confirmada. A travar o motor de pesquisa!")
                    break
        
        # 3. DECIDIR A PRÓXIMA DIREÇÃO
        handicap_anterior = handicap
        if delta_atual > 0: # Brancas ganham -> Aumentar o Handicap (Ajuda Pretas)
            handicap += step
        else:               # Pretas ganham -> Diminuir o Handicap (Ajuda Brancas)
            handicap -= step
            
        iteracao += 1
        
    # FIM DA PESQUISA
    melhor_h = None
    menor_diferenca = 999.0
    
    for h, dados in historico.items():
        tot = dados["b"] + dados["p"] + dados["e"]
        if tot == 0: continue
        d = abs((dados["b"] / tot * 100) - (dados["p"] / tot * 100))
        if d < menor_diferenca:
            menor_diferenca = d
            melhor_h = h
            
    if melhor_h is not None:
        final_b = historico[melhor_h]["orc_b"]
        final_p = historico[melhor_h]["orc_p"]
        print(f"\n⚠️ Fim da pesquisa. Analisando o Big Data recolhido...")
        print(f"🏆 MELHOR ORÇAMENTO: Brancas [{final_b} pts] vs Pretas [{final_p} pts] (Diferença de {menor_diferenca:.1f}%)")

if __name__ == "__main__":
    testar_equilibrio_de_cor(jogos_por_teste=200)