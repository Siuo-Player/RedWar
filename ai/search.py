from ai.evaluator import avaliador_mestre
import random

from engine.actions import normalize_action


def get_all_moves_for_analysis(gs):
    # Gerador simplificado que extrai todas as jogadas legais num formato listável
    acoes = []
    current_team = 'brancas' if gs.white_to_move else 'pretas'
    for r in range(len(gs.board)):
        for c in range(len(gs.board[0])):
            p = gs.board[r][c]
            if p and p.team == current_team and p.stun_timer == 0:
                for mv in p.get_valid_moves(r, c, gs.board, gs.tile_effects):
                    acoes.append({"start": (r, c), "end": mv, "type": "move"})
                for at in p.get_valid_attacks(r, c, gs.board, gs.tile_effects):
                    acoes.append({"start": (r, c), "end": at, "type": "attack"})
    return acoes


def analisar_posicao_continuamente(gs, max_depth=6):
    """
    Usa Iterative Deepening para analisar uma posição.
    A cada profundidade alcançada, faz um yield do Top 5 dos movimentos.
    """
    acoes = get_all_moves_for_analysis(gs)
    if not acoes:
        yield 0, []
        return

    # Inicia as pontuações a zeros
    for a in acoes: a["score"] = 0

    # Iterative Deepening clássico
    for depth in range(1, max_depth + 1):
        for acao in acoes:
            # Simula a jogada e usa o avaliador base (apenas 1 nível por agora para ser em tempo real)
            # Numa engine completa, isto desceria recursivamente.
            gs_clone = gs.fast_clone()
            gs_clone.execute_action(normalize_action(acao))

            # Perspetiva do Avaliador (Sempre negativo para o oponente)
            score = -avaliador_mestre(gs_clone)

            # Adiciona um pequeno ruído para desempatar jogadas iguais
            acao["score"] = score + random.randint(-10, 10)

        # Ordena do melhor para o pior
        acoes.sort(key=lambda x: x["score"], reverse=True)

        # Devolve o Top 5 a esta profundidade para o UI desenhar
        yield depth, acoes[:5]
