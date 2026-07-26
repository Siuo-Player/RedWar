# ai/color_balancer.py
import sys
import os
import random
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from engine.pieces import Bone, Ghoul, Obelisk, Sentry, FrostMage, BoneLord
from ai.evaluator import avaliador_guloso

PECAS_DISPONIVEIS = [
    ("Bone", 10), ("Ghoul", 30), ("Obelisk", 40), 
    ("Sentry", 50), ("FrostMage", 60), ("BoneLord", 100)
]

def criar_peca_por_nome(nome, team):
    if nome == "Bone": return Bone(team)
    if nome == "Ghoul": return Ghoul(team)
    if nome == "Obelisk": return Obelisk(team)
    if nome == "Sentry": return Sentry(team)
    if nome == "FrostMage": return FrostMage(team)
    if nome == "BoneLord": return BoneLord(team)
    return None

def preencher_draft_aleatorio(gs, team, linhas_validas, orcamento):
    pontos = orcamento
    for r in linhas_validas:
        for c in range(8):
            if gs.board[r][c] is not None: continue 
            validas = [op for op in PECAS_DISPONIVEIS if op[1] <= pontos]
            if not validas: break
            escolha = random.choice(validas)
            gs.board[r][c] = criar_peca_por_nome(escolha[0], team)
            pontos -= escolha[1]

def avaliar_peso_acao_rapida(gs, acao):
    # Avaliador Greedy simplificado para rapidez extrema de simulação
    end_r, end_c = acao["end"]
    alvo = gs.board[end_r][end_c]
    
    if acao["type"] == "attack" and alvo:
        return alvo.cost
    elif acao["type"] == "stun" and acao.get("area"):
        peso = 0
        for (ar, ac) in acao["area"]:
            p = gs.board[ar][ac]
            if p and p.team != acao["piece"].team:
                peso += p.cost * (1 if p.stun_timer > 0 else 0.4)
        return peso
    return random.uniform(0.1, 0.5)

def jogar_batalha_simulada(orcamento_brancas, orcamento_pretas):
    gs = GameState(time_limit_seconds=99999)
    preencher_draft_aleatorio(gs, 'pretas', [0, 1], orcamento_pretas)
    preencher_draft_aleatorio(gs, 'brancas', [6, 7], orcamento_brancas)
    
    turnos = 0
    while not gs.game_over and turnos < 150:
        turnos += 1
        current_team = 'brancas' if gs.white_to_move else 'pretas'
        acoes_possiveis = []
        
        for r in range(8):
            for c in range(8):
                p = gs.board[r][c]
                if p and p.team == current_team and p.can_act():
                    for move in p.get_valid_moves(r, c, gs.board):
                        acoes_possiveis.append({"start": (r, c), "end": move, "type": "move", "piece": p})
                    for atk in p.get_valid_attacks(r, c, gs.board):
                        acoes_possiveis.append({"start": (r, c), "end": atk, "type": "attack", "piece": p})
                    for foco, area in p.get_valid_stuns(r, c, gs.board).items():
                        acoes_possiveis.append({"start": (r, c), "end": foco, "type": "stun", "area": area, "piece": p})
        
        if acoes_possiveis:
            acoes_com_peso = [(acao, avaliar_peso_acao_rapida(gs, acao)) for acao in acoes_possiveis]
            acoes_com_peso.sort(key=lambda x: x[1], reverse=True)
            melhor_peso = acoes_com_peso[0][1]
            melhores_acoes = [a[0] for a in acoes_com_peso if a[1] == melhor_peso]
            acao_escolhida = random.choice(melhores_acoes)
            
            if acao_escolhida["type"] == "stun":
                gs.make_action(acao_escolhida["start"], acao_escolhida["end"], "stun", acao_escolhida["area"])
            else:
                gs.make_action(acao_escolhida["start"], acao_escolhida["end"], acao_escolhida["type"])
        else:
            gs.check_game_over()
            if not gs.game_over:
                gs.game_over = True
                gs.winner = "Bloqueio"

    return gs.winner

def testar_equilibrio_de_cor(jogos_por_teste=50):
    print("--- INICIAR TESTE DE HANDICAP (PRIMEIRO MOVIMENTO) ---")
    
    # Vamos manter as pretas nos 200 pontos e descer as brancas aos poucos
    orcamento_pretas = 200
    testes_brancas = [200, 190, 180, 170, 160, 150]
    
    for orcamento_brancas in testes_brancas:
        vitorias_brancas = 0
        vitorias_pretas = 0
        empates = 0
        
        sys.stdout.write(f"\nA testar Brancas [{orcamento_brancas} pts] vs Pretas [{orcamento_pretas} pts]...")
        sys.stdout.flush()
        
        for _ in range(jogos_por_teste):
            resultado = jogar_batalha_simulada(orcamento_brancas, orcamento_pretas)
            if not resultado: continue
            
            if "Brancas Vencem" in resultado:
                vitorias_brancas += 1
            elif "Pretas Vencem" in resultado:
                vitorias_pretas += 1
            else:
                empates += 1
                
        taxa_vitoria = (vitorias_brancas / jogos_por_teste) * 100
        print(f"\nResultados: Brancas {vitorias_brancas} | Pretas {vitorias_pretas} | Empates {empates}")
        print(f"Taxa de Vitória Brancas: {taxa_vitoria:.1f}%")
        
        if taxa_vitoria < 45.0:
            print("--> CONCLUSÃO: Orçamento insuficiente. O handicap foi demasiado pesado para as Brancas.")
            break

if __name__ == "__main__":
    testar_equilibrio_de_cor(jogos_por_teste=100) # 100 jogos para maior precisão estatística