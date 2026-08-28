"""DEV-mode hover visualization for actionable board state.

The rules engine remains authoritative. This layer only improves visual
interpretation: every legal option stays visible, while the hovered square and
any active silence aura receive stronger semantic emphasis.
"""
from __future__ import annotations

from types import MethodType
from typing import Any

from tools.replay.interaction import actions_for_destination

_ACTIVE_CONTROLLER: Any = None
_ORIGINAL_HIGHLIGHTS = None
_ORIGINAL_PANEL = None


def _active_silence_cells(gs: Any) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    for r in range(len(gs.board)):
        for c in range(len(gs.board[r])):
            piece = gs.board[r][c]
            if piece is None or piece.name != "Inquisitor" or not piece.can_act():
                continue
            for rr in range(len(gs.board)):
                for cc in range(len(gs.board[rr])):
                    if max(abs(rr - r), abs(cc - c)) <= 2:
                        cells.add((rr, cc))
    return cells


def _hover_actions(controller: Any, gs: Any) -> list[dict[str, Any]]:
    if not controller.casa_selecionada or not controller.hover_pos:
        return []
    sr, sc = controller.casa_selecionada
    tr, tc = controller.hover_pos
    return actions_for_destination(gs, sr, sc, tr, tc)


def _draw_hover_overlay(ecra: Any, controller: Any, gs: Any, tam_casa: int, off_x: int, off_y: int) -> None:
    import pygame
    if not controller.casa_selecionada:
        return

    silence_cells = _active_silence_cells(gs)
    for r, c in silence_cells:
        rect = pygame.Rect(off_x + c * tam_casa, off_y + r * tam_casa, tam_casa, tam_casa)
        pygame.draw.rect(ecra, (155, 90, 180), rect, 2)

    if not controller.hover_pos:
        return
    tr, tc = controller.hover_pos
    hover_rect = pygame.Rect(off_x + tc * tam_casa, off_y + tr * tam_casa, tam_casa, tam_casa)
    actions = _hover_actions(controller, gs)

    pygame.draw.rect(ecra, (255, 255, 255), hover_rect, 3)
    pygame.draw.rect(ecra, (255, 220, 70), hover_rect.inflate(-6, -6), 2)

    if actions:
        labels = []
        for action in actions:
            kind = action["type"]
            if kind == "spell":
                labels.append(str(action.get("spell_name", "spell")).upper())
            elif kind == "spawn":
                labels.append(f"SPAWN {action.get('spawn_name', '')}".strip())
            else:
                labels.append(kind.upper())
        font = pygame.font.SysFont("arial", max(14, min(20, int(tam_casa * 0.30))), bold=True)
        text = " / ".join(labels)
        surface = font.render(text, True, (255, 255, 255))
        bg = surface.get_rect(midbottom=(hover_rect.centerx, hover_rect.top - 4)).inflate(12, 8)
        pygame.draw.rect(ecra, (20, 20, 25), bg, border_radius=6)
        pygame.draw.rect(ecra, (255, 255, 255), bg, 1, border_radius=6)
        ecra.blit(surface, surface.get_rect(center=bg.center))

    if controller.hover_pos in silence_cells:
        font = pygame.font.SysFont("arial", max(12, min(18, int(tam_casa * 0.25))), bold=True)
        text = font.render("SILÊNCIO", True, (255, 235, 255))
        bg = text.get_rect(midtop=(hover_rect.centerx, hover_rect.bottom + 4)).inflate(10, 6)
        pygame.draw.rect(ecra, (55, 25, 65), bg, border_radius=5)
        ecra.blit(text, text.get_rect(center=bg.center))


