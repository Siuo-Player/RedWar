import pygame
from ui.window import TAMANHO_CASA

def desenhar_destaques(ecra, movimentos, ataques, stuns_dict, hover_pos):
    surface = pygame.Surface((TAMANHO_CASA, TAMANHO_CASA), pygame.SRCALPHA)
    
    surface.fill((100, 200, 150, 150))
    for (r, c) in movimentos:
        ecra.blit(surface, (c * TAMANHO_CASA, r * TAMANHO_CASA))
        
    surface.fill((220, 50, 50, 150))
    for (r, c) in ataques:
        ecra.blit(surface, (c * TAMANHO_CASA, r * TAMANHO_CASA))

    for foco in stuns_dict.keys():
        if hover_pos == foco:
            surface.fill((100, 100, 100, 200)) 
        else:
            surface.fill((180, 180, 180, 130))
        ecra.blit(surface, (foco[1] * TAMANHO_CASA, foco[0] * TAMANHO_CASA))

    if hover_pos in stuns_dict:
        area_afetada = stuns_dict[hover_pos]
        for (ar, ac) in area_afetada:
            rect = pygame.Rect(ac * TAMANHO_CASA, ar * TAMANHO_CASA, TAMANHO_CASA, TAMANHO_CASA)
            pygame.draw.rect(ecra, (255, 255, 255), rect, 3) 

def desenhar_pecas(ecra, board):
    """Desenha formas geométricas simples para cada tipo de peça."""
    for linha in range(8):
        for coluna in range(8):
            peca = board[linha][coluna]
            if peca is not None:
                x = coluna * TAMANHO_CASA
                y = linha * TAMANHO_CASA
                centro = (x + TAMANHO_CASA // 2, y + TAMANHO_CASA // 2)
                
                # Cores base: Branco vs Preto
                cor_base = (240, 240, 240) if peca.team == 'brancas' else (40, 40, 40)
                cor_borda = (0, 0, 0) if peca.team == 'brancas' else (255, 255, 255)
                
                # Se estiver atordoada, força a cor para azul-gelo
                if peca.stun_timer > 0:
                    cor_base = (100, 200, 255)

                raio = TAMANHO_CASA // 3
                
                # Desenho dinâmico com base na classe
                if peca.name == "Bone":
                    # Círculo simples
                    pygame.draw.circle(ecra, cor_base, centro, raio)
                    pygame.draw.circle(ecra, cor_borda, centro, raio, 2)
                    
                elif peca.name == "Sentry":
                    # Quadrado centralizado
                    rect = pygame.Rect(0, 0, raio*2, raio*2)
                    rect.center = centro
                    pygame.draw.rect(ecra, cor_base, rect)
                    pygame.draw.rect(ecra, cor_borda, rect, 2)
                    
                elif peca.name == "FrostMage":
                    # Triângulo
                    pontos = [
                        (centro[0], y + 15), # Topo
                        (x + 15, y + TAMANHO_CASA - 15), # Esquerda
                        (x + TAMANHO_CASA - 15, y + TAMANHO_CASA - 15) # Direita
                    ]
                    pygame.draw.polygon(ecra, cor_base, pontos)
                    pygame.draw.polygon(ecra, cor_borda, pontos, 2)