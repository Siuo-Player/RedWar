import pygame
import sys
from ui.window import TAMANHO_CASA, COLUNAS, LINHAS, LARGURA, ALTURA, desenhar_tabuleiro

def main():
    pygame.init()
    ecra = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("RedWar - Arquitetura Limpa")
    
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

        desenhar_tabuleiro(ecra, casa_selecionada)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()