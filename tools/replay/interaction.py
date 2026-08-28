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
    """Require confirmation when an offensive spell is aimed at an ally/self."""
    if action.get("type") != "spell":
        return False
    spell_name = str(action.get("spell_name", "")).casefold()
    if spell_name in SUPPORT_SPELLS:
        return False
    r, c = action["end"]
    target = gs.board[r][c]
    return bool(target is not None and target.team == "brancas")


def _button_rects(pygame: Any, width: int, height: int, count: int) -> list[Any]:
    button_w = min(420, max(220, width - 80))
    button_h = 52
    gap = 12
    total_h = count * button_h + max(0, count - 1) * gap
    top = (height - total_h) // 2
    left = (width - button_w) // 2
    return [pygame.Rect(left, top + i * (button_h + gap), button_w, button_h) for i in range(count)]


def _prompt(controller: Any, title: str, labels: list[str], *, allow_cancel: bool = True) -> int | None:
    """Render a blocking, deterministic selection dialog using current Pygame surface."""
    import pygame

    font = pygame.font.SysFont("arial", 28, bold=True)
    font_small = pygame.font.SysFont("arial", 20)
    rects = _button_rects(pygame, *controller.ecra.get_size(), len(labels))
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and allow_cancel and event.key == pygame.K_ESCAPE:
                return None
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for index, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        return index
            if event.type == pygame.KEYDOWN and pygame.K_1 <= event.key <= pygame.K_9:
                index = event.key - pygame.K_1
                if index < len(labels):
                    return index

        overlay = pygame.Surface(controller.ecra.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        controller.ecra.blit(overlay, (0, 0))
        title_surface = font.render(title, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(controller.ecra.get_width() // 2, rects[0].y - 55))
        controller.ecra.blit(title_surface, title_rect)
        for i, (rect, label) in enumerate(zip(rects, labels), start=1):
            pygame.draw.rect(controller.ecra, (55, 55, 70), rect, border_radius=8)
            pygame.draw.rect(controller.ecra, (180, 180, 200), rect, 2, border_radius=8)
            txt = font_small.render(f"{i}. {label}", True, (255, 255, 255))
            controller.ecra.blit(txt, txt.get_rect(center=rect.center))
        controller.ecra.blit(
            font_small.render("ESC = cancelar", True, (190, 190, 190)),
            (20, controller.ecra.get_height() - 34),
        )
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

        clicked_piece = self.gs.board[r][c]
        if clicked_piece is not None and clicked_piece.team == "brancas":
            self.casa_selecionada = (r, c)
            return None

        actions = actions_for_destination(self.gs, sr, sc, r, c)
        if not actions:
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
                "Este poder está a ser usado contra um herói aliado. Confirmar?",
                [
                    f"Confirmar {action_label(chosen)}",
                    "Voltar e escolher outro alvo",
                ],
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
