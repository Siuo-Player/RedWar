import sys
import os
import random
import json
from collections import defaultdict

# Garantir que o Python encontra a pasta engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from engine.pieces import Bone, Ghoul, Obelisk, Sentry, FrostMage, BoneLord

def criar_peca_por_nome(nome, team):
    if nome == "Bone": return Bone(team)
    if nome == "Ghoul": return Ghoul(team)
    if nome == "Obelisk": return Obelisk(team)
    if nome == "Sentry": return Sentry(team)
    if nome == "FrostMage": return FrostMage(team)
    if nome == "BoneLord": return BoneLord(team)
    return None

def preencher_draft_aleatorio(gs, team, linhas):
    pontos = 200
    opcoes = [("Bone", 10), ("Ghoul", 30), ("Obelisk", 40), ("Sentry", 50), ("FrostMage", 60), ("BoneLord", 100)]
    for r in linhas:
        for c in range(8):
            validas = [op for op in opcoes if op[1] <= pontos]
            if not validas: break
            escolha = random.choice(validas)
            gs.board[r][c] = criar_peca_por_nome(escolha[0], team)
            pontos -= escolha[1]

def run_simulation(num_matches=1000):
    stats = {
        "total_matches": 0,
        "outcomes": defaultdict(int),
        "piece_usage": defaultdict(int),
        "piece_wins": defaultdict(int),
        "action_types": defaultdict(int),
        "heatmap": [[0 for _ in range(8)] for _ in range(8)]
    }

    print(f"A iniciar simulação de {num_matches} partidas (Headless)...")

    for i in range(num_matches):
        gs = GameState(time_limit_seconds=99999) # Tempo infinito, simulação baseada em turnos
        
        preencher_draft_aleatorio(gs, 'pretas', [0, 1])
        preencher_draft_aleatorio(gs, 'brancas', [6, 7])
        
        # Registar que peças entraram em jogo
        pecas_iniciais = {'brancas': [], 'pretas': []}
        for r in range(8):
            for c in range(8):
                p = gs.board[r][c]
                if p:
                    stats["piece_usage"][p.name] += 1
                    pecas_iniciais[p.team].append(p.name)

        # Loop de Batalha Aleatória
        while not gs.game_over:
            current_team = 'brancas' if gs.white_to_move else 'pretas'
            acoes_possiveis = []
            
            for r in range(8):
                for c in range(8):
                    p = gs.board[r][c]
                    if p and p.team == current_team and p.can_act():
                        for move in p.get_valid_moves(r, c, gs.board):
                            acoes_possiveis.append({"start": (r, c), "end": move, "type": "move"})
                        for atk in p.get_valid_attacks(r, c, gs.board):
                            acoes_possiveis.append({"start": (r, c), "end": atk, "type": "attack"})
                        for foco, area in p.get_valid_stuns(r, c, gs.board).items():
                            acoes_possiveis.append({"start": (r, c), "end": foco, "type": "stun", "area": area})
            
            if acoes_possiveis:
                # O Agente "Random" escolhe uma ação à sorte
                acao = random.choice(acoes_possiveis)
                stats["action_types"][acao["type"]] += 1
                stats["heatmap"][acao["end"][0]][acao["end"][1]] += 1
                
                if acao["type"] == "stun":
                    gs.make_action(acao["start"], acao["end"], "stun", acao["area"])
                else:
                    gs.make_action(acao["start"], acao["end"], acao["type"])
            else:
                # Força verificação se quebrou
                gs.check_game_over()
                if not gs.game_over:
                    # Segurança: não devia acontecer com a nova regra, mas evita loops infinitos
                    gs.game_over = True
                    gs.winner = "Erro de Sincronização de Turno"

        # Registar Resultados
        stats["total_matches"] += 1
        winner_reason = gs.winner if gs.winner else "Desconhecido"
        stats["outcomes"][winner_reason] += 1
        
        # Registar Win-Rate das Peças
        if "Brancas Vencem" in winner_reason:
            for nome in pecas_iniciais['brancas']: stats["piece_wins"][nome] += 1
        elif "Pretas Vencem" in winner_reason:
            for nome in pecas_iniciais['pretas']: stats["piece_wins"][nome] += 1

        if (i + 1) % 100 == 0:
            print(f"{i + 1} partidas concluídas...")

    # Guardar para JSON
    with open("estatisticas_treino.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)
        
    print("Treino concluído! Resultados guardados em 'estatisticas_treino.json'.")

if __name__ == "__main__":
    run_simulation()