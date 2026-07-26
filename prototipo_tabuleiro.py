import pygame
import sys

# Configurações Iniciais
TAMANHO_CASA = 80
COLUNAS, LINHAS = 8, 8
LARGURA = COLUNAS * TAMANHO_CASA
ALTURA = LINHAS * TAMANHO_CASA

# Cores
COR_CLARA = (240, 217, 181)
COR_ESCURA = (181, 136, 99)
COR_SELECAO = (130, 151, 105)

def desenhar_tabuleiro(ecra, casa_selecionada):
    for linha in range(LINHAS):
        for coluna in range(COLUNAS):
            # Alternar cores
            cor = COR_CLARA if (linha + coluna) % 2 == 0 else COR_ESCURA
            
            # Destacar se estiver selecionada
            if casa_selecionada == (linha, coluna):
                cor = COR_SELECAO
                
            retangulo = pygame.Rect(coluna * TAMANHO_CASA, linha * TAMANHO_CASA, TAMANHO_CASA, TAMANHO_CASA)
            pygame.draw.rect(ecra, cor, retangulo)

def main():
    pygame.init()
    ecra = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Protótipo de Tabuleiro")
    
    casa_selecionada = None
    correr = True
    
    while correr:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                correr = False
                
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1: # Clique esquerdo
                    x, y = pygame.mouse.get_pos()
                    coluna = x // TAMANHO_CASA
                    linha = y // TAMANHO_CASA
                    
                    # Alternar seleção
                    if casa_selecionada == (linha, coluna):
                        casa_selecionada = None
                    else:
                        casa_selecionada = (linha, coluna)
                        print(f"Casa selecionada: Linha {linha}, Coluna {coluna}")

        desenhar_tabuleiro(ecra, casa_selecionada)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
