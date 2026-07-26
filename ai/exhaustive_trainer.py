# ai/exhaustive_trainer.py
import sys
import os
import random
import json
import time
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from engine.pieces import Bone, Ghoul, Obelisk, Sentry, FrostMage, BoneLord

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

def preencher_draft_estruturado(gs, team, linhas_validas, estrutura_foco=None):
    pontos = 200
    
    if estrutura_foco:
        for nome, (r, c) in estrutura_foco:
            peca_custo = next((p[1] for p in PECAS_DISPONIVEIS if p[0] == nome), 0)
            gs.board[r][c] = criar_peca_por_nome(nome, team)
            pontos -= peca_custo

    for r in linhas_validas:
        for c in range(8):
            if gs.board[r][c] is not None: continue 
            validas = [op for op in PECAS_DISPONIVEIS if op[1] <= pontos]
            if not validas: break
            escolha = random.choice(validas)
            gs.board[r][c] = criar_peca_por_nome(escolha[0], team)
            pontos -= escolha[1]

def avaliar_peso_acao(gs, acao):
    end_r, end_c = acao["end"]
    alvo = gs.board[end_r][end_c]
    if acao["type"] == "attack" and alvo:
        return alvo.cost * 1.0 
    elif acao["type"] == "stun" and acao.get("area"):
        peso_total = 0
        for (ar, ac) in acao["area"]:
            alvo_area = gs.board[ar][ac]
            if alvo_area and alvo_area.team != acao["piece"].team:
                peso_total += alvo_area.cost * (1.0 if alvo_area.stun_timer > 0 else 0.4)
        return peso_total
    return random.uniform(0.1, 0.5)

def run_exhaustive_simulation(matches_per_structure=20):
    stats = {
        "total_matches": 0,
        "outcomes": defaultdict(int),
        "structure_winrates_greedy": defaultdict(lambda: {"wins": 0, "plays": 0}),
        "structure_winrates_random": defaultdict(lambda: {"wins": 0, "plays": 0})
    }

    start_time = time.time()
    
    # Define as Estruturas a testar (Combinando 2 ou 3 peças para testar sinergias)
    estruturas_teste = [
        # O Rei guardado por 2 Obelisks (Formação Tartaruga)
        [("BoneLord", (0, 3)), ("Obelisk", (0, 2)), ("Obelisk", (0, 4))],
        # Sentry e FrostMage lado a lado (Formação de Controlo Longo)
        [("FrostMage", (1, 2)), ("Sentry", (1, 3))],
        # Vanguarda Agressiva dupla
        [("Ghoul", (1, 3)), ("Ghoul", (1, 4))]
    ]
    
    # Adicionar testes base de 1 peça para controlo
    for peca in PECAS_DISPONIVEIS:
        estruturas_teste.append([(peca[0], (0, 0))])

    total_cenarios = len(estruturas_teste) * 2 
    print(f"[{time.strftime('%H:%M:%S')}] A iniciar Simulação de Estruturas...")
    
    cenario_atual = 0
    for team, linhas in [('pretas', [0, 1]), ('brancas', [6, 7])]:
        for estrutura in estruturas_teste:
            estrutura_ajustada = []
            for nome, (r, c) in estrutura:
                if team == 'brancas':
                    # Espelhar as coordenadas para as brancas
                    r_ajustado = 7 if r == 0 else (6 if r == 1 else r)
                    estrutura_ajustada.append((nome, (r_ajustado, c)))
                else:
                    estrutura_ajustada.append((nome, (r, c)))

            cenario_atual += 1
            sys.stdout.write(f"\rCenário {cenario_atual}/{total_cenarios} - Equipa: {team}...")
            sys.stdout.flush()

            for match_idx in range(matches_per_structure):
                gs = GameState(time_limit_seconds=99999)
                is_greedy = (match_idx % 2 == 0)
                
                linhas_inimigas = [6, 7] if team == 'pretas' else [0, 1]
                team_inimiga = 'brancas' if team == 'pretas' else 'pretas'
                
                preencher_draft_estruturado(gs, team, linhas, estrutura_foco=estrutura_ajustada)
                preencher_draft_estruturado(gs, team_inimiga, linhas_inimigas)

                while not gs.game_over:
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
                        if is_greedy:
                            acoes_com_peso = [(acao, avaliar_peso_acao(gs, acao)) for acao in acoes_possiveis]
                            acoes_com_peso.sort(key=lambda x: x[1], reverse=True)
                            melhor_peso = acoes_com_peso[0][1]
                            melhores_acoes = [a[0] for a in acoes_com_peso if a[1] == melhor_peso]
                            acao_escolhida = random.choice(melhores_acoes)
                        else:
                            acao_escolhida = random.choice(acoes_possiveis)
                        
                        if acao_escolhida["type"] == "stun":
                            gs.make_action(acao_escolhida["start"], acao_escolhida["end"], "stun", acao_escolhida["area"])
                        else:
                            gs.make_action(acao_escolhida["start"], acao_escolhida["end"], acao_escolhida["type"])
                    else:
                        gs.check_game_over()
                        if not gs.game_over:
                            gs.game_over = True
                            gs.winner = "Erro de Sincronização"

                stats["total_matches"] += 1
                stats["outcomes"][gs.winner] += 1
                
                nomes = "_".join([nome for nome, pos in estrutura_ajustada])
                chave_posicao = f"{team}_Str[{nomes}]"
                
                dict_alvo = stats["structure_winrates_greedy"] if is_greedy else stats["structure_winrates_random"]
                dict_alvo[chave_posicao]["plays"] += 1
                
                # CORREÇÃO: Validar gs.winner antes do `in`
                if gs.winner and ((team == 'brancas' and "Brancas Vencem" in gs.winner) or (team == 'pretas' and "Pretas Vencem" in gs.winner)):
                    dict_alvo[chave_posicao]["wins"] += 1

    elapsed_time = time.time() - start_time
    print(f"\n\nConcluído em {elapsed_time:.2f} segundos.")
    with open("estatisticas_estruturas.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)

if __name__ == "__main__":
    run_exhaustive_simulation(matches_per_structure=20)