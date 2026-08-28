"""Player-intent interaction policy for manual RedWar sessions."""

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
            actions.append({"type": "spawn", "start": (sr, sc), "end": target, "spawn_name": spawn[2]})

    for spell in piece.get_valid_spells(sr, sc, gs.board, gs.tile_effects):
        spell_target = spell.get("target") if isinstance(spell, dict) else spell
        if spell_target == target:
            actions.append({
                "type": "spell",
                "start": (sr, sc),
                "end": target,
                "spell_name": spell.get("spell_type", "spell") if isinstance(spell, dict) else "spell",
            })

    return actions


def action_label(action: dict[str, Any]) -> str:
    action_type = action["type"]
    if action_type == "spell":
        return f"Usar {str(action.get('spell_name', 'spell')).upper()}"
    if action_type == "spawn":
        return f"Invocar {action.get('spawn_name', 'unidade')}"
    return {"move": "Mover", "attack": "Atacar", "stun": "Atordoar"}.get(action_type, action_type.capitalize())


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
    """Show action choices in the existing right-hand game panel."""
    import pygame

    width, height = controller.ecra.get_size()
    off_y, off_x, tam_casa = controller.get_ui_metrics()
    panel_x = off_x + 8 * tam_casa + 30
    panel_w = max(220, width - panel_x - 20)

    title_font = pygame.font.SysFont("arial", 22, bold=True)
    body_font = pygame.font.SysFont("arial", 17)
    hint_font = pygame.font.SysFont("arial", 13)
    button_h = 44
    gap = 10
    button_x = panel_x + 14
    button_w = max(170, panel_w - 28)
    title_y = 48
    first_y = title_y + 48

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
                for index in range(len(labels)):
                    rect = pygame.Rect(button_x, first_y + index * (button_h + gap), button_w, button_h)
                    if rect.collidepoint(event.pos):
                        return index

        # The normal game frame is already visible behind this panel. Redraw it
        # using the controller's current renderer, then replace only the right
        # panel with the action chooser.
        controller.renderizar(
            w=width,
            h=height,
            off_x=off_x,
            off_y_tab=off_y,
            tam_casa=tam_casa,
            painel_x=panel_x,
        )

        panel_top = 12
        panel_h = height - 24
        panel_rect = pygame.Rect(panel_x, panel_top, panel_w, panel_h)
        pygame.draw.rect(controller.ecra, (18, 18, 24), panel_rect, border_radius=10)
        pygame.draw.rect(controller.ecra, (115, 115, 135), panel_rect, 1, border_radius=10)

        title_surface = title_font.render(title, True, (245, 245, 250))
        controller.ecra.blit(title_surface, (button_x, title_y))

        selected = getattr(controller, "casa_selecionada", None)
        hover = getattr(controller, "hover_pos", None)
        if selected is not None:
            sr, sc = selected
            sub = body_font.render(f"Herói: {controller.gs.board[sr][sc].name}", True, (205, 205, 215))
            controller.ecra.blit(sub, (button_x, title_y + 28))
        if hover is not None:
            r, c = hover
            target = body_font.render(f"Destino: {r + 1},{c + 1}", True, (175, 175, 190))
            controller.ecra.blit(target, (button_x, title_y + 48))

        current_y = first_y + 35
        for index, label in enumerate(labels, start=1):
            rect = pygame.Rect(button_x, current_y, button_w, button_h)
            pygame.draw.rect(controller.ecra, (48, 48, 62), rect, border_radius=7)
            pygame.draw.rect(controller.ecra, (150, 150, 170), rect, 1, border_radius=7)
            txt = body_font.render(f"{index}. {label}", True, (255, 255, 255))
            controller.ecra.blit(txt, txt.get_rect(center=rect.center))
            current_y += button_h + gap

        hint = hint_font.render("ESC para cancelar · teclas 1–9", True, (175, 175, 185))
        controller.ecra.blit(hint, (button_x, panel_rect.bottom - 28))
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
            index = _prompt(self, "Confirmar poder contra aliado?", [f"Confirmar {action_label(chosen)}", "Cancelar"])
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
