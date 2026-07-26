import pygame
import sys
from ui.window import TAMANHO_CASA, COLUNAS, LINHAS, LARGURA, ALTURA, desenhar_tabuleiro
from ui.renderer import desenhar_pecas, desenhar_destaques
from engine.game_state import GameState

pygame.font.init()
FONTE_GAMEOVER = pygame.font.SysFont("Arial", 40, bold=True)

def main():
    pygame.init()
    ecra = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("RedWar - Game Over & AI Setup")
    
    gs = GameState()
    casa_selecionada = None
    movimentos, ataques, stuns = [], [], {}
    correr = True
    
    while correr:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hover_pos = (mouse_y // TAMANHO_CASA, mouse_x // TAMANHO_CASA)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                correr = False
                
            elif evento.type == pygame.MOUSEBUTTONDOWN and not gs.game_over:
                if evento.button == 1:
                    x, y = pygame.mouse.get_pos()
                    coluna = x // TAMANHO_CASA
                    linha = y // TAMANHO_CASA
                    alvo = (linha, coluna)
                    
                    if casa_selecionada:
                        if alvo in movimentos:
                            gs.make_action(casa_selecionada, alvo, "move")
                            casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                            continue
                        elif alvo in ataques:
                            gs.make_action(casa_selecionada, alvo, "attack")
                            casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                            continue
                        elif alvo in stuns:
                            gs.make_action(casa_selecionada, alvo, "stun", affected_area=stuns[alvo])
                            casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                            continue

                    if casa_selecionada == alvo:
                        casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                    else:
                        peca_clicada = gs.board[linha][coluna]
                        is_white = (peca_clicada and peca_clicada.team == 'brancas')
                        if peca_clicada and peca_clicada.can_act() and (is_white == gs.white_to_move):
                            casa_selecionada = alvo
                            movimentos = peca_clicada.get_valid_moves(linha, coluna, gs.board)
                            ataques = peca_clicada.get_valid_attacks(linha, coluna, gs.board)
                            stuns = peca_clicada.get_valid_stuns(linha, coluna, gs.board)
                        else:
                            casa_selecionada, movimentos, ataques, stuns = None, [], [], {}

        desenhar_tabuleiro(ecra, casa_selecionada)
        desenhar_destaques(ecra, movimentos, ataques, stuns, hover_pos)
        desenhar_pecas(ecra, gs.board)
        
        # UI DE FIM DE JOGO
        if gs.game_over:
            overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) # Ecrã escurece 
            ecra.blit(overlay, (0, 0))
            
            texto = FONTE_GAMEOVER.render(gs.winner, True, (255, 215, 0)) # Dourado
            rect_texto = texto.get_rect(center=(LARGURA//2, ALTURA//2))
            ecra.blit(texto, rect_texto)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()