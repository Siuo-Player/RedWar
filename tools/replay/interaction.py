"""Player-intent interaction policy for manual RedWar sessions.

This module is deliberately independent from the rules engine. It resolves a
board destination into one or more already-legal actions and asks the player
when the destination is semantically ambiguous or targets an allied unit with
an offensive spell.
"""

from __future__ import annotations

from types import MethodType
from typing import Any

SUPPORT_SPELLS = {"purify", "swap"}


def actions_for_destination(gs: Any, sr: int, sc: int, tr: int, tc: int) -> list[dict[str, Any]]:
    """Return every legal action whose destination is (tr, tc)."""
    piece = gs.board[sr][sc]
    if piece is None:
        return []

    actions: list[dict[str, Any]] = []
    target = (tr, tc)

    if target in piece.get_valid_moves(sr, sc, gs.board, gs.tile_effects):
        actions.append({"type": "move", "start": (sr, sc), "end": target})
    if target in piece.get_valid_attacks(sr, sc, gs.board, gs.tile_effects):
        actions.append({"type": "attack", "start": (sr, sc), "end": target})

    stuns = piece.get_valid_stuns(sr, sc, gs.board, gs.tile_effects)
    if target in stuns and stuns[target].get("has_enemy"):
        actions.append({"type": "stun", "start": (sr, sc), "end": target})

    for spawn in piece.get_valid_spawns(sr, sc, gs.board, gs.tile_effects):
        if target == (spawn[0], spawn[1]):
            actions.append(
                {
                    "type": "spawn",
                    "start": (sr, sc),
                    "end": target,
                    "spawn_name": spawn[2],
                }
            )

    for spell in piece.get_valid_spells(sr, sc, gs.board, gs.tile_effects):
        spell_target = spell.get("target") if isinstance(spell, dict) else spell
        if spell_target == target:
            actions.append(
                {
                    "type": "spell",
                    "start": (sr, sc),
                    "end": target,
                    "spell_name": spell.get("spell_type", "spell") if isinstance(spell, dict) else "spell",
                }
            )

    return actions


def action_label(action: dict[str, Any]) -> str:
    action_type = action["type"]
    if action_type == "spell":
        return f"Usar {str(action.get('spell_name', 'spell')).upper()}"
    if action_type == "spawn":
        return f"Invocar {action.get('spawn_name', 'unidade')}"
    return {
        "move": "Mover",
        "attack": "Atacar",
        "stun": "Atordoar",
    }.get(action_type, action_type.capitalize())


def needs_offensive_target_confirmation(gs: Any, action: dict[str, Any]) -> bool:
    """Require confirmation when an offensive spell is aimed at its caster's ally/self."""
    if action.get("type") != "spell":
        return False
    spell_name = str(action.get("spell_name", "")).casefold()
    if spell_name in SUPPORT_SPELLS:
        return False
    start_r, start_c = action.get("start", (None, None))
    end_r, end_c = action["end"]
    target = gs.board[end_r][end_c]
    caster = gs.board[start_r][start_c] if start_r is not None else None
    return bool(target is not None and caster is not None and target.team == caster.team)


