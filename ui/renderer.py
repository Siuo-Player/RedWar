# ui/renderer.py
import pygame

C_FUNDO = (30, 30, 35)
C_TABULEIRO_ESCURO = (118, 150, 86)
C_TABULEIRO_CLARO = (238, 238, 210)
C_TEXTO = (255, 255, 255)

def desenhar_tabuleiro(ecra, tam_casa, off_x, off_y):
    for r in range(8):
        for c in range(8):
            cor = C_TABULEIRO_CLARO if (r + c) % 2 == 0 else C_TABULEIRO_ESCURO
            pygame.draw.rect(ecra, cor, (off_x + c * tam_casa, off_y + r * tam_casa, tam_casa, tam_casa))

def desenhar_pecas(ecra, board, tam_casa, off_x, off_y):
    fonte = pygame.font.SysFont(None, int(tam_casa * 0.4))
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p:
                cx, cy = off_x + c * tam_casa + tam_casa//2, off_y + r * tam_casa + tam_casa//2
                cor_peca = (220, 220, 220) if p.team == 'brancas' else (40, 40, 40)
                pygame.draw.circle(ecra, cor_peca, (cx, cy), int(tam_casa * 0.4))
                
                cor_texto = (0, 0, 0) if p.team == 'brancas' else (255, 255, 255)
                texto = fonte.render(p.acronym, True, cor_texto)
                rect_texto = texto.get_rect(center=(cx, cy))
                ecra.blit(texto, rect_texto)
                
                if p.stun_timer > 0:
                    pygame.draw.circle(ecra, (0, 200, 255), (cx, cy), int(tam_casa * 0.45), 3)

def desenhar_loja_dinamica(ecra, largura, altura, catalogo, pts, peca_sel, off_y_loja):
    fonte = pygame.font.SysFont(None, 24)
    txt_pts = fonte.render(f"Orçamento: {pts} pts", True, (255,215,0))
    ecra.blit(txt_pts, (20, off_y_loja + 10))
    
    # Desenhar botão Enciclopédia
    btn_info = pygame.Rect(largura - 120, off_y_loja + 10, 100, 30)
    pygame.draw.rect(ecra, (50, 100, 200), btn_info, border_radius=5)
    ecra.blit(fonte.render("📖 INFO", True, C_TEXTO), (btn_info.x + 20, btn_info.y + 7))

    x_ini, y_ini = 20, off_y_loja + 50
    espaco = 90
    botoes = {}
    
    for i, item in enumerate(catalogo):
        bx = x_ini + (i % 6) * espaco
        by = y_ini + (i // 6) * 50
        rect = pygame.Rect(bx, by, 80, 40)
        
        cor = (80, 150, 80) if item["cost"] <= pts else (100, 100, 100)
        if peca_sel == item["name"]: cor = (200, 150, 50)
        
        pygame.draw.rect(ecra, cor, rect, border_radius=5)
        txt = fonte.render(f"{item['name']} ({item['cost']})", True, (255,255,255))
        ecra.blit(txt, (bx + 5, by + 12))
        botoes[item["name"]] = rect
        
    # Botão Ready
    btn_ready = pygame.Rect(largura - 120, off_y_loja + 60, 100, 40)
    pygame.draw.rect(ecra, (200, 50, 50), btn_ready, border_radius=5)
    ecra.blit(fonte.render("READY", True, C_TEXTO), (btn_ready.x + 20, btn_ready.y + 12))
    
    return botoes, btn_ready, btn_info

def desenhar_enciclopedia(ecra, largura, altura, catalogo):
    ecra.fill(C_FUNDO)
    fonte_tit = pygame.font.SysFont(None, 48)
    fonte_txt = pygame.font.SysFont(None, 24)
    
    ecra.blit(fonte_tit.render("📖 Enciclopédia de Batalha", True, (255,215,0)), (40, 40))
    
    y = 120
    for p in catalogo:
        nome = fonte_tit.render(f"{p['name']} [{p['cost']} pts]", True, (200,200,200))
        ecra.blit(nome, (40, y))
        ecra.blit(fonte_txt.render(f"Função: {p['desc']}", True, (150,200,150)), (60, y + 40))
        ecra.blit(fonte_txt.render(f"Passiva: {p['passiva']}", True, (200,150,150)), (60, y + 65))
        y += 110

    btn_voltar = pygame.Rect(largura - 150, 40, 120, 40)
    pygame.draw.rect(ecra, (100, 100, 100), btn_voltar, border_radius=5)
    ecra.blit(fonte_txt.render("VOLTAR", True, C_TEXTO), (btn_voltar.x + 25, btn_voltar.y + 12))
    return btn_voltar