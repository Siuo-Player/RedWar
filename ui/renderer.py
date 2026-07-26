# Lógica de desenho: traduz o game_state.py em imagens (tabuleiro, peças, seleções)
import pygame
from ui.window import TAMANHO_CASA

pygame.font.init()
FONTE = pygame.font.SysFont("Arial", 24, bold=True)

def desenhar_pecas(ecra, board):
    for linha in range(8):
        for coluna in range(8):
            peca = board[linha][coluna]
            if peca is not None:
                cor_texto = (255, 255, 255) if peca.team == 'brancas' else (0, 0, 0)
                texto_surface = FONTE.render(peca.acronym, True, cor_texto)
                
                rect = texto_surface.get_rect(center=(coluna * TAMANHO_CASA + TAMANHO_CASA // 2, 
                                                      linha * TAMANHO_CASA + TAMANHO_CASA // 2))
                
                if peca.team == 'brancas':
                    sombra = FONTE.render(peca.acronym, True, (50, 50, 50))
                    rect_sombra = sombra.get_rect(center=(coluna * TAMANHO_CASA + TAMANHO_CASA // 2 + 1, 
                                                          linha * TAMANHO_CASA + TAMANHO_CASA // 2 + 1))
                    ecra.blit(sombra, rect_sombra)

                ecra.blit(texto_surface, rect)