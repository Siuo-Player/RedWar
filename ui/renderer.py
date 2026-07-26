import pygame
from ui.window import TAMANHO_CASA, LARGURA

pygame.font.init()
FONTE = pygame.font.SysFont("Arial", 24, bold=True)
FONTE_PEQUENA = pygame.font.SysFont("Arial", 16, bold=True)

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
    for linha in range(8):
        for coluna in range(8):
            peca = board[linha][coluna]
            if peca is not None:
                x = coluna * TAMANHO_CASA
                y = linha * TAMANHO_CASA
                centro = (x + TAMANHO_CASA // 2, y + TAMANHO_CASA // 2)
                
                cor_base = (240, 240, 240) if peca.team == 'brancas' else (40, 40, 40)
                cor_borda = (0, 0, 0) if peca.team == 'brancas' else (255, 255, 255)
                
                if peca.stun_timer > 0:
                    cor_base = (100, 200, 255)

                raio = TAMANHO_CASA // 3
                
                if peca.name == "Bone" or peca.name == "BoneLord":
                    pygame.draw.circle(ecra, cor_base, centro, raio)
                    pygame.draw.circle(ecra, cor_borda, centro, raio, 2)
                    if peca.name == "BoneLord": 
                        pygame.draw.circle(ecra, (255, 215, 0), centro, raio//2)
                elif peca.name == "Sentry" or peca.name == "Obelisk":
                    rect = pygame.Rect(0, 0, raio*2, raio*2)
                    rect.center = centro
                    pygame.draw.rect(ecra, cor_base, rect)
                    pygame.draw.rect(ecra, cor_borda, rect, 2)
                elif peca.name == "Ghoul" or peca.name == "FrostMage":
                    pontos = [(centro[0], y + 15), (x + 15, y + TAMANHO_CASA - 15), (x + TAMANHO_CASA - 15, y + TAMANHO_CASA - 15)]
                    pygame.draw.polygon(ecra, cor_base, pontos)
                    pygame.draw.polygon(ecra, cor_borda, pontos, 2)

def format_time(seconds):
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins:02d}:{secs:02d}"

def desenhar_interface_batalha(ecra, gs):
    """Desenha os relógios durante o jogo."""
    rect_fundo = pygame.Rect(0, 8 * TAMANHO_CASA, LARGURA, 120)
    pygame.draw.rect(ecra, (30, 30, 30), rect_fundo)
    
    txt_pretas = FONTE.render(f"PRETAS: {format_time(gs.black_time)}", True, (255, 50, 50) if gs.black_time < 30 else (200, 200, 200))
    txt_brancas = FONTE.render(f"BRANCAS: {format_time(gs.white_time)}", True, (255, 50, 50) if gs.white_time < 30 else (255, 255, 255))
    
    ecra.blit(txt_pretas, (20, 8 * TAMANHO_CASA + 20))
    ecra.blit(txt_brancas, (LARGURA - 200, 8 * TAMANHO_CASA + 20))

def desenhar_loja_draft(ecra, pontos, timer, peca_selecionada, tempo_jogo_selecionado):
    rect_loja = pygame.Rect(0, 8 * TAMANHO_CASA, LARGURA, 120)
    pygame.draw.rect(ecra, (30, 30, 30), rect_loja)

    txt_pontos = FONTE.render(f"PONTOS: {pontos}", True, (255, 215, 0))
    txt_tempo = FONTE.render(f"DRAFT: {timer}s", True, (255, 50, 50) if timer < 10 else (255, 255, 255))
    ecra.blit(txt_pontos, (10, 8 * TAMANHO_CASA + 10))
    ecra.blit(txt_tempo, (LARGURA - 300, 8 * TAMANHO_CASA + 10))

    # Botão de Seleção de Tempo de Jogo
    btn_tempo = pygame.Rect(LARGURA - 450, 8 * TAMANHO_CASA + 10, 120, 30)
    pygame.draw.rect(ecra, (100, 150, 200), btn_tempo)
    txt_btn_tempo = FONTE_PEQUENA.render(f"JOGO: {tempo_jogo_selecionado//60} MIN", True, (0, 0, 0))
    ecra.blit(txt_btn_tempo, (LARGURA - 440, 8 * TAMANHO_CASA + 15))

    opcoes = [("Bone", 10), ("Ghoul", 30), ("Obelisk", 40), ("Sentry", 50), ("FrostMage", 60), ("BoneLord", 100)]
    for i, (nome, custo) in enumerate(opcoes):
        x = 10 + i * 100
        y = 8 * TAMANHO_CASA + 50
        cor = (100, 255, 100) if peca_selecionada == nome else (200, 200, 200)
        
        btn = pygame.Rect(x, y, 90, 40)
        pygame.draw.rect(ecra, cor, btn)
        pygame.draw.rect(ecra, (0, 0, 0), btn, 2)
        
        txt_nome = FONTE_PEQUENA.render(f"{nome}", True, (0, 0, 0))
        txt_custo = FONTE_PEQUENA.render(f"{custo} pts", True, (50, 50, 50))
        ecra.blit(txt_nome, (x + 5, y + 2))
        ecra.blit(txt_custo, (x + 5, y + 20))

    btn_ready = pygame.Rect(LARGURA - 110, 8 * TAMANHO_CASA + 50, 100, 40)
    pygame.draw.rect(ecra, (50, 200, 50), btn_ready)
    txt_ready = FONTE.render("READY", True, (0, 0, 0))
    ecra.blit(txt_ready, (LARGURA - 100, 8 * TAMANHO_CASA + 55))