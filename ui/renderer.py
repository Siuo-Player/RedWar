import os
import pygame

C_FUNDO = (30, 30, 30)
C_BRANCO = (255, 255, 255)
C_PRETO = (0, 0, 0)
C_AZUL = (50, 150, 255)
C_VERMELHO = (255, 50, 50)

_CACHE_IMAGENS = {}

def carregar_imagem_peca(nome_peca, team, tam):
    chave = (nome_peca, team, tam)
    if chave in _CACHE_IMAGENS: return _CACHE_IMAGENS[chave]
    caminho_pasta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ui", "assets")
    caminho_completo = os.path.join(caminho_pasta, f"{nome_peca.lower()}.png")

    if os.path.exists(caminho_completo):
        img = pygame.image.load(caminho_completo).convert_alpha()
        img = pygame.transform.smoothscale(img, (int(tam * 0.8), int(tam * 0.8)))
        if team == 'pretas': img.fill((40, 40, 40, 255), special_flags=pygame.BLEND_RGBA_MULT)
        else: img.fill((240, 245, 255, 255), special_flags=pygame.BLEND_RGBA_MULT)
        _CACHE_IMAGENS[chave] = img
        return img
    _CACHE_IMAGENS[chave] = None
    return None

def desenhar_menu_principal(ecra, w, h):
    ecra.fill(C_FUNDO)
    fonte_tit = pygame.font.SysFont("arial", 64, bold=True)
    txt_tit = fonte_tit.render("REDWAR", True, C_VERMELHO)
    ecra.blit(txt_tit, (w//2 - txt_tit.get_width()//2, h//4))
    
    btn_start = pygame.Rect(w//2 - 150, h//2, 300, 60)
    pygame.draw.rect(ecra, C_AZUL, btn_start, border_radius=10)
    txt_s = pygame.font.SysFont("arial", 32).render("Começar Batalha", True, C_BRANCO)
    ecra.blit(txt_s, (w//2 - txt_s.get_width()//2, h//2 + 10))
    
    btn_info = pygame.Rect(w//2 - 150, h//2 + 80, 300, 60)
    pygame.draw.rect(ecra, (100, 100, 100), btn_info, border_radius=10)
    txt_i = pygame.font.SysFont("arial", 32).render("Enciclopédia", True, C_BRANCO)
    ecra.blit(txt_i, (w//2 - txt_i.get_width()//2, h//2 + 90))
    
    return btn_start, btn_info

# MUDANÇA APENAS NA FUNÇÃO desenhar_selecao_dificuldade DENTRO DE ui/renderer.py

def desenhar_selecao_dificuldade(ecra, w, h, elo_atual):
    """
    Substitui a função anterior no ficheiro ui/renderer.py.
    Mostra apenas o slider do ELO, visto que o tempo é calculado com base nele.
    """
    ecra.fill(C_FUNDO)
    fonte = pygame.font.SysFont("arial", 36)
    
    txt_tit = fonte.render("Configurar Adversário (IA)", True, C_BRANCO)
    ecra.blit(txt_tit, (w//2 - txt_tit.get_width()//2, 50))
    
    # ELO Slider Representativo (100 a 2600)
    pygame.draw.rect(ecra, (50, 50, 50), (w//2 - 200, 150, 400, 20))
    x_elo = w//2 - 200 + int(((elo_atual - 100) / 2500) * 400)
    rect_elo_drag = pygame.Rect(x_elo - 10, 140, 20, 40)
    pygame.draw.rect(ecra, C_VERMELHO, rect_elo_drag)
    txt_elo = fonte.render(f"Rating ELO Desejado: {elo_atual}", True, C_BRANCO)
    ecra.blit(txt_elo, (w//2 - txt_elo.get_width()//2, 100))
    
    # Calcula o tempo e limite visualmente para apresentar ao jogador
    if elo_atual <= 300:
        tempo_aprox = 0.05
    else:
        tempo_aprox = ((elo_atual - 300) / 2300.0) * 5.0
        
    fonte_aviso = pygame.font.SysFont("arial", 20)
    txt_aviso = fonte_aviso.render(f"Poder Computacional Estimado: A IA vai pensar {tempo_aprox:.2f}s por turno.", True, (150, 200, 255))
    ecra.blit(txt_aviso, (w//2 - txt_aviso.get_width()//2, 220))
    
    if tempo_aprox > 2.0:
        txt_alerta = fonte_aviso.render("Aviso: ELOs altos causam longos tempos de processamento do tabuleiro.", True, (255, 150, 50))
        ecra.blit(txt_alerta, (w//2 - txt_alerta.get_width()//2, 260))
    
    btn_confirmar = pygame.Rect(w//2 - 100, 350, 200, 50)
    pygame.draw.rect(ecra, (100, 200, 100), btn_confirmar, border_radius=5)
    txt_c = pygame.font.SysFont("arial", 28).render("Confirmar", True, C_BRANCO)
    ecra.blit(txt_c, (w//2 - txt_c.get_width()//2, 360))
    
    return rect_elo_drag, btn_confirmar

def desenhar_analise(ecra, off_x_log, off_y, width, height, move_log, best_moves_dict):
    """
    O Painel de Análise de Xadrez que é atualizado em tempo real pela Thread Pós-Jogo.
    """
    pygame.draw.rect(ecra, (20, 20, 30), (off_x_log, off_y, width, height), border_radius=10)
    pygame.draw.rect(ecra, (100, 100, 255), (off_x_log, off_y, width, height), 2, border_radius=10)
    
    fonte_tit = pygame.font.SysFont("arial", 24, bold=True)
    fonte_txt = pygame.font.SysFont("arial", 16)
    fonte_best = pygame.font.SysFont("arial", 16, bold=True)
    
    tit = fonte_tit.render("Análise do Motor (Stockfish-like)", True, (150, 200, 255))
    ecra.blit(tit, (off_x_log + 20, off_y + 20))
    
    y = off_y + 60
    # Desliza para mostrar os últimos turnos se o histórico for grande
    mostrar_log = move_log[-8:] if len(move_log) > 8 else move_log
    
    for i, log in enumerate(mostrar_log):
        id_jogada = len(move_log) - len(mostrar_log) + i
        cor_txt = C_BRANCO
        txt_short = fonte_tit.render(log["short"], True, cor_txt)
        ecra.blit(txt_short, (off_x_log + 20, y))
        
        # Procura se a Thread de Análise já processou este turno
        if id_jogada in best_moves_dict:
            dados_analise = best_moves_dict[id_jogada]
            if dados_analise["forced_mate"]:
                txt_analise = fonte_best.render(f"Letal em {dados_analise['forced_mate']}", True, C_VERMELHO)
            else:
                txt_analise = fonte_best.render(f"Melhor: {dados_analise['best_move_str']} (Score: {dados_analise['score']})", True, (100, 255, 100))
        else:
            txt_analise = fonte_txt.render("A analisar com profundidade...", True, (150, 150, 150))
            
        ecra.blit(txt_analise, (off_x_log + 20, y + 25))
        y += 60

# ================= As funções de Renderização Normais mantêm-se iguais =================
def desenhar_tabuleiro(ecra, gs, tam_casa, off_x, off_y):
    luzes_chess = []
    if hasattr(gs, 'last_move') and gs.last_move:
        luzes_chess.append(gs.last_move["start"])
        luzes_chess.append(gs.last_move["end"])

    for r in range(8):
        for c in range(8):
            cor = (200, 200, 200) if (r + c) % 2 == 0 else (100, 100, 100)
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
    ameacas = p.get_threat_area(r, c, gs.board, gs.tile_effects)
    stuns = p.get_valid_stuns(r, c, gs.board, gs.tile_effects)
    spawns = p.get_valid_spawns(r, c, gs.board, gs.tile_effects)

    s_move = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
    s_move.fill((50, 255, 50, 80))  
    for mr, mc in movimentos:
        ecra.blit(s_move, (off_x + mc * tam_casa, off_y + mr * tam_casa))
        pygame.draw.rect(ecra, (50, 255, 50), (off_x + mc * tam_casa, off_y + mr * tam_casa, tam_casa, tam_casa), 2)

    s_threat = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
    s_threat.fill((255, 150, 0, 40))
    for tr, tc in ameacas:
        if (tr, tc) not in ataques:
            ecra.blit(s_threat, (off_x + tc * tam_casa, off_y + tr * tam_casa))
            pygame.draw.rect(ecra, (255, 150, 0, 150), (off_x + tc * tam_casa, off_y + tr * tam_casa, tam_casa, tam_casa), 2)

    s_atk = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
    s_atk.fill((255, 0, 0, 100))
    for ar, ac in ataques:
        ecra.blit(s_atk, (off_x + ac * tam_casa, off_y + ar * tam_casa))
        pygame.draw.rect(ecra, (255, 0, 0), (off_x + ac * tam_casa, off_y + ar * tam_casa, tam_casa, tam_casa), 4)

    s_spawn = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
    s_spawn.fill((255, 215, 0, 120)) 
    for sr, sc, sname in spawns:
        cx = off_x + sc * tam_casa + tam_casa // 2
        cy = off_y + sr * tam_casa + tam_casa // 2
        ecra.blit(s_spawn, (off_x + sc * tam_casa, off_y + sr * tam_casa))
        pygame.draw.rect(ecra, (255, 215, 0), (off_x + sc * tam_casa, off_y + sr * tam_casa, tam_casa, tam_casa), 4)
        pygame.draw.line(ecra, (255, 255, 255), (cx - 10, cy), (cx + 10, cy), 3)
        pygame.draw.line(ecra, (255, 255, 255), (cx, cy - 10), (cx, cy + 10), 3)

    for foco_r, foco_c in stuns.keys():
        info = stuns[(foco_r, foco_c)]
        cx = off_x + foco_c * tam_casa + tam_casa // 2
        cy = off_y + foco_r * tam_casa + tam_casa // 2
        compr = tam_casa // 4
        cor_cruz = (0, 255, 255) if info["has_enemy"] else (100, 120, 150)
        bg_alpha = 80 if info["has_enemy"] else 30
        espessura = 5 if info["has_enemy"] else 2
        s_stun = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
        s_stun.fill((*cor_cruz[:3], bg_alpha))
        ecra.blit(s_stun, (off_x + foco_c * tam_casa, off_y + foco_r * tam_casa))
        pygame.draw.line(ecra, cor_cruz, (cx - compr, cy), (cx + compr, cy), espessura)
        pygame.draw.line(ecra, cor_cruz, (cx, cy - compr), (cx, cy + compr), espessura)
        for (aoe_r, aoe_c) in info["aoe"]:
            rect_aoe = pygame.Rect(off_x + aoe_c * tam_casa + 2, off_y + aoe_r * tam_casa + 2, tam_casa - 4, tam_casa - 4)
            pygame.draw.rect(ecra, cor_cruz, rect_aoe, max(1, espessura - 2))

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
                    texto = fonte.render("BL" if p.name == "BoneLord" else p.name[:2].capitalize(), True, cor_texto)
                    ecra.blit(texto, texto.get_rect(center=(cx, cy)))
                
                if p.stun_timer > 0: pygame.draw.circle(ecra, (0, 150, 255), (cx, cy), int(tam_casa * 0.42), 4)
                if hasattr(p, 'lifespan') and p.lifespan is not None:
                    txt_vida = fonte_vida.render(str(p.lifespan), True, (255, 50, 50))
                    pos_x = off_x + c * tam_casa + tam_casa - int(tam_casa * 0.25)
                    pos_y = off_y + r * tam_casa + int(tam_casa * 0.05)
                    ecra.blit(fonte_vida.render(str(p.lifespan), True, C_PRETO), (pos_x + 1, pos_y + 1))
                    ecra.blit(txt_vida, (pos_x, pos_y))

def desenhar_log(ecra, gs, off_x_log, off_y, width, height):
    pygame.draw.rect(ecra, (40, 40, 40), (off_x_log, off_y, width, height), border_radius=10)
    tit = pygame.font.SysFont("arial", 24, bold=True).render("Registo de Batalha", True, C_BRANCO)
    ecra.blit(tit, (off_x_log + 20, off_y + 20))
    pygame.draw.line(ecra, (100, 100, 100), (off_x_log + 20, off_y + 50), (off_x_log + width - 20, off_y + 50), 2)
    y = off_y + 60
    for log in gs.move_log[-12:]:
        cor_txt = (150, 200, 255) if log["team"] == "brancas" else (255, 150, 150)
        ecra.blit(pygame.font.SysFont("arial", 24, bold=True).render(log["short"], True, cor_txt), (off_x_log + 20, y))
        y += 40

def desenhar_loja_dinamica(ecra, w, h, catalogo, pontos, peca_selecionada, off_y):
    fonte_tit = pygame.font.SysFont("arial", 36)
    fonte_item = pygame.font.SysFont("arial", 24)
    ecra.blit(fonte_tit.render(f"Orçamento Restante: {pontos} pts", True, C_BRANCO), (20, off_y))
    botoes = {}
    for i, item in enumerate(catalogo):
        x, y = 20 + (i % 6) * 110, off_y + 40 + (i // 6) * 60
        cor_btn = (150, 50, 50) if item["cost"] > pontos else ((100, 200, 100) if item["name"] == peca_selecionada else (80, 80, 80))
        rect = pygame.Rect(x, y, 100, 50)
        pygame.draw.rect(ecra, cor_btn, rect, border_radius=5)
        ecra.blit(fonte_item.render(item["name"], True, C_BRANCO), (x + 5, y + 5))
        ecra.blit(fonte_item.render(f"{item['cost']} pts", True, C_BRANCO), (x + 5, y + 25))
        if item["cost"] <= pontos: botoes[item["name"]] = rect
            
    btn_r = pygame.Rect(w - 150, off_y, 130, 40)
    pygame.draw.rect(ecra, (50, 150, 250), btn_r, border_radius=5)
    ecra.blit(fonte_tit.render("Pronto!", True, C_BRANCO), (btn_r.x + 20, btn_r.y + 10))
    return botoes, btn_r, pygame.Rect(0,0,0,0)

def desenhar_enciclopedia(ecra, w, h, catalogo):
    btn_voltar = pygame.Rect(w//2 - 60, h - 60, 120, 40)
    pygame.draw.rect(ecra, (150, 50, 50), btn_voltar, border_radius=5)
    ecra.blit(pygame.font.SysFont("arial", 32).render("Voltar", True, C_BRANCO), (btn_voltar.x + 25, btn_voltar.y + 10))
    return btn_voltar