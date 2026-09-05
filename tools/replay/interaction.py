"""Player-intent interaction policy for manual RedWar sessions.

The rules engine remains authoritative. This module only resolves player intent
and presents contextual information using the existing battle sidebar.
"""

from __future__ import annotations

from types import MethodType
from typing import Any

from engine.actions import normalize_action
from tools.replay.interaction_state import InteractionContext, InteractionState, derive_interaction_state
from ui.hero_encyclopedia_panel import (
    HeroEncyclopediaPanelState,
    encyclopedia_lines,
    scroll_panel,
    select_hero,
    selected_hero_context,
    toggle_panel,
)
from ui.sidebar_layout import sidebar_layout_for_viewport
from ui.sidebar_theme import SIDEBAR_THEME

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
            actions.append({
                "type": "spawn",
                "start": (sr, sc),
                "end": target,
                "spawn_name": spawn[2],
            })

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
    """Require confirmation when an offensive spell targets an allied unit."""
    if action.get("type") != "spell":
        return False
    if str(action.get("spell_name", "")).casefold() in SUPPORT_SPELLS:
        return False
    start_r, start_c = action.get("start", (None, None))
    end_r, end_c = action["end"]
    target = gs.board[end_r][end_c]
    caster = gs.board[start_r][start_c] if start_r is not None else None
    return bool(target is not None and caster is not None and target.team == caster.team)


def _sync_interaction_state(
    controller: Any,
    *,
    destination: tuple[int, int] | None = None,
    action_count: int | None = None,
    confirmation_required: bool | None = None,
) -> InteractionState:
    """Mirror current UI intent into the formal state model without changing authority."""
    if destination is not None:
        controller._interaction_destination = destination
    elif not hasattr(controller, "_interaction_destination"):
        controller._interaction_destination = None
    if action_count is not None:
        controller._interaction_action_count = action_count
    elif not hasattr(controller, "_interaction_action_count"):
        controller._interaction_action_count = 0
    if confirmation_required is not None:
        controller._interaction_confirmation_required = confirmation_required
    elif not hasattr(controller, "_interaction_confirmation_required"):
        controller._interaction_confirmation_required = False

    gs = getattr(controller, "gs", None)
    context = InteractionContext(
        selected_hero=getattr(controller, "casa_selecionada", None),
        hovered_cell=getattr(controller, "hover_pos", None),
        destination=getattr(controller, "_interaction_destination", None),
        action_count=getattr(controller, "_interaction_action_count", 0),
        confirmation_required=getattr(controller, "_interaction_confirmation_required", False),
        game_over=bool(getattr(gs, "game_over", False)),
        enemy_turn=bool(gs is not None and not getattr(gs, "white_to_move", True)),
        replay_analysis=bool(getattr(controller, "replay_analysis", False)),
    )
    state = derive_interaction_state(context)
    controller._interaction_state = state
    return state


def _clear_pending_interaction(controller: Any) -> None:
    controller._interaction_destination = None
    controller._interaction_action_count = 0
    controller._interaction_confirmation_required = False
    _sync_interaction_state(controller)


def _panel_geometry(controller: Any) -> tuple[int, int, int]:
    width, _ = controller.ecra.get_size()
    off_y, off_x, tam_casa = controller.get_ui_metrics()
    layout = sidebar_layout_for_viewport(
        viewport_width=width,
        board_left=off_x,
        board_width=8 * tam_casa,
        right_margin=20,
        board_gap=30,
        minimum_width=240,
    )
    return layout.panel_x, layout.panel_width, off_y


def _selected_piece(controller: Any) -> Any:
    selected = getattr(controller, "casa_selecionada", None)
    if selected is None:
        return None
    r, c = selected
    return controller.gs.board[r][c]


def _sync_encyclopedia_selection(controller: Any) -> HeroEncyclopediaPanelState:
    piece = _selected_piece(controller)
    hero_name = getattr(piece, "name", None)
    state = getattr(controller, "_hero_encyclopedia_state", HeroEncyclopediaPanelState())
    state = select_hero(state, hero_name)
    controller._hero_encyclopedia_state = state
    return state


