import os
import pygame

C_FUNDO = (30, 30, 30)
C_BRANCO = (255, 255, 255)
C_PRETO = (0, 0, 0)

_CACHE_IMAGENS = {}

def carregar_imagem_peca(nome_peca, team, tam):
    chave = (nome_peca, team, tam)
    if chave in _CACHE_IMAGENS: 
        return _CACHE_IMAGENS[chave]
    
    caminho_pasta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "assets")
    caminho_completo = os.path.join(caminho_pasta, f"{nome_peca.lower()}.png")

    if os.path.exists(caminho_completo):
        img = pygame.image.load(caminho_completo).convert_alpha()
        img = pygame.transform.smoothscale(img, (int(tam * 0.8), int(tam * 0.8)))

        if team == 'pretas':
            cor_filtro = (40, 40, 40, 255) 
            img.fill(cor_filtro, special_flags=pygame.BLEND_RGBA_MULT)
        else:
            cor_filtro = (240, 245, 255, 255)
            img.fill(cor_filtro, special_flags=pygame.BLEND_RGBA_MULT)

        _CACHE_IMAGENS[chave] = img
        return img
        
    _CACHE_IMAGENS[chave] = None
    return None

def desenhar_tabuleiro(ecra, gs, tam_casa, off_x, off_y):
    # Destaques do Último Movimento (Estilo Chess.com)
    luzes_chess = []
    if hasattr(gs, 'last_move') and gs.last_move:
        luzes_chess.append(gs.last_move["start"])
        luzes_chess.append(gs.last_move["end"])

    for r in range(8):
        for c in range(8):
            cor = (200, 200, 200) if (r + c) % 2 == 0 else (100, 100, 100)
            
            # Pinta as casas do último movimento de amarelo translúcido
            if (r, c) in luzes_chess:
                cor = (230, 230, 120) if (r + c) % 2 == 0 else (180, 180, 80)

            rect = pygame.Rect(off_x + c * tam_casa, off_y + r * tam_casa, tam_casa, tam_casa)
            pygame.draw.rect(ecra, cor, rect)
            
            if gs.tile_effects and gs.tile_effects[r][c]:
                efeito = gs.tile_effects[r][c]["type"]
                if efeito == "ice":
                    s = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
                    s.fill((100, 200, 255, 150))
                    ecra.blit(s, (rect.x, rect.y))
                    pygame.draw.rect(ecra, (50, 150, 255), rect, 2)
                elif efeito == "fire":
                    s = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
                    s.fill((255, 100, 0, 80))
                    ecra.blit(s, (rect.x, rect.y))

def desenhar_destaques(ecra, gs, casa_selecionada, tam_casa, off_x, off_y):
    if not casa_selecionada: return
    r, c = casa_selecionada
    p = gs.board[r][c]
    if not p: return

    movimentos = p.get_valid_moves(r, c, gs.board, gs.tile_effects)
    ataques = p.get_valid_attacks(r, c, gs.board, gs.tile_effects)
    stuns = p.get_valid_stuns(r, c, gs.board, gs.tile_effects)
    spawns = p.get_valid_spawns(r, c, gs.board, gs.tile_effects)

    s_move = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
    s_move.fill((100, 255, 100, 100))  
    s_spawn = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
    s_spawn.fill((200, 100, 255, 100)) 

    for mr, mc in movimentos:
        ecra.blit(s_move, (off_x + mc * tam_casa, off_y + mr * tam_casa))

    for sr, sc, sname in spawns:
        ecra.blit(s_spawn, (off_x + sc * tam_casa, off_y + sr * tam_casa))

    for ar, ac in ataques:
        rect_atk = pygame.Rect(off_x + ac * tam_casa, off_y + ar * tam_casa, tam_casa, tam_casa)
        s_atk = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
        s_atk.fill((255, 80, 80, 80))
        ecra.blit(s_atk, (rect_atk.x, rect_atk.y))
        pygame.draw.rect(ecra, (255, 50, 50), rect_atk, 4)

    # UI DO MAGO CORRIGIDA
    for foco_r, foco_c in stuns.keys():
        info = stuns[(foco_r, foco_c)]
        cx = off_x + foco_c * tam_casa + tam_casa // 2
        cy = off_y + foco_r * tam_casa + tam_casa // 2
        compr = tam_casa // 4
        
        # Se tem inimigo, cruz é azul viva. Se está vazio, cruz é cinza desbotada.
        cor_cruz = (0, 200, 255) if info["has_enemy"] else (150, 150, 150)
        
        pygame.draw.line(ecra, cor_cruz, (cx - compr, cy), (cx + compr, cy), 5)
        pygame.draw.line(ecra, cor_cruz, (cx, cy - compr), (cx, cy + compr), 5)
        
        for (aoe_r, aoe_c) in info["aoe"]:
            rect_aoe = pygame.Rect(off_x + aoe_c * tam_casa + 2, off_y + aoe_r * tam_casa + 2, tam_casa - 4, tam_casa - 4)
            pygame.draw.rect(ecra, cor_cruz, rect_aoe, 2)

