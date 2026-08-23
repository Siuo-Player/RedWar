import sys
import os
import pygame
import math
from typing import Optional, Dict, Tuple, List, Any
from engine.config import LINHAS, COLUNAS

COLORS = {
    "bg": (30, 30, 30), "panel_bg": (25, 25, 35), "hud_bg": (20, 20, 24),
    "text": (255, 255, 255), "text_muted": (150, 150, 150),
    "white_team": (150, 200, 255), "black_team": (255, 120, 120),
    "move": (50, 255, 50), "attack": (255, 40, 40), "stun_aoe": (100, 150, 255),
    "stun_hit": (255, 120, 0), "spell": (200, 50, 255), "btn_primary": (50, 150, 255),
    "btn_danger": (200, 60, 60), "danger": (255, 70, 70), "success": (100, 255, 100),
    "warning": (255, 200, 50), "btn_disabled": (60, 60, 60), "btn_secondary": (100, 100, 100),
    "board_light": (200, 200, 200), "board_dark": (100, 100, 100)
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
        caminho_base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.dirname(__file__))
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

# O restante do renderer mantém os mesmos componentes/renderizadores da revisão anterior.