def _selected_panel_rect(controller: Any) -> Any:
    import pygame
    panel_x, panel_w, _ = _panel_geometry(controller)
    panel_h = controller.ecra.get_height() - 28
    selected_h = max(180, min(330, int(panel_h * 0.36)))
    return pygame.Rect(panel_x, 14, panel_w, selected_h)


def _encyclopedia_button_rect(controller: Any) -> Any:
    import pygame
    rect = _selected_panel_rect(controller)
    return pygame.Rect(rect.x + 12, rect.bottom - 42, max(80, rect.width - 24), 30)


def _sidebar_context_rect(controller: Any, action_labels: list[str] | None = None) -> Any:
    import pygame
    panel_x, panel_w, _ = _panel_geometry(controller)
    panel_h = controller.ecra.get_height() - 28
    gap = 10
    selected_h = max(180, min(330, int(panel_h * 0.36)))
    action_h = 0
    if action_labels:
        action_h = min(max(118, 70 + len(action_labels) * 48), int(panel_h * 0.40))
    context_h = panel_h - selected_h - action_h - (2 if action_h else 1) * gap
    selected_rect = pygame.Rect(panel_x, 14, panel_w, selected_h)
    return pygame.Rect(panel_x, selected_rect.bottom + gap, panel_w, max(120, context_h))


