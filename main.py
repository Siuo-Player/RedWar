import pygame
import sys
import random
import time
from ui.window import TAMANHO_CASA, COLUNAS, LINHAS, LARGURA, ALTURA, desenhar_tabuleiro
from ui.renderer import desenhar_pecas, desenhar_destaques, desenhar_loja_draft, desenhar_interface_batalha
from engine.game_state import GameState
from engine.pieces import Bone, Ghoul, Obelisk, Sentry, FrostMage, BoneLord

ALTURA_TOTAL = ALTURA + 120 
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
    
    clock = pygame.time.Clock() # Necessário para o delta time
    fase_atual = "DRAFT" 
    
    # Variáveis de Draft
    pontos_jogador = 200
    peca_loja = None
    tempo_inicio_draft = time.time()
    opcoes_tempo_jogo = [60, 180, 600] # 1, 3 e 10 minutos
    idx_tempo = 1
    
    # O GameState será recriado ao clicar Ready para aplicar o tempo escolhido
    gs = GameState(time_limit_seconds=opcoes_tempo_jogo[idx_tempo]) 
    
    # Variáveis de Batalha
    casa_selecionada = None
    movimentos, ataques, stuns = [], [], {}
    
    correr = True
    while correr:
        dt = clock.tick(60) / 1000.0 # Segundos passados desde o último frame
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        linha_hover = mouse_y // TAMANHO_CASA
        coluna_hover = mouse_x // TAMANHO_CASA
        hover_pos = (linha_hover, coluna_hover)

        tempo_restante = max(0, 60 - int(time.time() - tempo_inicio_draft))

        # Atualizar relógio da batalha
        if fase_atual == "BATTLE" and not gs.game_over:
            gs.update_time(dt)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                correr = False
                
            elif evento.type == pygame.MOUSEBUTTONDOWN and not gs.game_over:
                if evento.button == 1:
                    x, y = pygame.mouse.get_pos()
                    
                    if fase_atual == "DRAFT":
                        if y >= ALTURA:
                            # Botão Ready
                            if x >= LARGURA - 110 and y >= ALTURA + 50:
                                auto_draft_ia(gs)
                                fase_atual = "BATTLE"
                            # Botão Tempo de Jogo
                            elif LARGURA - 450 <= x <= LARGURA - 330 and 8 * TAMANHO_CASA + 10 <= y <= 8 * TAMANHO_CASA + 40:
                                idx_tempo = (idx_tempo + 1) % len(opcoes_tempo_jogo)
                                # Transfere as peças colocadas para o novo GameState com o novo tempo
                                temp_board = gs.board
                                gs = GameState(time_limit_seconds=opcoes_tempo_jogo[idx_tempo])
                                gs.board = temp_board
                            # Comprar Peça
                            else:
                                opcoes = [("Bone", 10), ("Ghoul", 30), ("Obelisk", 40), ("Sentry", 50), ("FrostMage", 60), ("BoneLord", 100)]
                                for i, (nome, custo) in enumerate(opcoes):
                                    bx = 10 + i * 100
                                    by = ALTURA + 50
                                    if bx <= x <= bx + 90 and by <= y <= by + 40:
                                        peca_loja = nome if custo <= pontos_jogador else None
                        
                        elif peca_loja and y < ALTURA:
                            linha, coluna = y // TAMANHO_CASA, x // TAMANHO_CASA
                            if linha >= 6 and gs.board[linha][coluna] is None:
                                nova_peca = criar_peca_por_nome(peca_loja, 'brancas')
                                if nova_peca is not None: # <-- Correção do Pylance
                                    gs.board[linha][coluna] = nova_peca
                                    pontos_jogador -= nova_peca.cost
                                    peca_loja = None
                                
                    elif fase_atual == "BATTLE":
                        coluna = x // TAMANHO_CASA
                        linha = y // TAMANHO_CASA
                        alvo = (linha, coluna)
                        
                        if casa_selecionada == alvo:
                            casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                        elif casa_selecionada:
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
                                casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                        else:
                            peca_clicada = gs.board[linha][coluna] if linha < 8 else None
                            is_white = (peca_clicada and peca_clicada.team == 'brancas')
                            if peca_clicada and peca_clicada.can_act() and (is_white == gs.white_to_move):
                                casa_selecionada = alvo
                                movimentos = peca_clicada.get_valid_moves(linha, coluna, gs.board)
                                ataques = peca_clicada.get_valid_attacks(linha, coluna, gs.board)
                                stuns = peca_clicada.get_valid_stuns(linha, coluna, gs.board)

        ecra.fill((0, 0, 0))
        desenhar_tabuleiro(ecra, casa_selecionada)
        
        if fase_atual == "BATTLE":
            desenhar_destaques(ecra, movimentos, ataques, stuns, hover_pos)
            desenhar_interface_batalha(ecra, gs)
        elif fase_atual == "DRAFT":
            desenhar_loja_draft(ecra, pontos_jogador, tempo_restante, peca_loja, opcoes_tempo_jogo[idx_tempo])
            if tempo_restante == 0:
                auto_draft_ia(gs)
                fase_atual = "BATTLE"
                
        desenhar_pecas(ecra, gs.board)

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