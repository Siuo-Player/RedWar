import pygame
from ui.window import TAMANHO_CASA

pygame.font.init()
FONTE = pygame.font.SysFont("Arial", 24, bold=True)

def desenhar_destaques(ecra, movimentos, ataques, stuns_dict, hover_pos):
    """Cria os overlays transparentes para as ações válidas e desenha a Box Branca."""
    surface = pygame.Surface((TAMANHO_CASA, TAMANHO_CASA), pygame.SRCALPHA)
    
    # 1. Movimentos (Verde/Ciano Transparente)
    surface.fill((100, 200, 150, 150))
    for (r, c) in movimentos:
        ecra.blit(surface, (c * TAMANHO_CASA, r * TAMANHO_CASA))
        
    # 2. Ataques (Vermelho Transparente)
    surface.fill((220, 50, 50, 150))
    for (r, c) in ataques:
        ecra.blit(surface, (c * TAMANHO_CASA, r * TAMANHO_CASA))

    # 3. Focos de Stun (Cinza)
    for foco in stuns_dict.keys():
        if hover_pos == foco:
            surface.fill((100, 100, 100, 200)) # Cinza Escuro (Mouse em cima)
        else:
            surface.fill((180, 180, 180, 130)) # Cinza Claro
        ecra.blit(surface, (foco[1] * TAMANHO_CASA, foco[0] * TAMANHO_CASA))

    # 4. Box Branca (Se o rato estiver num Foco válido)
    if hover_pos in stuns_dict:
        area_afetada = stuns_dict[hover_pos]
        for (ar, ac) in area_afetada:
            rect = pygame.Rect(ac * TAMANHO_CASA, ar * TAMANHO_CASA, TAMANHO_CASA, TAMANHO_CASA)
            # draw.rect com espessura (width=3) desenha apenas a borda (a tua "box")
            pygame.draw.rect(ecra, (255, 255, 255), rect, 3) 

def desenhar_pecas(ecra, board):
    for linha in range(8):
        for coluna in range(8):
            peca = board[linha][coluna]
            if peca is not None:
                cor_texto = (255, 255, 255) if peca.team == 'brancas' else (0, 0, 0)
                
                # Se a peça estiver atordoada, escreve [STUNNED] em cima dela
                if peca.stun_timer > 0:
                    cor_texto = (100, 200, 255) # Azul gelo para indicar atordoamento
                    
                texto_surface = FONTE.render(peca.acronym, True, cor_texto)
                rect = texto_surface.get_rect(center=(coluna * TAMANHO_CASA + TAMANHO_CASA // 2, 
                                                      linha * TAMANHO_CASA + TAMANHO_CASA // 2))
                
                if peca.team == 'brancas':
                    sombra = FONTE.render(peca.acronym, True, (50, 50, 50))
                    rect_sombra = sombra.get_rect(center=(coluna * TAMANHO_CASA + TAMANHO_CASA // 2 + 1, 
                                                          linha * TAMANHO_CASA + TAMANHO_CASA // 2 + 1))
                    ecra.blit(sombra, rect_sombra)

                ecra.blit(texto_surface, rect)