def desenhar_pecas(ecra, board, tam_casa, off_x, off_y):
    fonte = pygame.font.SysFont("arial", int(tam_casa * 0.4))
    fonte_vida = pygame.font.SysFont("arial", int(tam_casa * 0.3), bold=True)
    
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p:
                cx = off_x + c * tam_casa + tam_casa // 2
                cy = off_y + r * tam_casa + tam_casa // 2
                
                img = carregar_imagem_peca(p.name, p.team, tam_casa)
                if img:
                    cor_base = (100, 140, 200) if p.team == 'brancas' else (200, 80, 80)
                    pygame.draw.circle(ecra, cor_base, (cx, cy), int(tam_casa * 0.38))
                    pygame.draw.circle(ecra, (20, 20, 20), (cx, cy), int(tam_casa * 0.38), 2)
                    ecra.blit(img, img.get_rect(center=(cx, cy)))
                else:
                    cor_peca = (230, 230, 230) if p.team == 'brancas' else (50, 50, 50)
                    pygame.draw.circle(ecra, cor_peca, (cx, cy), int(tam_casa * 0.38))
                    cor_texto = C_PRETO if p.team == 'brancas' else C_BRANCO
                    sigla = "BL" if p.name == "BoneLord" else p.name[:2].capitalize()
                    texto = fonte.render(sigla, True, cor_texto)
                    ecra.blit(texto, texto.get_rect(center=(cx, cy)))
                
                if p.stun_timer > 0:
                    pygame.draw.circle(ecra, (0, 150, 255), (cx, cy), int(tam_casa * 0.42), 4)

                if hasattr(p, 'lifespan') and p.lifespan is not None:
                    txt_vida = fonte_vida.render(str(p.lifespan), True, (255, 50, 50))
                    pos_x = off_x + c * tam_casa + tam_casa - int(tam_casa * 0.25)
                    pos_y = off_y + r * tam_casa + int(tam_casa * 0.05)
                    sombra = fonte_vida.render(str(p.lifespan), True, C_PRETO)
                    ecra.blit(sombra, (pos_x + 1, pos_y + 1))
                    ecra.blit(txt_vida, (pos_x, pos_y))

def desenhar_log(ecra, gs, off_x_log, off_y, width, height):
    """Desenha o histórico de ações no lado direito do ecrã."""
    pygame.draw.rect(ecra, (40, 40, 40), (off_x_log, off_y, width, height), border_radius=10)
    fonte_tit = pygame.font.SysFont("arial", 24, bold=True)
    fonte_txt = pygame.font.SysFont("arial", 16)
    
    tit = fonte_tit.render("Registo de Batalha", True, C_BRANCO)
    ecra.blit(tit, (off_x_log + 20, off_y + 20))
    pygame.draw.line(ecra, (100, 100, 100), (off_x_log + 20, off_y + 50), (off_x_log + width - 20, off_y + 50), 2)
    
    y = off_y + 60
    # Mostra os últimos 12 turnos para caber no painel
    for log in gs.move_log[-12:]:
        cor_txt = (150, 200, 255) if log["team"] == "brancas" else (255, 150, 150)
        txt_short = fonte_tit.render(log["short"], True, cor_txt)
        txt_full = fonte_txt.render(log["full"], True, (200, 200, 200))
        
        ecra.blit(txt_short, (off_x_log + 20, y))
        ecra.blit(txt_full, (off_x_log + 20, y + 25))
        y += 55