def _hover_panel_lines(controller: Any) -> list[str]:
    if controller is None or not controller.hover_pos:
        return []
    r, c = controller.hover_pos
    gs = controller.gs
    lines: list[str] = [f"Casa: {r + 1},{c + 1}"]
    piece = gs.board[r][c]
    effect = gs.tile_effects[r][c] if gs.tile_effects else None
    if piece is not None:
        lines.append(f"Herói: {piece.name}")
        if piece.stun_timer > 0:
            lines.append(f"Atordoado: {piece.stun_timer}")
        if getattr(piece, "lifespan", None) is not None:
            lines.append(f"Duração: {piece.lifespan}")
    if effect:
        etype = effect.get("type", "?")
        timer = effect.get("timer")
        lines.append(f"Efeito: {etype}" + (f" ({timer})" if timer is not None else ""))
    if (r, c) in _active_silence_cells(gs):
        lines.append("SILÊNCIO: poderes bloqueados")
    actions = _hover_actions(controller, gs)
    if actions:
        labels = []
        for action in actions:
            label = action["type"].upper()
            if action["type"] == "spell":
                label = str(action.get("spell_name", "spell")).upper()
            elif action["type"] == "spawn":
                label = f"SPAWN {action.get('spawn_name', '')}".strip()
            labels.append(label)
        lines.append("Ações: " + " / ".join(labels))
    elif controller.casa_selecionada:
        lines.append("Ações: nenhuma legal")
    return lines


def _draw_hover_panel_overlay(ecra: Any, controller: Any, painel_x: int, height: int) -> None:
    if controller is None or not controller.hover_pos:
        return
    import pygame
    lines = _hover_panel_lines(controller)
    if not lines:
        return
    box_h = min(height - 24, 24 * len(lines) + 18)
    box = pygame.Rect(painel_x + 12, 20 + height - box_h - 12, 326, box_h)
    pygame.draw.rect(ecra, (18, 18, 24), box, border_radius=8)
    pygame.draw.rect(ecra, (160, 160, 180), box, 1, border_radius=8)
    font = pygame.font.SysFont("arial", 16)
    y = box.y + 8
    for line in lines[: max(1, (box_h - 14) // 24)]:
        surface = font.render(line, True, (235, 235, 240))
        ecra.blit(surface, (box.x + 8, y))
        y += 24


def _patched_highlights(ecra: Any, gs: Any, casa_selecionada: Any, hover_pos: Any, tam_casa: int, off_x: int, off_y: int) -> None:
    _ORIGINAL_HIGHLIGHTS(ecra, gs, casa_selecionada, hover_pos, tam_casa, off_x, off_y)
    if _ACTIVE_CONTROLLER is not None:
        _draw_hover_overlay(ecra, _ACTIVE_CONTROLLER, gs, tam_casa, off_x, off_y)


def _patched_panel(ecra: Any, peca: Any, off_x: int, off_y: int, width: int, height: int) -> None:
    _ORIGINAL_PANEL(ecra, peca, off_x, off_y, width, height)


def install_hover_visuals(controller: Any) -> None:
    """Install DEV-only hover emphasis and hovered-cell diagnostics."""
    global _ACTIVE_CONTROLLER, _ORIGINAL_HIGHLIGHTS, _ORIGINAL_PANEL
    _ACTIVE_CONTROLLER = controller
    import ui.renderer as renderer
    if _ORIGINAL_HIGHLIGHTS is None:
        _ORIGINAL_HIGHLIGHTS = renderer.desenhar_destaques_com_hover
        renderer.desenhar_destaques_com_hover = _patched_highlights
    if _ORIGINAL_PANEL is None:
        _ORIGINAL_PANEL = renderer.desenhar_painel_heroi
        renderer.desenhar_painel_heroi = _patched_panel

    original_render = controller.renderizar

    def wrapped_render(self: Any, *args: Any, **kwargs: Any) -> Any:
        result = original_render(*args, **kwargs)
        if self.fase_atual in {"BATALHA", "ANALISE"} and args:
            painel_x = kwargs.get("painel_x", args[5] if len(args) > 5 else None)
            height = kwargs.get("h", args[1] if len(args) > 1 else self.ecra.get_height())
            if painel_x is not None:
                _draw_hover_panel_overlay(self.ecra, self, painel_x, height - 40)
        return result

    controller.renderizar = MethodType(wrapped_render, controller)
