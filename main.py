import pygame
import sys
from ui.window import TAMANHO_CASA, COLUNAS, LINHAS, LARGURA, ALTURA, desenhar_tabuleiro
from ui.renderer import desenhar_pecas
from engine.game_state import GameState

def main():
    pygame.init()
    ecra = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("RedWar - Movimento vs Ataque")
    
    gs = GameState()
    casa_selecionada = None
    correr = True
    
    while correr:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                correr = False
                
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    x, y = pygame.mouse.get_pos()
                    coluna = x // TAMANHO_CASA
                    linha = y // TAMANHO_CASA
                    
                    if casa_selecionada == (linha, coluna):
                        casa_selecionada = None
                    else:
                        casa_selecionada = (linha, coluna)
                        peca_clicada = gs.board[linha][coluna]
                        
                        if peca_clicada:
                            print(f"\n--- {peca_clicada.name} ({peca_clicada.team}) ---")
                            movimentos = peca_clicada.get_valid_moves(linha, coluna, gs.board)
                            ataques = peca_clicada.get_valid_attacks(linha, coluna, gs.board)
                            print(f"Pode MOVER para: {movimentos}")
                            print(f"Pode ATACAR em: {ataques}")

        desenhar_tabuleiro(ecra, casa_selecionada)
        desenhar_pecas(ecra, gs.board) 
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()