def _prompt(controller: Any, title: str, labels: list[str], *, allow_cancel: bool = True) -> int | None:
    """Show a compact action picker without obscuring the board."""
    import pygame

    width, height = controller.ecra.get_size()
    board_left = 60
    board_top = 80
    board_size = 8 * min(width // 9, max(8, (height - 200) // 8))
    center_x = board_left + board_size // 2
    center_y = board_top + board_size // 2

    font = pygame.font.SysFont("arial", 18, bold=True)
    small = pygame.font.SysFont("arial", 14)
    button_h = 38
    gap = 8
    max_button_w = 210
    button_ws = [min(max_button_w, max(120, font.size(f"{i}. {label}")[0] + 26)) for i, label in enumerate(labels, start=1)]
    total_w = sum(button_ws) + gap * (len(labels) - 1)
    left = max(12, min(width - total_w - 12, center_x - total_w // 2))
    top = max(12, center_y - button_h // 2)
    rects = []
    x = left
    for button_w in button_ws:
        rects.append(pygame.Rect(x, top, button_w, button_h))
        x += button_w + gap

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if allow_cancel and event.key == pygame.K_ESCAPE:
                    return None
                if pygame.K_1 <= event.key <= pygame.K_9:
                    index = event.key - pygame.K_1
                    if index < len(labels):
                        return index
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for index, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        return index

        # Keep the complete board visible; only add a small local picker.
        selected = getattr(controller, "hover_pos", None)
        if selected is not None:
            r, c = selected
            try:
                off_y, off_x, tam_casa = controller.get_ui_metrics()
                target_x = off_x + c * tam_casa + tam_casa // 2
                target_y = off_y + r * tam_casa
                picker_w = total_w + 16
                picker_h = button_h + 34
                picker_left = max(8, min(width - picker_w - 8, target_x - picker_w // 2))
                picker_top = max(8, target_y - picker_h - 8)
                rects = []
                x = picker_left + 8
                for button_w in button_ws:
                    rects.append(pygame.Rect(x, picker_top + 26, button_w, button_h))
                    x += button_w + gap
                header_rect = pygame.Rect(picker_left, picker_top, picker_w, picker_h)
            except Exception:
                header_rect = pygame.Rect(left, top - 22, total_w, button_h + 30)
        else:
            header_rect = pygame.Rect(left, top - 22, total_w, button_h + 30)

        shadow = header_rect.move(3, 3)
        pygame.draw.rect(controller.ecra, (8, 8, 12), shadow, border_radius=9)
        pygame.draw.rect(controller.ecra, (34, 34, 44), header_rect, border_radius=9)
        pygame.draw.rect(controller.ecra, (170, 170, 190), header_rect, 2, border_radius=9)
        title_surface = small.render(title, True, (245, 245, 250))
        controller.ecra.blit(title_surface, title_surface.get_rect(midtop=(header_rect.centerx, header_rect.top + 6)))
        for i, (rect, label) in enumerate(zip(rects, labels), start=1):
            pygame.draw.rect(controller.ecra, (58, 58, 74), rect, border_radius=7)
            pygame.draw.rect(controller.ecra, (145, 145, 165), rect, 1, border_radius=7)
            txt = font.render(f"{i}. {label}", True, (255, 255, 255))
            controller.ecra.blit(txt, txt.get_rect(center=rect.center))
        hint = small.render("ESC para cancelar", True, (185, 185, 195))
        hint_rect = hint.get_rect(midbottom=(header_rect.centerx, header_rect.bottom - 5))
        controller.ecra.blit(hint, hint_rect)
        pygame.display.flip()
        controller.clock.tick(60)


def _install_instance_wrapper(controller: Any) -> None:
    original = controller.tratar_cliques

    def wrapped(self: Any, mx: int, my: int, pos: tuple[int, int]) -> Any:
        if not (
            self.fase_atual == "BATALHA"
            and self.gs.white_to_move
            and not self.gs.game_over
            and self.hover_pos
        ):
            return original(mx, my, pos)

        r, c = self.hover_pos
        if not self.casa_selecionada:
            piece = self.gs.board[r][c]
            if piece is not None and piece.team == "brancas":
                self.casa_selecionada = (r, c)
            return None

        sr, sc = self.casa_selecionada
        if (sr, sc) == (r, c):
            self.casa_selecionada = None
            return None

        actions = actions_for_destination(self.gs, sr, sc, r, c)
        if not actions:
            clicked_piece = self.gs.board[r][c]
            if clicked_piece is not None and clicked_piece.team == "brancas":
                self.casa_selecionada = (r, c)
            return None

        if len(actions) == 1:
            chosen = actions[0]
        else:
            labels = [action_label(action) for action in actions]
            index = _prompt(self, "Escolhe a ação", labels)
            if index is None:
                return None
            chosen = actions[index]

        if needs_offensive_target_confirmation(self.gs, chosen):
            index = _prompt(
                self,
                "Confirmar poder contra aliado?",
                [f"Confirmar {action_label(chosen)}", "Cancelar"],
                allow_cancel=True,
            )
            if index != 0:
                return None

        if self.modo_predador and self.pondering_active and self.bot_ativo is not None and hasattr(self.bot_ativo, "stop_pondering"):
            self.bot_ativo.stop_pondering()
            self.pondering_active = False

        _, off_x, tam_casa = self.get_ui_metrics()
        self.desenhar_animacao(self.gs, chosen["start"], chosen["end"], chosen["type"], tam_casa, off_x, 80)
        self.gs.execute_action(chosen)
        self.casa_selecionada = None
        return None

    controller.tratar_cliques = MethodType(wrapped, controller)


def install_intent_interaction(controller: Any) -> None:
    """Install the manual-play interaction policy on one game controller."""
    _install_instance_wrapper(controller)
