import sys
import os
import pygame
import math
from engine.config import LINHAS, COLUNAS

C_FUNDO = (30, 30, 30)
C_BRANCO = (255, 255, 255)
C_PRETO = (0, 0, 0)
C_AZUL = (50, 150, 255)
C_VERMELHO = (255, 50, 50)

_CACHE_IMAGENS = {}
_BOARD_BG_CACHE = {}

def desenhar_coordenadas(ecra, tam_casa, off_x, off_y):
    fonte = pygame.font.SysFont("arial", 14, bold=True)
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for c in range(COLUNAS):
        txt = fonte.render(letras[c], True, (150, 150, 150))
        ecra.blit(txt, (off_x + c * tam_casa + tam_casa//2 - txt.get_width()//2, off_y + LINHAS * tam_casa + 5))
    for r in range(LINHAS):
        txt = fonte.render(str(LINHAS - r), True, (150, 150, 150))
        ecra.blit(txt, (off_x - txt.get_width() - 8, off_y + r * tam_casa + tam_casa//2 - txt.get_height()//2))

def desenhar_painel_heroi(ecra, peca, off_x, off_y, width, height):
    pygame.draw.rect(ecra, (25, 25, 35), (off_x, off_y, width, height), border_radius=10)
    pygame.draw.rect(ecra, (150, 150, 200), (off_x, off_y, width, height), 2, border_radius=10)

    fonte_tit = pygame.font.SysFont("arial", 28, bold=True)
    fonte_sub = pygame.font.SysFont("arial", 18, italic=True)
    fonte_desc = pygame.font.SysFont("arial", 16)

    tam_avatar = min(96, int(width * 0.22))
    img = carregar_imagem_peca(peca.name, peca.team, tam_avatar)
    if img:
        avatar_rect = img.get_rect()
        avatar_rect.topleft = (off_x + width - tam_avatar - 16, off_y + 16)
        ecra.blit(img, avatar_rect)
        pygame.draw.rect(ecra, (80, 80, 90), (avatar_rect.x - 6, avatar_rect.y - 6, tam_avatar + 12, tam_avatar + 12), 2, border_radius=8)
    else:
        pygame.draw.rect(ecra, (60, 60, 70), (off_x + width - tam_avatar - 16, off_y + 16, tam_avatar, tam_avatar), border_radius=8)

    cor_nome = (150, 200, 255) if peca.team == 'brancas' else (255, 120, 120)
    ecra.blit(fonte_tit.render(peca.name, True, cor_nome), (off_x + 20, off_y + 18))
    ecra.blit(fonte_sub.render(f"Facção: {peca.team.capitalize()}", True, (150, 150, 150)), (off_x + 20, off_y + 50))

    y_pix = off_y + 90
    ecra.blit(fonte_desc.render(f"Custo: {peca.cost} pts", True, C_BRANCO), (off_x + 20, y_pix))

    y_pix += 30
    if peca.stun_timer > 0:
        ecra.blit(fonte_desc.render(f"⚠️ ATORDOADO ({peca.stun_timer} turnos)", True, (255, 200, 50)), (off_x + 20, y_pix))
        y_pix += 26
    if hasattr(peca, 'lifespan') and peca.lifespan is not None:
        ecra.blit(fonte_desc.render(f"⏳ Vida restante: {peca.lifespan} turnos", True, (255, 100, 100)), (off_x + 20, y_pix))
        y_pix += 26

    pygame.draw.line(ecra, (100, 100, 100), (off_x + 16, y_pix + 8), (off_x + width - tam_avatar - 32, y_pix + 8))
    y_pix += 18
    desc = getattr(peca, 'descricao', 'Unidade padrão.')
    
    ecra.blit(fonte_sub.render("Descrição:", True, (200, 200, 200)), (off_x + 20, y_pix))
    y_pix += 22
    for linha in str(desc).split('\n'):
        ecra.blit(fonte_desc.render(linha, True, C_BRANCO), (off_x + 20, y_pix))
        y_pix += 18

    y_pix += 20
    ecra.blit(fonte_sub.render("Passiva:", True, (200, 200, 200)), (off_x + 20, y_pix))
    
    passiva_txt = getattr(peca, 'passiva', 'Nenhuma.')
    y_pix += 22
    words = passiva_txt.split(' ')
    linha_atual = ""
    for w in words:
        if fonte_desc.size(linha_atual + w)[0] < width - 40:
            linha_atual += w + " "
        else:
            ecra.blit(fonte_desc.render(linha_atual, True, (140, 255, 160)), (off_x + 20, y_pix))
            y_pix += 18
            linha_atual = w + " "
    ecra.blit(fonte_desc.render(linha_atual, True, (140, 255, 160)), (off_x + 20, y_pix))

def desenhar_destaques_com_hover(ecra, gs, casa_selecionada, hover_pos, tam_casa, off_x, off_y):
    if not casa_selecionada: return
    r, c = casa_selecionada
    p = gs.board[r][c]
    if not p: return

    ticks = pygame.time.get_ticks()
    pulsar = (math.sin(ticks / 300.0) + 1.0) / 2.0

    movimentos = p.get_valid_moves(r, c, gs.board, gs.tile_effects)
    ataques = p.get_valid_attacks(r, c, gs.board, gs.tile_effects)
    stuns = p.get_valid_stuns(r, c, gs.board, gs.tile_effects)

    s_move = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
    for mr, mc in movimentos:
        alpha = int(80 + 120 * (1.0 if hover_pos == (mr, mc) else pulsar))
        s_move.fill((50, 255, 50, alpha))
        ecra.blit(s_move, (off_x + mc * tam_casa, off_y + mr * tam_casa))
        if hover_pos == (mr, mc):
            pygame.draw.rect(ecra, (200, 255, 150), (off_x + mc * tam_casa, off_y + mr * tam_casa, tam_casa, tam_casa), 3)

    s_atk = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
    for ar, ac in ataques:
        alpha = int(90 + 120 * pulsar) if hover_pos == (ar, ac) else int(60 + 80 * pulsar)
        s_atk.fill((255, 40, 40, alpha))
        ecra.blit(s_atk, (off_x + ac * tam_casa, off_y + ar * tam_casa))
        cx = off_x + ac * tam_casa + tam_casa // 2
        cy = off_y + ar * tam_casa + tam_casa // 2
        thickness = max(1, int(2 + 3 * pulsar))
        leng = int(tam_casa * (0.35 + 0.05 * pulsar))
        pygame.draw.line(ecra, (255, 20, 20), (cx - leng, cy), (cx + leng, cy), thickness)
        pygame.draw.line(ecra, (255, 20, 20), (cx, cy - leng), (cx, cy + leng), thickness)

    font_vfx = pygame.font.SysFont("arial", max(12, int(tam_casa * 0.28)), bold=True)
    for foco, info in stuns.items():
        foco_r, foco_c = foco
        for (aoe_r, aoe_c) in info["aoe"]:
            s_aoe = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
            base_alpha = 60 if info["has_enemy"] else 30
            alpha = int(base_alpha + 90 * pulsar)
            color = (0, 200, 255) if info["has_enemy"] else (100, 120, 150)
            s_aoe.fill((*color, alpha))
            ecra.blit(s_aoe, (off_x + aoe_c * tam_casa, off_y + aoe_r * tam_casa))
        if info["has_enemy"]:
            txt = font_vfx.render("STUN", True, (255, 255, 255))
        else:
            txt = font_vfx.render("AOE", True, (220, 220, 220))
        osc = int(math.sin((ticks + (foco_r * 13 + foco_c * 7)) / 280.0) * (tam_casa * 0.12))
        tx = off_x + foco_c * tam_casa + tam_casa // 2 - txt.get_width() // 2
        ty = off_y + foco_r * tam_casa - txt.get_height() - 6 + osc
        vfx_surf = pygame.Surface((txt.get_width(), txt.get_height()), pygame.SRCALPHA)
        vfx_surf.fill((0, 0, 0, 0))
        vfx_surf.blit(txt, (0, 0))
        vfx_surf.set_alpha(int(160 + 95 * pulsar))
        ecra.blit(vfx_surf, (tx, ty))

    if hasattr(p, 'get_valid_spells'):
        for spell in p.get_valid_spells(r, c, gs.board, gs.tile_effects):
            tr, tc = spell["target"]
            s_spell = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
            alpha = int(90 + 120 * pulsar) if hover_pos == (tr, tc) else int(60 + 80 * pulsar)
            s_spell.fill((200, 50, 255, alpha))
            ecra.blit(s_spell, (off_x + tc * tam_casa, off_y + tr * tam_casa))
            
            txt = font_vfx.render(spell["spell_type"].upper(), True, (255, 255, 255))
            osc = int(math.sin((ticks + (tr * 13 + tc * 7)) / 280.0) * (tam_casa * 0.12))
            tx = off_x + tc * tam_casa + tam_casa // 2 - txt.get_width() // 2
            ty = off_y + tr * tam_casa - txt.get_height() - 6 + osc
            vfx_surf = pygame.Surface((txt.get_width(), txt.get_height()), pygame.SRCALPHA)
            vfx_surf.fill((0, 0, 0, 0))
            vfx_surf.blit(txt, (0, 0))
            vfx_surf.set_alpha(int(160 + 95 * pulsar))
            ecra.blit(vfx_surf, (tx, ty))

def carregar_imagem_peca(nome_peca, team, tam):
    chave = (nome_peca, team, tam)
    if chave in _CACHE_IMAGENS: return _CACHE_IMAGENS[chave]
    if getattr(sys, 'frozen', False):
        caminho_base = sys._MEIPASS #type: ignore
    else:
        caminho_base = os.path.dirname(os.path.dirname(__file__))

    caminho_pasta = os.path.join(caminho_base, "ui", "assets")
    caminho_completo = os.path.join(caminho_pasta, f"{nome_peca.lower()}.png")

    if os.path.exists(caminho_completo):
        img = pygame.image.load(caminho_completo).convert_alpha()
        img = pygame.transform.smoothscale(img, (int(tam * 0.65), int(tam * 0.65)))
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
    txt_s = pygame.font.SysFont("arial", 32).render("Jogar", True, C_BRANCO)
    ecra.blit(txt_s, (w//2 - txt_s.get_width()//2, h//2 + 10))
    
    btn_info = pygame.Rect(w//2 - 150, h//2 + 80, 300, 60)
    pygame.draw.rect(ecra, (100, 100, 100), btn_info, border_radius=10)
    txt_i = pygame.font.SysFont("arial", 32).render("Enciclopédia", True, C_BRANCO)
    ecra.blit(txt_i, (w//2 - txt_i.get_width()//2, h//2 + 90))
    
    return btn_start, btn_info

# --- NOVOS ECRÃS DE MENU SEPARADOS ---

def desenhar_selecao_modo(ecra, w, h):
    """ Ecrã: Escolher entre IA ou Multiplayer """
    ecra.fill(C_FUNDO)
    txt_tit = pygame.font.SysFont("arial", 48, bold=True).render("Selecione o Modo", True, C_BRANCO)
    ecra.blit(txt_tit, (w//2 - txt_tit.get_width()//2, 100))

    btn_ia = pygame.Rect(w//2 - 150, 250, 300, 60)
    pygame.draw.rect(ecra, C_AZUL, btn_ia, border_radius=10)
    txt_ia = pygame.font.SysFont("arial", 32).render("Jogar vs IA", True, C_BRANCO)
    ecra.blit(txt_ia, (w//2 - txt_ia.get_width()//2, 260))

    # Botão bloqueado
    btn_multi = pygame.Rect(w//2 - 150, 340, 300, 60)
    pygame.draw.rect(ecra, (60, 60, 60), btn_multi, border_radius=10)
    txt_multi = pygame.font.SysFont("arial", 28).render("Multiplayer (Em Breve)", True, (120, 120, 120))
    ecra.blit(txt_multi, (w//2 - txt_multi.get_width()//2, 355))

    btn_voltar = pygame.Rect(w//2 - 100, 480, 200, 50)
    pygame.draw.rect(ecra, C_VERMELHO, btn_voltar, border_radius=10)
    txt_v = pygame.font.SysFont("arial", 28).render("Voltar", True, C_BRANCO)
    ecra.blit(txt_v, (w//2 - txt_v.get_width()//2, 490))

    return btn_ia, btn_multi, btn_voltar

def desenhar_selecao_tipo_ia(ecra, w, h):
    """ Ecrã: Escolher entre IA Normal ou Predador """
    ecra.fill(C_FUNDO)
    txt_tit = pygame.font.SysFont("arial", 48, bold=True).render("Comportamento da IA", True, C_BRANCO)
    ecra.blit(txt_tit, (w//2 - txt_tit.get_width()//2, 100))

    btn_normal = pygame.Rect(w//2 - 200, 230, 400, 80)
    pygame.draw.rect(ecra, (100, 200, 100), btn_normal, border_radius=10)
    txt_n = pygame.font.SysFont("arial", 28, bold=True).render("Modo Normal", True, C_PRETO)
    txt_nd = pygame.font.SysFont("arial", 16).render("A IA pensa de forma tradicional, apenas no seu turno.", True, (40,40,40))
    ecra.blit(txt_n, (w//2 - txt_n.get_width()//2, 240))
    ecra.blit(txt_nd, (w//2 - txt_nd.get_width()//2, 280))

    btn_predador = pygame.Rect(w//2 - 200, 340, 400, 80)
    pygame.draw.rect(ecra, (200, 60, 60), btn_predador, border_radius=10)
    txt_p = pygame.font.SysFont("arial", 28, bold=True).render("Modo Predador", True, C_BRANCO)
    txt_pd = pygame.font.SysFont("arial", 16).render("A IA persegue os teus pensamentos e joga quase instantaneamente.", True, (255,200,200))
    ecra.blit(txt_p, (w//2 - txt_p.get_width()//2, 350))
    ecra.blit(txt_pd, (w//2 - txt_pd.get_width()//2, 390))

    btn_voltar = pygame.Rect(w//2 - 100, 480, 200, 50)
    pygame.draw.rect(ecra, (100, 100, 100), btn_voltar, border_radius=10)
    txt_v = pygame.font.SysFont("arial", 28).render("Voltar", True, C_BRANCO)
    ecra.blit(txt_v, (w//2 - txt_v.get_width()//2, 490))

    return btn_normal, btn_predador, btn_voltar

def desenhar_selecao_dificuldade(ecra, w, h, elo_atual):
    """ Ecrã: Escolher o Rating ELO """
    ecra.fill(C_FUNDO)
    fonte = pygame.font.SysFont("arial", 36)
    
    txt_tit = fonte.render("Definir Dificuldade ELO", True, C_BRANCO)
    ecra.blit(txt_tit, (w//2 - txt_tit.get_width()//2, 80))
    
    pygame.draw.rect(ecra, (50, 50, 50), (w//2 - 200, 180, 400, 20))
    x_elo = w//2 - 200 + int(((elo_atual - 100) / 2500) * 400)
    rect_elo_drag = pygame.Rect(x_elo - 10, 170, 20, 40)
    pygame.draw.rect(ecra, C_VERMELHO, rect_elo_drag)
    txt_elo = fonte.render(f"Rating ELO Desejado: {elo_atual}", True, C_BRANCO)
    ecra.blit(txt_elo, (w//2 - txt_elo.get_width()//2, 130))
    
    if elo_atual <= 300: tempo_aprox = 0.05
    else: tempo_aprox = ((elo_atual - 300) / 2300.0) * 5.0
        
    fonte_aviso = pygame.font.SysFont("arial", 20)
    txt_aviso = fonte_aviso.render(f"Poder Computacional Estimado: {tempo_aprox:.2f}s por turno.", True, (150, 200, 255))
    ecra.blit(txt_aviso, (w//2 - txt_aviso.get_width()//2, 240))
    
    btn_confirmar = pygame.Rect(w//2 - 150, 330, 300, 60)
    pygame.draw.rect(ecra, (100, 200, 100), btn_confirmar, border_radius=10)
    txt_c = pygame.font.SysFont("arial", 28, bold=True).render("Iniciar Batalha", True, C_BRANCO)
    ecra.blit(txt_c, (w//2 - txt_c.get_width()//2, 345))

    btn_voltar = pygame.Rect(w//2 - 100, 420, 200, 50)
    pygame.draw.rect(ecra, (100, 100, 100), btn_voltar, border_radius=10)
    txt_v = pygame.font.SysFont("arial", 28).render("Voltar", True, C_BRANCO)
    ecra.blit(txt_v, (w//2 - txt_v.get_width()//2, 430))
    
    return rect_elo_drag, btn_confirmar, btn_voltar

# ---------------------------------------------

def desenhar_analise(ecra, off_x_log, off_y, width, height, move_log, best_moves_dict, selected_idx=None):
    pygame.draw.rect(ecra, (20, 20, 30), (off_x_log, off_y, width, height), border_radius=10)
    pygame.draw.rect(ecra, (100, 100, 255), (off_x_log, off_y, width, height), 2, border_radius=10)
    
    fonte_tit = pygame.font.SysFont("arial", 22, bold=True)
    fonte_txt = pygame.font.SysFont("arial", 15)
    fonte_best = pygame.font.SysFont("arial", 15, bold=True)
    
    tit = fonte_tit.render("Análise do Motor (Stockfish)", True, (150, 200, 255))
    ecra.blit(tit, (off_x_log + 15, off_y + 15))
    
    y = off_y + 50
    mostrar_log = move_log[-7:] if len(move_log) > 7 else move_log
    offset_base = len(move_log) - len(mostrar_log)
    
    rects_clicaveis = []
    
    for i, log in enumerate(mostrar_log):
        id_jogada = offset_base + i
        rect_item = pygame.Rect(off_x_log + 10, y - 2, width - 20, 48)
        
        if selected_idx == id_jogada:
            pygame.draw.rect(ecra, (50, 50, 80), rect_item, border_radius=5)
            pygame.draw.rect(ecra, (100, 200, 255), rect_item, 1, border_radius=5)
            
        rects_clicaveis.append((rect_item, id_jogada))
        
        cor_txt = (255, 255, 255)
        txt_short = fonte_tit.render(log["short"], True, cor_txt)
        ecra.blit(txt_short, (off_x_log + 15, y))
        
        if id_jogada in best_moves_dict:
            dados_analise = best_moves_dict[id_jogada]
            if dados_analise["forced_mate"]:
                txt_analise = fonte_best.render(f"Letal em {dados_analise['forced_mate']}", True, C_VERMELHO)
            else:
                txt_analise = fonte_best.render(f"Melhor: {dados_analise['best_move_str']} (Score: {dados_analise['score']})", True, (100, 255, 100))
        else:
            txt_analise = fonte_txt.render("A analisar profundidade...", True, (150, 150, 150))
            
        ecra.blit(txt_analise, (off_x_log + 15, y + 22))
        y += 52

    return rects_clicaveis

def desenhar_tabuleiro(ecra, gs, tam_casa, off_x, off_y):
    key = (tam_casa, LINHAS, COLUNAS)
    bg = _BOARD_BG_CACHE.get(key)
    if bg is None:
        bg = pygame.Surface((COLUNAS * tam_casa, LINHAS * tam_casa))
        for r in range(LINHAS):
            for c in range(COLUNAS):
                cor = (200, 200, 200) if (r + c) % 2 == 0 else (100, 100, 100)
                rect = pygame.Rect(c * tam_casa, r * tam_casa, tam_casa, tam_casa)
                pygame.draw.rect(bg, cor, rect)
        _BOARD_BG_CACHE[key] = bg

    ecra.blit(bg, (off_x, off_y))

    luzes_chess = []
    if hasattr(gs, 'last_move') and gs.last_move:
        luzes_chess.append(gs.last_move["start"])
        luzes_chess.append(gs.last_move["end"])

    for r in range(LINHAS):
        for c in range(COLUNAS):
            rect = pygame.Rect(off_x + c * tam_casa, off_y + r * tam_casa, tam_casa, tam_casa)
            if (r, c) in luzes_chess:
                s = pygame.Surface((tam_casa, tam_casa), pygame.SRCALPHA)
                s.fill((230, 230, 120, 180) if (r + c) % 2 == 0 else (180, 180, 80, 160))
                ecra.blit(s, (rect.x, rect.y))
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
    pass 

def desenhar_pecas(ecra, board, tam_casa, off_x, off_y):
    fonte = pygame.font.SysFont("arial", int(tam_casa * 0.4))
    fonte_vida = pygame.font.SysFont("arial", int(tam_casa * 0.3), bold=True)
    for r in range(LINHAS):
        for c in range(COLUNAS):
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

def desenhar_loja_dinamica(ecra, off_x, off_y, width, height, catalogo, pontos, peca_selecionada):
    pygame.draw.rect(ecra, (30, 30, 40), (off_x, off_y, width, height), border_radius=10)
    pygame.draw.rect(ecra, (100, 150, 200), (off_x, off_y, width, height), 2, border_radius=10)

    fonte_tit = pygame.font.SysFont("arial", 24, bold=True)
    fonte_item = pygame.font.SysFont("arial", 18, bold=True)
    fonte_pts = pygame.font.SysFont("arial", 16)

    txt_tit = fonte_tit.render(f"Orçamento: {pontos} pts", True, (255, 215, 0))
    ecra.blit(txt_tit, (off_x + 20, off_y + 20))
    pygame.draw.line(ecra, (100, 100, 100), (off_x + 20, off_y + 55), (off_x + width - 20, off_y + 55), 2)

    botoes = {}
    colunas = 2
    largura_btn = (width - 60) // colunas
    altura_btn = 45
    espaco_y = 10
    espaco_x = 20
    start_y = off_y + 70

    for i, item in enumerate(catalogo):
        col = i % colunas
        row = i // colunas
        x = off_x + 20 + col * (largura_btn + espaco_x)
        y = start_y + row * (altura_btn + espaco_y)

        if item["cost"] > pontos:
            cor_btn = (60, 40, 40)
            cor_txt = (120, 120, 120)
        elif item["name"] == peca_selecionada:
            cor_btn = (100, 200, 100)
            cor_txt = C_BRANCO
        else:
            cor_btn = (60, 60, 80)
            cor_txt = (220, 220, 220)

        rect = pygame.Rect(x, y, largura_btn, altura_btn)
        pygame.draw.rect(ecra, cor_btn, rect, border_radius=6)
        if item["cost"] <= pontos:
            pygame.draw.rect(ecra, (100, 100, 150), rect, 1, border_radius=6)
        
        txt_nome = fonte_item.render(item["name"], True, cor_txt)
        txt_custo = fonte_pts.render(f"{item['cost']} pts", True, (150, 255, 150) if item["cost"] <= pontos else cor_txt)
        
        ecra.blit(txt_nome, (x + 8, y + 5))
        ecra.blit(txt_custo, (x + 8, y + 24))

        if item["cost"] <= pontos:
            botoes[item["name"]] = rect

    btn_r = pygame.Rect(off_x + 20, off_y + height - 70, width - 40, 50)
    pygame.draw.rect(ecra, C_AZUL, btn_r, border_radius=8)
    txt_pronto = fonte_tit.render("Batalhar! (Pronto)", True, C_BRANCO)
    ecra.blit(txt_pronto, (btn_r.x + btn_r.width//2 - txt_pronto.get_width()//2, btn_r.y + 12))

    return botoes, btn_r, None

def desenhar_enciclopedia(ecra, w, h, catalogo):
    btn_voltar = pygame.Rect(w//2 - 60, h - 60, 120, 40)
    pygame.draw.rect(ecra, (150, 50, 50), btn_voltar, border_radius=5)
    ecra.blit(pygame.font.SysFont("arial", 32).render("Voltar", True, C_BRANCO), (btn_voltar.x + 25, btn_voltar.y + 10))
    return btn_voltar

def desenhar_hud_jogadores(ecra, off_x, off_y_top, off_y_bot, tam_casa, bot_name, gs):
    altura = 36
    rect_top = pygame.Rect(off_x, off_y_top, COLUNAS * tam_casa, altura)
    pygame.draw.rect(ecra, (20, 20, 24), rect_top)
    pygame.draw.rect(ecra, (80, 80, 90), rect_top, 1)
    fonte = pygame.font.SysFont("arial", 18, bold=True)
    txt_top = fonte.render(f"Inimigo: {bot_name}", True, C_BRANCO)
    ecra.blit(txt_top, (rect_top.x + 8, rect_top.y + 6))

    clock_left = fonte.render(f"Brancas: {int(getattr(gs, 'white_time', 0))}s", True, (200,200,200))
    clock_right = fonte.render(f"Pretas: {int(getattr(gs, 'black_time', 0))}s", True, (200,200,200))
    ecra.blit(clock_left, (rect_top.x + 220, rect_top.y + 6))
    ecra.blit(clock_right, (rect_top.x + 420, rect_top.y + 6))

    white_mat = 0
    black_mat = 0
    for r in range(LINHAS):
        for c in range(COLUNAS):
            p = getattr(gs, 'board', [[None]*COLUNAS]*LINHAS)[r][c]
            if p:
                if p.team == 'brancas':
                    white_mat += getattr(p, 'cost', 0)
                else:
                    black_mat += getattr(p, 'cost', 0)
    mat_txt_w = fonte.render(f"Mat: {white_mat}", True, (180, 255, 180))
    mat_txt_b = fonte.render(f"Mat: {black_mat}", True, (255, 180, 180))
    ecra.blit(mat_txt_w, (rect_top.x + 600, rect_top.y + 6))
    ecra.blit(mat_txt_b, (rect_top.x + 700, rect_top.y + 6))

    rect_bot = pygame.Rect(off_x, off_y_bot, COLUNAS * tam_casa, altura)
    pygame.draw.rect(ecra, (18, 18, 22), rect_bot)
    pygame.draw.rect(ecra, (80, 80, 90), rect_bot, 1)
    txt_bot = fonte.render("Jogador", True, C_BRANCO)
    ecra.blit(txt_bot, (rect_bot.x + 8, rect_bot.y + 6))
    return rect_top, rect_bot

def desenhar_eval_bar(ecra, gs, off_x, altura_tabuleiro, off_y_tab):
    score = getattr(gs, 'current_score', 0)
    if score is None: score = 0

    max_abs = 20000.0
    norm = max(-1.0, min(1.0, score / max_abs))
    bar_w = 20
    fill = (norm + 1.0) / 2.0

    rect_track = pygame.Rect(off_x, off_y_tab, bar_w, altura_tabuleiro)
    pygame.draw.rect(ecra, (30, 30, 30), rect_track)
    pygame.draw.rect(ecra, (80, 80, 80), rect_track, 1)

    filled_h = int(rect_track.h * fill)
    rect_fill = pygame.Rect(rect_track.x, rect_track.y + rect_track.h - filled_h, bar_w, filled_h)
    color = (240, 240, 240) if norm > 0 else (40, 40, 40)
    pygame.draw.rect(ecra, color, rect_fill)
    return rect_track