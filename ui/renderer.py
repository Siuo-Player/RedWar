import sys
import os
import pygame
import math
from typing import Optional, Dict, Tuple, List, Any
from engine.config import LINHAS, COLUNAS

# ==========================================
# TEMA E CORES (1.1 - Bug de Cores Corrigido)
# ==========================================
COLORS = {
    "bg": (30, 30, 30),
    "panel_bg": (25, 25, 35),
    "hud_bg": (20, 20, 24),
    "text": (255, 255, 255),
    "text_muted": (150, 150, 150),
    "white_team": (150, 200, 255),
    "black_team": (255, 120, 120),
    "move": (50, 255, 50),
    "attack": (255, 40, 40),
    "stun_aoe": (100, 150, 255),
    "stun_hit": (255, 120, 0),
    "spell": (200, 50, 255),
    "btn_primary": (50, 150, 255),
    "btn_danger": (200, 60, 60),
    "danger": (255, 70, 70),
    "success": (100, 255, 100),
    "warning": (255, 200, 50),
    "btn_disabled": (60, 60, 60),
    "btn_secondary": (100, 100, 100),
    "board_light": (200, 200, 200),
    "board_dark": (100, 100, 100)
}

class FontManager:
    _fonts: Dict[Tuple[str, int, bool, bool], pygame.font.Font] = {}
    @classmethod
    def get(cls, name: str, size: int, bold: bool = False, italic: bool = False) -> pygame.font.Font:
        key = (name, size, bold, italic)
        if key not in cls._fonts:
            cls._fonts[key] = pygame.font.SysFont(name, size, bold=bold, italic=italic)
        return cls._fonts[key]

class AssetManager:
    _images: Dict[Tuple[str, str, int], Optional[pygame.Surface]] = {}
    @classmethod
    def get_image(cls, nome_peca: str, team: str, tam: int) -> Optional[pygame.Surface]:
        chave = (nome_peca, team, tam)
        if chave in cls._images:
            return cls._images[chave]
        caminho_base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(__file__))) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(__file__))
        caminho_completo = os.path.join(caminho_base, "ui", "assets", f"{nome_peca.lower()}.png")
        if os.path.exists(caminho_completo):
            try:
                img = pygame.image.load(caminho_completo).convert_alpha()
                img = pygame.transform.smoothscale(img, (int(tam * 0.65), int(tam * 0.65)))
                cor_overlay = (40, 40, 40, 255) if team == 'pretas' else (240, 245, 255, 255)
                img.fill(cor_overlay, special_flags=pygame.BLEND_RGBA_MULT)
                cls._images[chave] = img
                return img
            except pygame.error as exc:
                print(f"[Renderer Warning] Não foi possível carregar o asset {caminho_completo}: {exc}")
        cls._images[chave] = None
        return None

class VFXManager:
    _cached_surfaces: Dict[Tuple[Tuple[int, int, int], int, int], pygame.Surface] = {}
    @classmethod
    def draw_tint(cls, ecra: pygame.Surface, color: Tuple[int, int, int], alpha: int, rect: pygame.Rect):
        key = (color, rect.width, rect.height)
        if key not in cls._cached_surfaces:
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            s.fill((*color, 255))
            cls._cached_surfaces[key] = s
        surf = cls._cached_surfaces[key]
        surf.set_alpha(alpha)
        ecra.blit(surf, rect.topleft)

class RendererState:
    def __init__(self):
        self.board_bg: Optional[pygame.Surface] = None
        self.board_size_key: Optional[Tuple[int, int, int]] = None
        self.hud_hash: Optional[int] = None
        self.white_mat: int = 0
        self.black_mat: int = 0
        self.hl_hash: Optional[int] = None
        self.hl_pos: Optional[Tuple[int, int]] = None
        self.hl_moves: list = []
        self.hl_attacks: list = []
        self.hl_stuns: dict = {}
        self.hl_spells: list = []

_RSTATE = RendererState()

