import pygame
import sys
import random
import time
from ui.window import TAMANHO_CASA, COLUNAS, LINHAS, LARGURA, ALTURA, desenhar_tabuleiro
from ui.renderer import desenhar_pecas, desenhar_destaques, desenhar_loja_draft
from engine.game_state import GameState
from engine.pieces import Bone, Ghoul, Obelisk, Sentry, FrostMage, BoneLord

ALTURA_TOTAL = ALTURA + 120 # Espaço para a loja
pygame.font.init()
FONTE_GAMEOVER = pygame.font.SysFont("Arial", 40, bold=True)

def criar_peca_por_nome(nome, team):
    if nome == "Bone": return Bone(team)
    if nome == "Ghoul": return Ghoul(team)
    if nome == "Obelisk": return Obelisk(team)
    if nome == "Sentry": return Sentry(team)
    if nome == "FrostMage": return FrostMage(team)
    if nome == "BoneLord": return BoneLord(team)
    return None

def auto_draft_ia(gs):
    """Preenche as linhas 0 e 1 de forma aleatória para a IA treinar."""
    pontos_ia = 200
    opcoes = [("Bone", 10), ("Ghoul", 30), ("Obelisk", 40), ("Sentry", 50), ("FrostMage", 60), ("BoneLord", 100)]
    for r in range(2):
        for c in range(8):
            opcoes_validas = [op for op in opcoes if op[1] <= pontos_ia]
            if not opcoes_validas: break
            escolha = random.choice(opcoes_validas)
            gs.board[r][c] = criar_peca_por_nome(escolha[0], 'pretas')
            pontos_ia -= escolha[1]

def main():
    pygame.init()
    ecra = pygame.display.set_mode((LARGURA, ALTURA_TOTAL))
    pygame.display.set_caption("RedWar - Combat Engine")
    
    gs = GameState()
    fase_atual = "DRAFT" # Pode ser "DRAFT" ou "BATTLE"
    
    # Variáveis de Draft
    pontos_jogador = 200
    peca_loja = None
    tempo_inicio = time.time()
    
    # Variáveis de Batalha
    casa_selecionada = None
    movimentos, ataques, stuns = [], [], {}
    
    correr = True
    while correr:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        linha_hover = mouse_y // TAMANHO_CASA
        coluna_hover = mouse_x // TAMANHO_CASA
        hover_pos = (linha_hover, coluna_hover)

        tempo_restante = max(0, 60 - int(time.time() - tempo_inicio))

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                correr = False
                
            elif evento.type == pygame.MOUSEBUTTONDOWN and not gs.game_over:
                if evento.button == 1:
                    x, y = pygame.mouse.get_pos()
                    
                    if fase_atual == "DRAFT":
                        # Clicar na loja
                        if y >= ALTURA:
                            if x >= LARGURA - 110 and y >= ALTURA + 50:
                                # Botão Ready Clicado
                                auto_draft_ia(gs)
                                fase_atual = "BATTLE"
                            else:
                                # Comprar peça
                                opcoes = [("Bone", 10), ("Ghoul", 30), ("Obelisk", 40), ("Sentry", 50), ("FrostMage", 60), ("BoneLord", 100)]
                                for i, (nome, custo) in enumerate(opcoes):
                                    bx = 10 + i * 100
                                    by = ALTURA + 50
                                    if bx <= x <= bx + 90 and by <= y <= by + 40:
                                        peca_loja = nome if custo <= pontos_jogador else None
                        
                        # Clicar no tabuleiro para colocar peça comprada
                        elif peca_loja and y < ALTURA:
                            linha, coluna = y // TAMANHO_CASA, x // TAMANHO_CASA
                            # Só permite colocar nas linhas 6 e 7 e em casas vazias
                            if linha >= 6 and gs.board[linha][coluna] is None:
                                nova_peca = criar_peca_por_nome(peca_loja, 'brancas')
                                gs.board[linha][coluna] = nova_peca
                                pontos_jogador -= nova_peca.cost
                                peca_loja = None
                                
                    elif fase_atual == "BATTLE":
                        coluna = x // TAMANHO_CASA
                        linha = y // TAMANHO_CASA
                        alvo = (linha, coluna)
                        
                        # Desselecionar ao clicar em si mesmo (Resolve o bug do Mago!)
                        if casa_selecionada == alvo:
                            casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                        elif casa_selecionada:
                            # Tentar executar ação
                            if alvo in movimentos:
                                gs.make_action(casa_selecionada, alvo, "move")
                                casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                            elif alvo in ataques:
                                gs.make_action(casa_selecionada, alvo, "attack")
                                casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                            elif alvo in stuns:
                                gs.make_action(casa_selecionada, alvo, "stun", affected_area=stuns[alvo])
                                casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                            else:
                                # Clicou noutro sítio inválido, limpa seleção
                                casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                        else:
                            # Selecionar nova peça
                            peca_clicada = gs.board[linha][coluna] if linha < 8 else None
                            is_white = (peca_clicada and peca_clicada.team == 'brancas')
                            if peca_clicada and peca_clicada.can_act() and (is_white == gs.white_to_move):
                                casa_selecionada = alvo
                                movimentos = peca_clicada.get_valid_moves(linha, coluna, gs.board)
                                ataques = peca_clicada.get_valid_attacks(linha, coluna, gs.board)
                                stuns = peca_clicada.get_valid_stuns(linha, coluna, gs.board)

        # Renderização Base
        ecra.fill((0, 0, 0))
        
        # Desenhar o mundo
        desenhar_tabuleiro(ecra, casa_selecionada)
        if fase_atual == "BATTLE":
            desenhar_destaques(ecra, movimentos, ataques, stuns, hover_pos)
        desenhar_pecas(ecra, gs.board)
        
        # UI Específica
        if fase_atual == "DRAFT":
            desenhar_loja_draft(ecra, pontos_jogador, tempo_restante, peca_loja)
            if tempo_restante == 0:
                auto_draft_ia(gs)
                fase_atual = "BATTLE"

        if gs.game_over:
            overlay = pygame.Surface((LARGURA, ALTURA_TOTAL), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) 
            ecra.blit(overlay, (0, 0))
            
            texto = FONTE_GAMEOVER.render(gs.winner, True, (255, 215, 0))
            rect_texto = texto.get_rect(center=(LARGURA//2, ALTURA_TOTAL//2))
            ecra.blit(texto, rect_texto)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()