def _encyclopedia_control_rects(controller: Any, action_labels: list[str] | None = None) -> tuple[Any, Any]:
    import pygame
    context_rect = _sidebar_context_rect(controller, action_labels)
    width = max(32, min(92, (context_rect.width - 30) // 2))
    up = pygame.Rect(context_rect.x + 10, context_rect.bottom - 34, width, 24)
    down = pygame.Rect(up.right + 8, up.y, width, 24)
    return up, down


def _draw_encyclopedia(ecra: Any, controller: Any, rect: Any, body: Any, small: Any) -> None:
    import pygame
    piece = _selected_piece(controller)
    state = _sync_encyclopedia_selection(controller)
    if piece is None or state.hero_name is None:
        ecra.blit(body.render("Seleciona um herói", True, SIDEBAR_THEME.text_muted), (rect.x + 12, rect.y + 52))
        return

    context = selected_hero_context(state.hero_name)
    lines = encyclopedia_lines(context)
    inner = pygame.Rect(rect.x + 10, rect.y + 42, max(0, rect.width - 20), max(0, rect.height - 82))
    line_h = max(18, small.get_height() + 5)
    visible = max(1, inner.height // line_h)
    state = scroll_panel(state, 0, line_count=len(lines), visible_lines=visible)
    controller._hero_encyclopedia_state = state
    start = state.scroll_offset
    end = min(len(lines), start + visible)
    y = inner.y
    for line in lines[start:end]:
        text = line
        while text:
            available = max(20, inner.width)
            clipped = text
            while clipped and small.size(clipped)[0] > available:
                clipped = clipped[:-1]
            if not clipped:
                break
            suffix = "" if len(clipped) == len(text) else "…"
            ecra.blit(small.render(clipped + suffix, True, SIDEBAR_THEME.text_secondary), (inner.x, y))
            y += line_h
            text = text[len(clipped):].lstrip()
            if y + line_h > inner.bottom:
                text = ""

    up, down = _encyclopedia_control_rects(controller)
    button_h = up.height
    for button, label in ((up, "↑"), (down, "↓")):
        pygame.draw.rect(ecra, SIDEBAR_THEME.action_surface, button, border_radius=6)
        pygame.draw.rect(ecra, SIDEBAR_THEME.focus_border, button, 1, border_radius=6)
        txt = small.render(label, True, SIDEBAR_THEME.text_primary)
        ecra.blit(txt, txt.get_rect(center=button.center))


def _hover_target(controller: Any) -> tuple[int, int] | None:
    hover = getattr(controller, "hover_pos", None)
    if hover is not None:
        return hover
    selected = getattr(controller, "casa_selecionada", None)
    return selected


def _draw_section(ecra: Any, rect: Any, title: str) -> None:
    import pygame
    pygame.draw.rect(ecra, SIDEBAR_THEME.surface, rect, border_radius=8)
    pygame.draw.rect(ecra, SIDEBAR_THEME.border, rect, 1, border_radius=8)
    font = pygame.font.SysFont("arial", max(16, min(21, rect.height // 8)), bold=True)
    ecra.blit(font.render(title, True, SIDEBAR_THEME.text_heading), (rect.x + 12, rect.y + 8))


def _draw_sidebar(ecra: Any, controller: Any, *, action_labels: list[str] | None = None, action_title: str = "AÇÕES") -> list[Any]:
    """Draw the three semantic sidebar zones and return clickable action rects."""
    import pygame

    panel_x, panel_w, _ = _panel_geometry(controller)
    panel_top = 14
    panel_h = ecra.get_height() - 28
    gap = 10

    selected_h = max(180, min(330, int(panel_h * 0.36)))
    action_h = 0
    if action_labels:
        action_h = min(max(118, 70 + len(action_labels) * 48), int(panel_h * 0.40))
    context_h = panel_h - selected_h - action_h - (2 if action_h else 1) * gap

    selected_rect = pygame.Rect(panel_x, panel_top, panel_w, selected_h)
    context_rect = pygame.Rect(panel_x, selected_rect.bottom + gap, panel_w, max(120, context_h))
    action_rect = None
    if action_h:
        action_rect = pygame.Rect(panel_x, context_rect.bottom + gap, panel_w, action_h)

    piece = _selected_piece(controller)
    state = _sync_encyclopedia_selection(controller)
    _draw_section(ecra, selected_rect, "HERÓI SELECIONADO")
    body = pygame.font.SysFont("arial", 16)
    small = pygame.font.SysFont("arial", 13)

    if piece is None:
        ecra.blit(body.render("Nenhum herói selecionado", True, SIDEBAR_THEME.text_muted), (selected_rect.x + 12, selected_rect.y + 52))
    else:
        name = body.render(piece.name, True, SIDEBAR_THEME.text_primary)
        ecra.blit(name, (selected_rect.x + 12, selected_rect.y + 48))
        team_label = "Brancas" if piece.team == "brancas" else "Pretas"
        ecra.blit(small.render(team_label, True, SIDEBAR_THEME.text_secondary), (selected_rect.x + 12, selected_rect.y + 72))
        status = []
        if piece.stun_timer > 0:
            status.append(f"Atordoado: {piece.stun_timer}")
        if getattr(piece, "lifespan", None) is not None:
            status.append(f"Duração: {piece.lifespan}")
        if getattr(piece, "spawn_cooldown", 0):
            status.append(f"Cooldown: {piece.spawn_cooldown}")
        if not status:
            status.append("Estado: normal")
        y = selected_rect.y + 96
        for line in status[:2]:
            ecra.blit(small.render(line, True, SIDEBAR_THEME.text_secondary), (selected_rect.x + 12, y))
            y += 20
        if state.open:
            label = "FECHAR ENCICLOPÉDIA"
        else:
            label = "VER REGRAS DO HERÓI"
        button = _encyclopedia_button_rect(controller)
        pygame.draw.rect(ecra, SIDEBAR_THEME.action_surface, button, border_radius=7)
        pygame.draw.rect(ecra, SIDEBAR_THEME.focus_border, button, 1, border_radius=7)
        txt = small.render(label, True, SIDEBAR_THEME.text_primary)
        ecra.blit(txt, txt.get_rect(center=button.center))

    clickable: list[Any] = []
    if state.open and piece is not None:
        _draw_section(ecra, context_rect, "ENCICLOPÉDIA — REGRAS")
        _draw_encyclopedia(ecra, controller, context_rect, body, small)
    else:
        target = _hover_target(controller)
        _draw_section(ecra, context_rect, "CASA EM HOVER")
        if target is None:
            ecra.blit(body.render("Move o cursor sobre o tabuleiro", True, SIDEBAR_THEME.text_muted), (context_rect.x + 12, context_rect.y + 52))
        else:
            r, c = target
            y = context_rect.y + 48
            ecra.blit(body.render(f"Casa: {r + 1},{c + 1}", True, SIDEBAR_THEME.text_primary), (context_rect.x + 12, y))
            y += 24
            target_piece = controller.gs.board[r][c]
            if target_piece is None:
                ecra.blit(small.render("Vazia", True, SIDEBAR_THEME.text_secondary), (context_rect.x + 12, y))
            else:
                team = "Brancas" if target_piece.team == "brancas" else "Pretas"
                ecra.blit(body.render(f"{target_piece.name} · {team}", True, SIDEBAR_THEME.text_secondary), (context_rect.x + 12, y))
                y += 22
                if target_piece.stun_timer > 0:
                    ecra.blit(small.render(f"Atordoado: {target_piece.stun_timer}", True, SIDEBAR_THEME.text_secondary), (context_rect.x + 12, y))
                    y += 19
                if getattr(target_piece, "lifespan", None) is not None:
                    ecra.blit(small.render(f"Duração: {target_piece.lifespan}", True, SIDEBAR_THEME.text_secondary), (context_rect.x + 12, y))
                    y += 19
            effect = controller.gs.tile_effects[r][c] if controller.gs.tile_effects else None
            if effect:
                etype = effect.get("type", "?")
                timer = effect.get("timer")
                label = f"Efeito: {etype}" + (f" · {timer} turnos" if timer is not None else "")
                ecra.blit(small.render(label, True, SIDEBAR_THEME.info), (context_rect.x + 12, y))
                y += 19
            if _selected_piece(controller) is not None and controller.gs.white_to_move:
                sr, sc = controller.casa_selecionada
                actions = actions_for_destination(controller.gs, sr, sc, r, c)
                if actions:
                    ecra.blit(small.render("Ações legais: " + " / ".join(action_label(a) for a in actions), True, SIDEBAR_THEME.text_secondary), (context_rect.x + 12, min(context_rect.bottom - 22, y + 6)))
                else:
                    ecra.blit(small.render("Nenhuma ação legal", True, SIDEBAR_THEME.text_disabled), (context_rect.x + 12, min(context_rect.bottom - 22, y + 6)))

    if action_rect is not None:
        _draw_section(ecra, action_rect, action_title)
        button_h = 40
        by = action_rect.y + 40
        bw = action_rect.width - 24
        for index, label in enumerate(action_labels):
            rect = pygame.Rect(action_rect.x + 12, by, bw, button_h)
            pygame.draw.rect(ecra, SIDEBAR_THEME.action_surface, rect, border_radius=7)
            pygame.draw.rect(ecra, SIDEBAR_THEME.focus_border, rect, 1, border_radius=7)
            txt = body.render(f"{index + 1}. {label}", True, SIDEBAR_THEME.text_primary)
            ecra.blit(txt, txt.get_rect(center=rect.center))
            clickable.append(rect)
            by += button_h + 8
        hint = small.render("ESC cancelar · 1–9 escolher", True, SIDEBAR_THEME.text_muted)
        ecra.blit(hint, (action_rect.x + 12, action_rect.bottom - 22))

    return clickable


def _install_sidebar_render(controller: Any) -> None:
    if getattr(controller, "_intent_sidebar_installed", False):
        return
    original = controller.renderizar

    def wrapped_render(self: Any, *args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        if self.fase_atual == "BATALHA":
            _draw_sidebar(self.ecra, self)
        _sync_interaction_state(self)
        return result

    controller.renderizar = MethodType(wrapped_render, controller)
    controller._intent_sidebar_installed = True


def _prompt(controller: Any, title: str, labels: list[str], *, allow_cancel: bool = True) -> int | None:
    """Choose an action in the lower/right action zone without hiding the board."""
    import pygame

    _install_sidebar_render(controller)
    width, height = controller.ecra.get_size()
    panel_x, panel_w, _ = _panel_geometry(controller)
    action_labels = labels
    controller._interaction_action_count = len(action_labels)
    _sync_interaction_state(controller)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if allow_cancel and event.key == pygame.K_ESCAPE:
                    return None
                if pygame.K_1 <= event.key <= pygame.K_9:
                    index = event.key - pygame.K_1
                    if index < len(action_labels):
                        return index
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                rects = _draw_sidebar(controller.ecra, controller, action_labels=action_labels, action_title=title)
                for index, rect in enumerate(rects):
                    if rect.collidepoint(event.pos):
                        return index

        controller.renderizar(
            w=width,
            h=height,
            off_x=controller.get_ui_metrics()[1],
            off_y_tab=controller.get_ui_metrics()[0],
            tam_casa=controller.get_ui_metrics()[2],
            painel_x=panel_x,
        )
        _draw_sidebar(controller.ecra, controller, action_labels=action_labels, action_title=title)
        pygame.display.flip()
        controller.clock.tick(60)


def _install_instance_wrapper(controller: Any) -> None:
    original = controller.tratar_cliques
    _install_sidebar_render(controller)
    _sync_interaction_state(controller)
    controller._hero_encyclopedia_state = HeroEncyclopediaPanelState()

    def wrapped(self: Any, mx: int, my: int, pos: tuple[int, int]) -> Any:
        if self.fase_atual == "BATALHA":
            _sync_encyclopedia_selection(self)
            if _selected_piece(self) is not None:
                button = _encyclopedia_button_rect(self)
                if button.collidepoint(pos):
                    self._hero_encyclopedia_state = toggle_panel(self._hero_encyclopedia_state)
                    return None
                if self._hero_encyclopedia_state.open:
                    context_rect = _sidebar_context_rect(self)
                    up, down = _encyclopedia_control_rects(self)
                    context = selected_hero_context(self._hero_encyclopedia_state.hero_name)
                    lines = encyclopedia_lines(context)
                    inner_height = max(1, context_rect.height - 82)
                    line_h = 18
                    visible = max(1, inner_height // line_h)
                    if up.collidepoint(pos):
                        self._hero_encyclopedia_state = scroll_panel(
                            self._hero_encyclopedia_state, -max(1, visible - 1),
                            line_count=len(lines), visible_lines=visible,
                        )
                        return None
                    if down.collidepoint(pos):
                        self._hero_encyclopedia_state = scroll_panel(
                            self._hero_encyclopedia_state, max(1, visible - 1),
                            line_count=len(lines), visible_lines=visible,
                        )
                        return None

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
                _clear_pending_interaction(self)
                _sync_interaction_state(self)
            return None

        sr, sc = self.casa_selecionada
        if (sr, sc) == (r, c):
            self.casa_selecionada = None
            _clear_pending_interaction(self)
            return None

        actions = actions_for_destination(self.gs, sr, sc, r, c)
        if not actions:
            clicked_piece = self.gs.board[r][c]
            if clicked_piece is not None and clicked_piece.team == "brancas":
                self.casa_selecionada = (r, c)
                _clear_pending_interaction(self)
                _sync_interaction_state(self)
            return None

        self._interaction_destination = (r, c)
        self._interaction_action_count = len(actions)
        _sync_interaction_state(self)

        if len(actions) == 1:
            chosen = actions[0]
        else:
            labels = [action_label(action) for action in actions]
            index = _prompt(self, "ESCOLHER AÇÃO", labels)
            if index is None:
                _clear_pending_interaction(self)
                return None
            chosen = actions[index]

        if needs_offensive_target_confirmation(self.gs, chosen):
            self._interaction_confirmation_required = True
            _sync_interaction_state(self)
            index = _prompt(self, "CONFIRMAR PODER", [f"Confirmar {action_label(chosen)}", "Cancelar"])
            self._interaction_confirmation_required = False
            if index != 0:
                _clear_pending_interaction(self)
                return None

        if self.modo_predador and self.pondering_active and self.bot_ativo is not None and hasattr(self.bot_ativo, "stop_pondering"):
            self.bot_ativo.stop_pondering()
            self.pondering_active = False

        _, off_x, tam_casa = self.get_ui_metrics()
        self.desenhar_animacao(self.gs, chosen["start"], chosen["end"], chosen["type"], tam_casa, off_x, 80)
        self.gs.execute_action(normalize_action(chosen))
        self.casa_selecionada = None
        _clear_pending_interaction(self)
        return None

    controller.tratar_cliques = MethodType(wrapped, controller)


def install_intent_interaction(controller: Any) -> None:
    """Install manual interaction plus the persistent battle sidebar."""
    _install_instance_wrapper(controller)