def get_cached_highlights(gs: Any, r: int, c: int) -> Tuple[list, list, dict, list]:
    h = gs.get_state_hash()
    if _RSTATE.hl_hash == h and _RSTATE.hl_pos == (r, c):
        return _RSTATE.hl_moves, _RSTATE.hl_attacks, _RSTATE.hl_stuns, _RSTATE.hl_spells
    p = gs.board[r][c]
    moves = p.get_valid_moves(r, c, gs.board, gs.tile_effects) if p else []
    attacks = p.get_valid_attacks(r, c, gs.board, gs.tile_effects) if p else []
    stuns = p.get_valid_stuns(r, c, gs.board, gs.tile_effects) if p else {}
    spells = p.get_valid_spells(r, c, gs.board, gs.tile_effects) if hasattr(p, 'get_valid_spells') else []
    _RSTATE.hl_hash = h
    _RSTATE.hl_pos = (r, c)
    _RSTATE.hl_moves, _RSTATE.hl_attacks = moves, attacks
    _RSTATE.hl_stuns, _RSTATE.hl_spells = stuns, spells
    return moves, attacks, stuns, spells

def draw_text_wrapped(ecra: pygame.Surface, text: str, font: pygame.font.Font, color: Tuple[int, int, int], x: int, y: int, max_width: int) -> int:
    for paragraph in str(text).split('\n'):
        words = paragraph.split(' ')
        current_line = ""
        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    ecra.blit(font.render(current_line, True, color), (x, y))
                    y += font.get_linesize() + 2
                current_line = word + " "
        if current_line:
            ecra.blit(font.render(current_line, True, color), (x, y))
            y += font.get_linesize() + 2
    return y

