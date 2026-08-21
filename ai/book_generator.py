import sys
import os
import json
import random
import time
from collections import Counter
import concurrent.futures

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.game_state import GameState
from engine.config import ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS, LINHAS, COLUNAS
from engine.pieces import obter_catalogo_pecas
from ai.bot import BOT_INTERMEDIO # Usamos o Intermédio para gerar o livro mais depressa

ARQUIVO_LIVRO = os.path.join("data", "opening_book.json")

def gerar_draft_aleatorio(orcamento, linhas_validas):
    """Gera uma abertura válida e devolve a composição e a lista de peças."""
    catalogo = obter_catalogo_pecas()
    pontos = orcamento
    draft = []
    nomes = []
    
    for r in linhas_validas:
        for c in range(COLUNAS):
            validas = [p for p in catalogo if p["cost"] <= pontos]
            if not validas: break
            escolha = random.choice(validas)
            draft.append({
                "r": r, "c": c, 
                "name": escolha["name"], 
                "class_name": escolha["class"].__name__ # Guardamos o nome (string) em vez do objeto tipo
            })
            nomes.append(escolha["name"])
            pontos -= escolha["cost"]
            
    # Criar uma assinatura única para a abertura (ex: "1x BoneLord + 2x Ghoul")
    contagem = Counter(nomes)
    assinatura = " + ".join(sorted([f"{qtd}x {nome}" for nome, qtd in contagem.items()]))
    return draft, assinatura, orcamento - pontos

def simular_duelo_aberturas(draft_brancas, draft_pretas, seed):
    random.seed(seed)
    gs = GameState(time_limit_seconds=99999)
    
    # Aplicar aberturas no tabuleiro
    for pos in draft_brancas: gs.board[pos["r"]][pos["c"]] = pos["class_name"]('brancas')
    for pos in draft_pretas: gs.board[pos["r"]][pos["c"]] = pos["class"]('pretas')

    turnos = 0
    while not gs.game_over and turnos < 150:
        turnos += 1
        parsed = BOT_INTERMEDIO.play(gs)
        if parsed:
            gs.execute_action(parsed)
        else:
            gs.check_game_over()
            if not gs.game_over: gs.game_over, gs.winner = True, "Bloqueio"
            break

    if "Brancas" in str(gs.winner): return 1.0
    elif "Pretas" in str(gs.winner): return 0.0
    return 0.5

def treinar_livro_aberturas(iteracoes=50):
    print("📚 A GERAR LIVRO DE ABERTURAS POR SELF-PLAY...")
    
    # Carregar livro existente ou criar novo
    os.makedirs("data", exist_ok=True)
    if os.path.exists(ARQUIVO_LIVRO):
        with open(ARQUIVO_LIVRO, 'r') as f: livro = json.load(f)
    else:
        livro = {}

    start_time = time.time()
    
    for i in range(iteracoes):
        d_brancas, ass_b, desperdicio_b = gerar_draft_aleatorio(ORCAMENTO_BRANCAS, [LINHAS-2, LINHAS-1])
        d_pretas, ass_p, desperdicio_p = gerar_draft_aleatorio(ORCAMENTO_PRETAS, [0, 1])
        
        # Inicializar a assinatura no livro se não existir
        if ass_b not in livro: 
            livro[ass_b] = {
                "wins": 0, "games": 0, "winrate": 0.0, 
                "desperdicio": desperdicio_b, 
                "team": d_brancas
                }
        if ass_p not in livro:
            livro[ass_p] = {
                "wins": 0, "games": 0, "winrate": 0.0, 
                "desperdicio": desperdicio_p, 
                "team": d_pretas
                }
        
        # O duelo!
        resultado = simular_duelo_aberturas(d_brancas, d_pretas, random.randint(1, 99999))
        
        livro[ass_b]["games"] += 1
        livro[ass_p]["games"] += 1
        livro[ass_b]["wins"] += resultado
        livro[ass_p]["wins"] += (1.0 - resultado)
        
        livro[ass_b]["winrate"] = round((livro[ass_b]["wins"] / livro[ass_b]["games"]) * 100, 1)
        livro[ass_p]["winrate"] = round((livro[ass_p]["wins"] / livro[ass_p]["games"]) * 100, 1)
        
        sys.stdout.write(f"\rDuelos processados: {i+1}/{iteracoes} | Tempo: {time.time()-start_time:.1f}s")
        sys.stdout.flush()

    with open(ARQUIVO_LIVRO, 'w') as f:
        json.dump(livro, f, indent=4)
        
    print("\n\n✅ Livro atualizado! Aberturas guardadas em data/opening_book.json")

if __name__ == "__main__":
    treinar_livro_aberturas(50)