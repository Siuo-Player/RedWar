# Gestão da janela Pygame, eventos de input do rato e renderização base
import pygame

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
            cor = COR_CLARA if (linha + coluna) % 2 == 0 else COR_ESCURA
            if casa_selecionada == (linha, coluna):
                cor = COR_SELECAO
                
            retangulo = pygame.Rect(coluna * TAMANHO_CASA, linha * TAMANHO_CASA, TAMANHO_CASA, TAMANHO_CASA)
            pygame.draw.rect(ecra, cor, retangulo)