def desenhar_loja_dinamica(ecra, w, h, catalogo, pontos, peca_selecionada, off_y):
    fonte_tit = pygame.font.SysFont("arial", 36)
    fonte_item = pygame.font.SysFont("arial", 24)
    
    txt_pts = fonte_tit.render(f"Orçamento Restante: {pontos} pts", True, C_BRANCO)
    ecra.blit(txt_pts, (20, off_y))
    
    botoes = {}
    x_base = 20
    y_base = off_y + 40
    espaco_x = 110
    
    for i, item in enumerate(catalogo):
        x = x_base + (i % 6) * espaco_x
        y = y_base + (i // 6) * 60
        
        cor_btn = (100, 200, 100) if item["name"] == peca_selecionada else (80, 80, 80)
        if item["cost"] > pontos:
            cor_btn = (150, 50, 50)
            
        rect = pygame.Rect(x, y, 100, 50)
        pygame.draw.rect(ecra, cor_btn, rect, border_radius=5)
        
        nome_txt = fonte_item.render(item["name"], True, C_BRANCO)
        custo_txt = fonte_item.render(f"{item['cost']} pts", True, C_BRANCO)
        
        ecra.blit(nome_txt, (x + 5, y + 5))
        ecra.blit(custo_txt, (x + 5, y + 25))
        
        if item["cost"] <= pontos:
            botoes[item["name"]] = rect
            
    btn_ready = pygame.Rect(w - 150, off_y, 130, 40)
    pygame.draw.rect(ecra, (50, 150, 250), btn_ready, border_radius=5)
    txt_ready = fonte_tit.render("Pronto!", True, C_BRANCO)
    ecra.blit(txt_ready, (btn_ready.x + 20, btn_ready.y + 10))
    
    btn_info = pygame.Rect(w - 150, off_y + 50, 130, 40)
    pygame.draw.rect(ecra, (200, 150, 50), btn_info, border_radius=5)
    txt_info = fonte_tit.render("Info", True, C_BRANCO)
    ecra.blit(txt_info, (btn_info.x + 40, btn_info.y + 10))
    
    return botoes, btn_ready, btn_info

def desenhar_enciclopedia(ecra, w, h, catalogo):
    fonte_tit = pygame.font.SysFont("arial", 48)
    fonte_sub = pygame.font.SysFont("arial", 32)
    fonte_desc = pygame.font.SysFont("arial", 24)
    
    txt_tit = fonte_tit.render("Enciclopédia de Peças", True, C_BRANCO)
    ecra.blit(txt_tit, (w//2 - txt_tit.get_width()//2, 20))
    
    y = 80
    for item in catalogo:
        txt_nome = fonte_sub.render(f"{item['name']} ({item['cost']} pts)", True, (200, 200, 100))
        ecra.blit(txt_nome, (50, y))
        y += 30
        txt_d = fonte_desc.render(f"Descrição: {item['desc']}", True, C_BRANCO)
        ecra.blit(txt_d, (70, y))
        y += 25
        txt_p = fonte_desc.render(f"Passiva: {item['passiva']}", True, (150, 200, 255))
        ecra.blit(txt_p, (70, y))
        y += 40
        
    btn_voltar = pygame.Rect(w//2 - 60, h - 60, 120, 40)
    pygame.draw.rect(ecra, (150, 50, 50), btn_voltar, border_radius=5)
    txt_voltar = fonte_sub.render("Voltar", True, C_BRANCO)
    ecra.blit(txt_voltar, (btn_voltar.x + 25, btn_voltar.y + 10))
    
    return btn_voltar