def desenhar_botao(ecra: pygame.Surface, rect: pygame.Rect, texto: str, cor_fundo: Tuple[int, int, int], cor_texto: Tuple[int, int, int] = COLORS["text"], font_size: int = 32, subtexto: Optional[str] = None) -> None:
    pygame.draw.rect(ecra, cor_fundo, rect, border_radius=10)
    font = FontManager.get("arial", font_size, bold=True)
    txt_surf = font.render(texto, True, cor_texto)
    y_center = rect.y + 10 if subtexto else rect.y + rect.height//2 - txt_surf.get_height()//2
    ecra.blit(txt_surf, (rect.x + rect.width//2 - txt_surf.get_width()//2, y_center))
    if subtexto:
        font_sub = FontManager.get("arial", 16)
        sub_surf = font_sub.render(subtexto, True, (240, 240, 240))
        ecra.blit(sub_surf, (rect.x + rect.width//2 - sub_surf.get_width()//2, rect.y + 45))

def desenhar_texto_animado(ecra: pygame.Surface, texto: str, tx: int, base_y: int, pulsar: float, cor: Tuple[int,int,int], font: pygame.font.Font) -> None:
    txt_surf = font.render(texto, True, cor)
    vfx_surf = pygame.Surface((txt_surf.get_width(), txt_surf.get_height()), pygame.SRCALPHA)
    vfx_surf.blit(txt_surf, (0, 0))
    vfx_surf.set_alpha(int(160 + 95 * pulsar))
    ecra.blit(vfx_surf, (tx, base_y - txt_surf.get_height()))

def desenhar_coordenadas(ecra: pygame.Surface, tam_casa: int, off_x: int, off_y: int) -> None:
    fonte = FontManager.get("arial", 14, bold=True)
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for c in range(COLUNAS):
        lbl = letras[c] if c < len(letras) else str(c)
        txt = fonte.render(lbl, True, COLORS["text_muted"])
        ecra.blit(txt, (off_x + c * tam_casa + tam_casa//2 - txt.get_width()//2, off_y + LINHAS * tam_casa + 5))
    for r in range(LINHAS):
        txt = fonte.render(str(LINHAS - r), True, COLORS["text_muted"])
        ecra.blit(txt, (off_x - txt.get_width() - 8, off_y + r * tam_casa + tam_casa//2 - txt.get_height()//2))

def desenhar_tabuleiro(ecra: pygame.Surface, gs: Any, tam_casa: int, off_x: int, off_y: int) -> None:
    key = (tam_casa, LINHAS, COLUNAS)
    if _RSTATE.board_size_key != key or not _RSTATE.board_bg:
        bg = pygame.Surface((COLUNAS * tam_casa, LINHAS * tam_casa))
        for r in range(LINHAS):
            for c in range(COLUNAS):
                cor = COLORS["board_light"] if (r + c) % 2 == 0 else COLORS["board_dark"]
                pygame.draw.rect(bg, cor, pygame.Rect(c * tam_casa, r * tam_casa, tam_casa, tam_casa))
        _RSTATE.board_bg = bg
        _RSTATE.board_size_key = key
    ecra.blit(_RSTATE.board_bg, (off_x, off_y))
    last_start = gs.last_move["start"] if getattr(gs, 'last_move', None) else None
    last_end = gs.last_move["end"] if getattr(gs, 'last_move', None) else None
    for r in range(LINHAS):
        for c in range(COLUNAS):
            rect = pygame.Rect(off_x + c * tam_casa, off_y + r * tam_casa, tam_casa, tam_casa)
            if (r, c) == last_start or (r, c) == last_end:
                VFXManager.draw_tint(ecra, (230, 230, 120) if (r + c) % 2 == 0 else (180, 180, 80), 180, rect)
            if gs.tile_effects and gs.tile_effects[r][c]:
                efeito = gs.tile_effects[r][c]["type"]
                if efeito == "ice":
                    VFXManager.draw_tint(ecra, (100, 200, 255), 150, rect)
                    pygame.draw.rect(ecra, (50, 150, 255), rect, 2)
                elif efeito == "fire":
                    VFXManager.draw_tint(ecra, (255, 100, 0), 80, rect)

def desenhar_pecas(ecra: pygame.Surface, board: list, tam_casa: int, off_x: int, off_y: int) -> None:
    fonte = FontManager.get("arial", int(tam_casa * 0.4))
    fonte_vida = FontManager.get("arial", int(tam_casa * 0.3), bold=True)
    for r in range(LINHAS):
        for c in range(COLUNAS):
            p = board[r][c]
            if p:
                cx = off_x + c * tam_casa + tam_casa // 2
                cy = off_y + r * tam_casa + tam_casa // 2
                img = AssetManager.get_image(p.name, p.team, tam_casa)
                if img:
                    cor_base = (100, 140, 200) if p.team == 'brancas' else (200, 80, 80)
                    pygame.draw.circle(ecra, cor_base, (cx, cy), int(tam_casa * 0.38))
                    pygame.draw.circle(ecra, (20, 20, 20), (cx, cy), int(tam_casa * 0.38), 2)
                    ecra.blit(img, img.get_rect(center=(cx, cy)))
                else:
                    cor_peca = (230, 230, 230) if p.team == 'brancas' else (50, 50, 50)
                    pygame.draw.circle(ecra, cor_peca, (cx, cy), int(tam_casa * 0.38))
                    cor_texto = (0,0,0) if p.team == 'brancas' else COLORS["text"]
                    acronym = getattr(p, 'acronym', None)
                    texto = fonte.render(acronym if acronym else p.name[:2].capitalize(), True, cor_texto)
                    ecra.blit(texto, texto.get_rect(center=(cx, cy)))
                if p.stun_timer > 0:
                    pygame.draw.circle(ecra, (0, 150, 255), (cx, cy), int(tam_casa * 0.42), 4)
                if getattr(p, 'lifespan', None) is not None:
                    txt_vida = fonte_vida.render(str(p.lifespan), True, COLORS["danger"])
                    pos_x = off_x + c * tam_casa + tam_casa - int(tam_casa * 0.25)
                    pos_y = off_y + r * tam_casa + int(tam_casa * 0.05)
                    ecra.blit(fonte_vida.render(str(p.lifespan), True, (0,0,0)), (pos_x + 1, pos_y + 1))
                    ecra.blit(txt_vida, (pos_x, pos_y))

def desenhar_destaques_com_hover(ecra: pygame.Surface, gs: Any, casa_selecionada: Optional[Tuple[int,int]], hover_pos: Optional[Tuple[int,int]], tam_casa: int, off_x: int, off_y: int) -> None:
    if not casa_selecionada: return
    r, c = casa_selecionada
    p = gs.board[r][c]
    if not p: return
    movimentos, ataques, stuns, spells = get_cached_highlights(gs, r, c)
    ticks = pygame.time.get_ticks()
    pulsar = (math.sin(ticks / 300.0) + 1.0) / 2.0
    font_vfx = FontManager.get("arial", max(12, int(tam_casa * 0.28)), bold=True)
    for mr, mc in movimentos:
        alpha = int(80 + 120 * (1.0 if hover_pos == (mr, mc) else pulsar))
        rect = pygame.Rect(off_x + mc * tam_casa, off_y + mr * tam_casa, tam_casa, tam_casa)
        VFXManager.draw_tint(ecra, COLORS["move"], alpha, rect)
        if hover_pos == (mr, mc): pygame.draw.rect(ecra, COLORS["success"], rect, 3)
    for ar, ac in ataques:
        alpha = int(90 + 120 * pulsar) if hover_pos == (ar, ac) else int(60 + 80 * pulsar)
        rect = pygame.Rect(off_x + ac * tam_casa, off_y + ar * tam_casa, tam_casa, tam_casa)
        VFXManager.draw_tint(ecra, COLORS["attack"], alpha, rect)
        cx, cy = rect.center
        thickness = max(1, int(2 + 3 * pulsar))
        leng = int(tam_casa * (0.35 + 0.05 * pulsar))
        pygame.draw.line(ecra, COLORS["danger"], (cx - leng, cy), (cx + leng, cy), thickness)
        pygame.draw.line(ecra, COLORS["danger"], (cx, cy - leng), (cx, cy + leng), thickness)
    for foco, info in stuns.items():
        foco_r, foco_c = foco
        is_hovered = hover_pos == foco
        for aoe_r, aoe_c in info["aoe"]:
            if (aoe_r, aoe_c) == (foco_r, foco_c): continue
            alvo = gs.board[aoe_r][aoe_c]
            is_enemy = alvo and alvo.team != p.team
            alpha_a = int(90 + 60 * pulsar) if is_hovered else int(25 + 15 * pulsar)
            cor_aoe = COLORS["stun_hit"] if is_enemy else COLORS["stun_aoe"]
            rect = pygame.Rect(off_x + aoe_c * tam_casa, off_y + aoe_r * tam_casa, tam_casa, tam_casa)
            VFXManager.draw_tint(ecra, cor_aoe, alpha_a, rect)
        alvo_centro = gs.board[foco_r][foco_c]
        enemy_center = alvo_centro and alvo_centro.team != p.team
        alpha_c = int(140 + 70 * pulsar) if is_hovered else int(60 + 30 * pulsar)
        cor_centro = COLORS["attack"] if enemy_center else COLORS["spell"]
        rect_center = pygame.Rect(off_x + foco_c * tam_casa, off_y + foco_r * tam_casa, tam_casa, tam_casa)
        VFXManager.draw_tint(ecra, cor_centro, alpha_c, rect_center)
        pygame.draw.rect(ecra, COLORS["text"], rect_center, 2 if is_hovered else 1)
        if is_hovered or enemy_center:
            txt_str = "STUN" if info["has_enemy"] else "MIRA"
            cor_txt = COLORS["text"] if info["has_enemy"] else COLORS["text_muted"]
            osc = int(math.sin((ticks + (foco_r * 13 + foco_c * 7)) / 280.0) * (tam_casa * 0.12))
            desenhar_texto_animado(ecra, txt_str, rect_center.x + tam_casa//2 - font_vfx.size(txt_str)[0]//2, rect_center.y - 6 + osc, pulsar, cor_txt, font_vfx)
    for spell in spells:
        tr, tc = spell.get("target", (r, c)) if isinstance(spell, dict) else (spell[0], spell[1])
        nome_feitico = spell.get("spell_type", "SPELL").upper() if isinstance(spell, dict) else "SPELL"
        alpha = int(90 + 120 * pulsar) if hover_pos == (tr, tc) else int(60 + 80 * pulsar)
        rect = pygame.Rect(off_x + tc * tam_casa, off_y + tr * tam_casa, tam_casa, tam_casa)
        VFXManager.draw_tint(ecra, COLORS["spell"], alpha, rect)
        osc = int(math.sin((ticks + (tr * 13 + tc * 7)) / 280.0) * (tam_casa * 0.12))
        desenhar_texto_animado(ecra, nome_feitico, rect.x + tam_casa//2 - font_vfx.size(nome_feitico)[0]//2, rect.y - 6 + osc, pulsar, COLORS["text"], font_vfx)

def desenhar_painel_heroi(ecra: pygame.Surface, peca: Any, off_x: int, off_y: int, width: int, height: int) -> None:
    pygame.draw.rect(ecra, COLORS["panel_bg"], (off_x, off_y, width, height), border_radius=10)
    pygame.draw.rect(ecra, (150, 150, 200), (off_x, off_y, width, height), 2, border_radius=10)
    fonte_tit = FontManager.get("arial", 28, bold=True)
    fonte_sub = FontManager.get("arial", 18, italic=True)
    fonte_desc = FontManager.get("arial", 16)
    tam_avatar = min(96, int(width * 0.22))
    img = AssetManager.get_image(peca.name, peca.team, tam_avatar)
    avatar_rect = pygame.Rect(off_x + width - tam_avatar - 16, off_y + 16, tam_avatar, tam_avatar)
    if img:
        ecra.blit(img, avatar_rect.topleft)
        pygame.draw.rect(ecra, (80, 80, 90), (avatar_rect.x - 6, avatar_rect.y - 6, tam_avatar + 12, tam_avatar + 12), 2, border_radius=8)
    else:
        pygame.draw.rect(ecra, (60, 60, 70), avatar_rect, border_radius=8)
    cor_nome = COLORS["white_team"] if peca.team == 'brancas' else COLORS["black_team"]
    ecra.blit(fonte_tit.render(peca.name, True, cor_nome), (off_x + 20, off_y + 18))
    ecra.blit(fonte_sub.render(f"Facção: {peca.team.capitalize()}", True, COLORS["text_muted"]), (off_x + 20, off_y + 50))
    y_pix = off_y + 90
    ecra.blit(fonte_desc.render(f"Custo: {peca.cost} pts", True, COLORS["text"]), (off_x + 20, y_pix))
    y_pix += 30
    if peca.stun_timer > 0:
        ecra.blit(fonte_desc.render(f"⚠️ ATORDOADO ({peca.stun_timer} turnos)", True, COLORS["warning"]), (off_x + 20, y_pix))
        y_pix += 26
    if getattr(peca, 'lifespan', None) is not None:
        ecra.blit(fonte_desc.render(f"⏳ Vida restante: {peca.lifespan} turnos", True, COLORS["danger"]), (off_x + 20, y_pix))
        y_pix += 26
    pygame.draw.line(ecra, (100, 100, 100), (off_x + 16, y_pix + 8), (off_x + width - tam_avatar - 32, y_pix + 8))
    y_pix += 18
    ecra.blit(fonte_sub.render("Descrição:", True, (200, 200, 200)), (off_x + 20, y_pix))
    y_pix += 22
    y_pix = draw_text_wrapped(ecra, getattr(peca, 'descricao', 'Unidade padrão.'), fonte_desc, COLORS["text"], off_x + 20, y_pix, width - 40)
    y_pix += 10
    ecra.blit(fonte_sub.render("Passiva:", True, (200, 200, 200)), (off_x + 20, y_pix))
    y_pix += 22
    draw_text_wrapped(ecra, getattr(peca, 'passiva', 'Nenhuma.'), fonte_desc, (140, 255, 160), off_x + 20, y_pix, width - 40)

def desenhar_log(ecra: pygame.Surface, gs: Any, off_x_log: int, off_y: int, width: int, height: int) -> None:
    pygame.draw.rect(ecra, (40, 40, 40), (off_x_log, off_y, width, height), border_radius=10)
    tit = FontManager.get("arial", 24, bold=True).render("Registo de Batalha", True, COLORS["text"])
    ecra.blit(tit, (off_x_log + 20, off_y + 20))
    pygame.draw.line(ecra, (100, 100, 100), (off_x_log + 20, off_y + 50), (off_x_log + width - 20, off_y + 50), 2)
    y = off_y + 60
    for log in gs.move_log[-12:]:
        cor_txt = COLORS["white_team"] if log["team"] == "brancas" else COLORS["black_team"]
        ecra.blit(FontManager.get("arial", 24, bold=True).render(log["short"], True, cor_txt), (off_x_log + 20, y))
        y += 40

def desenhar_analise(ecra: pygame.Surface, off_x_log: int, off_y: int, width: int, height: int, move_log: list, best_moves_dict: dict, selected_idx: Optional[int] = None) -> list:
    pygame.draw.rect(ecra, (20, 20, 30), (off_x_log, off_y, width, height), border_radius=10)
    pygame.draw.rect(ecra, (100, 100, 255), (off_x_log, off_y, width, height), 2, border_radius=10)
    fonte_tit = FontManager.get("arial", 22, bold=True)
    fonte_txt = FontManager.get("arial", 15)
    fonte_best = FontManager.get("arial", 15, bold=True)
    tit = fonte_tit.render("Análise do Motor (Stockfish)", True, COLORS["white_team"])
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
        txt_short = fonte_tit.render(log["short"], True, COLORS["text"])
        ecra.blit(txt_short, (off_x_log + 15, y))
        if id_jogada in best_moves_dict:
            dados_analise = best_moves_dict[id_jogada]
            if dados_analise["forced_mate"]:
                txt_analise = fonte_best.render(f"Letal em {dados_analise['forced_mate']}", True, COLORS["danger"])
            else:
                txt_analise = fonte_best.render(f"Melhor: {dados_analise['best_move_str']} (Score: {dados_analise['score']})", True, COLORS["success"])
        else:
            txt_analise = fonte_txt.render("A analisar profundidade...", True, COLORS["text_muted"])
        ecra.blit(txt_analise, (off_x_log + 15, y + 22))
        y += 52
    return rects_clicaveis

def desenhar_hud_jogadores(ecra: pygame.Surface, off_x: int, off_y_top: int, off_y_bot: int, tam_casa: int, bot_name: str, gs: Any) -> Tuple[pygame.Rect, pygame.Rect]:
    altura = 36
    fonte = FontManager.get("arial", 18, bold=True)
    h = gs.get_state_hash()
    if _RSTATE.hud_hash != h:
        w_mat, b_mat = 0, 0
        for r in range(LINHAS):
            for c in range(COLUNAS):
                p = gs.board[r][c]
                if p:
                    if p.team == 'brancas': w_mat += getattr(p, 'cost', 0)
                    else: b_mat += getattr(p, 'cost', 0)
        _RSTATE.hud_hash = h
        _RSTATE.white_mat = w_mat
        _RSTATE.black_mat = b_mat
    largura_total = COLUNAS * tam_casa
    terco = largura_total // 3
    rect_top = pygame.Rect(off_x, off_y_top, largura_total, altura)
    pygame.draw.rect(ecra, COLORS["hud_bg"], rect_top)
    pygame.draw.rect(ecra, (80, 80, 90), rect_top, 1)
    ecra.blit(fonte.render(f"Inimigo: {bot_name}", True, COLORS["text"]), (rect_top.x + 8, rect_top.y + 6))
    ecra.blit(fonte.render(f"Brancas: {int(getattr(gs, 'white_time', 0))}s", True, (200,200,200)), (rect_top.x + terco, rect_top.y + 6))
    ecra.blit(fonte.render(f"Pretas: {int(getattr(gs, 'black_time', 0))}s", True, (200,200,200)), (rect_top.x + terco + int(terco*0.4), rect_top.y + 6))
    ecra.blit(fonte.render(f"Mat: {_RSTATE.white_mat}", True, (180, 255, 180)), (rect_top.x + terco*2, rect_top.y + 6))
    ecra.blit(fonte.render(f"Mat: {_RSTATE.black_mat}", True, (255, 180, 180)), (rect_top.x + terco*2 + int(terco*0.4), rect_top.y + 6))
    rect_bot = pygame.Rect(off_x, off_y_bot, largura_total, altura)
    pygame.draw.rect(ecra, (18, 18, 22), rect_bot)
    pygame.draw.rect(ecra, (80, 80, 90), rect_bot, 1)
    ecra.blit(fonte.render("Jogador", True, COLORS["text"]), (rect_bot.x + 8, rect_bot.y + 6))
    return rect_top, rect_bot

def desenhar_eval_bar(ecra: pygame.Surface, gs: Any, off_x: int, altura_tabuleiro: int, off_y_tab: int) -> pygame.Rect:
    score = getattr(gs, 'current_score', 0) or 0
    norm = max(-1.0, min(1.0, score / 20000.0))
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

def desenhar_loja_dinamica(ecra: pygame.Surface, off_x: int, off_y: int, width: int, height: int, catalogo: list, pontos: int, peca_selecionada: Optional[str]) -> Tuple[dict, pygame.Rect]:
    pygame.draw.rect(ecra, (30, 30, 40), (off_x, off_y, width, height), border_radius=10)
    pygame.draw.rect(ecra, (100, 150, 200), (off_x, off_y, width, height), 2, border_radius=10)
    fonte_tit = FontManager.get("arial", 24, bold=True)
    fonte_item = FontManager.get("arial", 18, bold=True)
    fonte_pts = FontManager.get("arial", 16)
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
    btn_r_y = off_y + height - 70
    btn_r = pygame.Rect(off_x + 20, btn_r_y, width - 40, 50)
    for i, item in enumerate(catalogo):
        col = i % colunas
        row = i // colunas
        x = off_x + 20 + col * (largura_btn + espaco_x)
        y = start_y + row * (altura_btn + espaco_y)
        if y + altura_btn > btn_r_y - 10: break
        if item["cost"] > pontos: cor_btn, cor_txt = (60, 40, 40), COLORS["text_muted"]
        elif item["name"] == peca_selecionada: cor_btn, cor_txt = (100, 200, 100), COLORS["text"]
        else: cor_btn, cor_txt = (60, 60, 80), (220, 220, 220)
        rect = pygame.Rect(x, y, largura_btn, altura_btn)
        pygame.draw.rect(ecra, cor_btn, rect, border_radius=6)
        if item["cost"] <= pontos:
            pygame.draw.rect(ecra, (100, 100, 150), rect, 1, border_radius=6)
            botoes[item["name"]] = rect
        ecra.blit(fonte_item.render(item["name"], True, cor_txt), (x + 8, y + 5))
        cor_custo = (150, 255, 150) if item["cost"] <= pontos else cor_txt
        ecra.blit(fonte_pts.render(f"{item['cost']} pts", True, cor_custo), (x + 8, y + 24))
    desenhar_botao(ecra, btn_r, "Batalhar! (Pronto)", COLORS["btn_primary"], font_size=24)
    return botoes, btn_r

def desenhar_menu_principal(ecra: pygame.Surface, w: int, h: int) -> Tuple[pygame.Rect, pygame.Rect]:
    ecra.fill(COLORS["bg"])
    txt_tit = FontManager.get("arial", 64, bold=True).render("REDWAR", True, COLORS["danger"])
    ecra.blit(txt_tit, (w//2 - txt_tit.get_width()//2, h * 0.25))
    btn_w = min(300, int(w * 0.4))
    btn_start = pygame.Rect(w//2 - btn_w//2, h * 0.5, btn_w, 60)
    desenhar_botao(ecra, btn_start, "Jogar", COLORS["btn_primary"])
    btn_info = pygame.Rect(w//2 - btn_w//2, h * 0.5 + 80, btn_w, 60)
    desenhar_botao(ecra, btn_info, "Enciclopédia", COLORS["btn_secondary"])
    return btn_start, btn_info

def desenhar_selecao_modo(ecra: pygame.Surface, w: int, h: int) -> Tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
    ecra.fill(COLORS["bg"])
    txt_tit = FontManager.get("arial", 48, bold=True).render("Selecione o Modo", True, COLORS["text"])
    ecra.blit(txt_tit, (w//2 - txt_tit.get_width()//2, h * 0.15))
    btn_w = min(300, int(w * 0.4))
    btn_ia = pygame.Rect(w//2 - btn_w//2, h * 0.35, btn_w, 60)
    desenhar_botao(ecra, btn_ia, "Jogar vs IA", COLORS["btn_primary"])
    btn_multi = pygame.Rect(w//2 - btn_w//2, h * 0.35 + 90, btn_w, 60)
    desenhar_botao(ecra, btn_multi, "Multiplayer (Em Breve)", COLORS["btn_disabled"], (120, 120, 120), 28)
    btn_voltar = pygame.Rect(w//2 - 100, h * 0.35 + 230, 200, 50)
    desenhar_botao(ecra, btn_voltar, "Voltar", COLORS["danger"], font_size=28)
    return btn_ia, btn_multi, btn_voltar

def desenhar_selecao_tipo_ia(ecra: pygame.Surface, w: int, h: int) -> Tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
    ecra.fill(COLORS["bg"])
    txt_tit = FontManager.get("arial", 48, bold=True).render("Comportamento da IA", True, COLORS["text"])
    ecra.blit(txt_tit, (w//2 - txt_tit.get_width()//2, h * 0.15))
    btn_w = min(400, int(w * 0.6))
    btn_normal = pygame.Rect(w//2 - btn_w//2, h * 0.35, btn_w, 80)
    desenhar_botao(ecra, btn_normal, "Modo Clássico", (100, 200, 100), (0,0,0), 28, "A IA pensa de forma tradicional, apenas no seu turno.")
    btn_predador = pygame.Rect(w//2 - btn_w//2, h * 0.35 + 110, btn_w, 80)
    desenhar_botao(ecra, btn_predador, "Modo Contínuo", COLORS["btn_danger"], COLORS["text"], 28, "A IA antecipa jogadas enquanto o humano pensa.")
    btn_voltar = pygame.Rect(w//2 - 100, h * 0.35 + 250, 200, 50)
    desenhar_botao(ecra, btn_voltar, "Voltar", COLORS["btn_secondary"], font_size=28)
    return btn_normal, btn_predador, btn_voltar

def desenhar_selecao_dificuldade(ecra: pygame.Surface, w: int, h: int, elo_atual: int) -> Tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
    ecra.fill(COLORS["bg"])
    fonte = FontManager.get("arial", 36)
    txt_tit = fonte.render("Nível de Dificuldade ELO", True, COLORS["text"])
    ecra.blit(txt_tit, (w//2 - txt_tit.get_width()//2, h * 0.15))
    bar_w = min(400, int(w * 0.6))
    bar_x = w//2 - bar_w//2
    pygame.draw.rect(ecra, (50, 50, 50), (bar_x, h * 0.3, bar_w, 20))
    ratio = max(0.0, min(1.0, (elo_atual - 100) / 2500.0))
    x_elo = bar_x + int(ratio * bar_w)
    rect_elo_drag = pygame.Rect(x_elo - 10, h * 0.3 - 10, 20, 40)
    pygame.draw.rect(ecra, COLORS["danger"], rect_elo_drag)
    txt_elo = fonte.render(f"Força de Jogo Estimada: {elo_atual}", True, COLORS["text"])
    ecra.blit(txt_elo, (w//2 - txt_elo.get_width()//2, h * 0.22))
    txt_aviso = FontManager.get("arial", 20).render("Determina a profundidade e rigor da avaliação posicional", True, COLORS["white_team"])
    ecra.blit(txt_aviso, (w//2 - txt_aviso.get_width()//2, h * 0.4))
    btn_confirmar = pygame.Rect(w//2 - 150, h * 0.55, 300, 60)
    desenhar_botao(ecra, btn_confirmar, "Iniciar Batalha", (100, 200, 100), font_size=28)
    btn_voltar = pygame.Rect(w//2 - 100, h * 0.55 + 90, 200, 50)
    desenhar_botao(ecra, btn_voltar, "Voltar", COLORS["btn_secondary"], font_size=28)
    return rect_elo_drag, btn_confirmar, btn_voltar

def desenhar_enciclopedia(ecra: pygame.Surface, w: int, h: int, catalogo: list) -> pygame.Rect:
    btn_voltar = pygame.Rect(w//2 - 60, h - 60, 120, 40)
    desenhar_botao(ecra, btn_voltar, "Voltar", (150, 50, 50))
    return btn_voltar
