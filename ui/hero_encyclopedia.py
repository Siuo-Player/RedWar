from __future__ import annotations

from typing import Any

import pygame

from engine.pieces import HERO_DEFS
from ui.renderer import AssetManager, COLORS, FontManager, draw_text_wrapped, desenhar_botao


def _movement_text(data: dict[str, Any]) -> str:
    movement = data.get("behavior", {}).get("movement", {}) or {}
    kind = movement.get("type", "none")
    if kind == "none":
        return "Nenhum"
    if kind == "orthogonal":
        return f"Ortogonal — até {movement.get('max_steps', 1)} casa(s)"
    if kind == "diagonal":
        return f"Diagonal — até {movement.get('max_steps', 1)} casa(s)"
    if kind == "adjacent":
        return "Uma casa em qualquer direção"
    if kind == "knight":
        return "Em L (padrão de cavalo)"
    if kind == "forward_cone":
        return "Cone frontal: " + str(movement.get("deltas", []))
    if kind == "ray":
        return f"Raio — mínimo {movement.get('min_steps', 1)} casa(s), sem bloqueio especial declarado"
    return f"Padrão: {kind}"


def _attack_text(data: dict[str, Any]) -> str:
    attack = data.get("behavior", {}).get("attack", {}) or {}
    kind = attack.get("type", "none")
    if kind == "none":
        return "Nenhum ataque básico"
    if attack.get("attack_action") == "spell":
        return f"SPELL: {attack.get('spell_name', 'desconhecida')}"
    if kind == "orthogonal":
        return f"Ortogonal — até {attack.get('max_steps', 1)} casa(s)"
    if kind == "diagonal":
        return f"Diagonal — até {attack.get('max_steps', 1)} casa(s)"
    if kind == "adjacent":
        return "Uma casa em qualquer direção"
    if kind == "knight":
        return "Em L (padrão de cavalo)"
    if kind == "ray":
        minimum = attack.get("min_steps", 1)
        return f"Raio — mínimo {minimum} casa(s), máximo o tabuleiro"
    if kind == "pattern":
        return f"Padrão: {attack.get('deltas', [])}"
    return f"Padrão: {kind}"


SPELL_DETAILS = {
    "nevada": "Centro até distância Manhattan 3. Afeta uma cruz (centro + 4 ortogonais): inimigos normais ficam atordoados por 2; inimigos já atordoados morrem. O centro recebe gelo durante 3 turnos.",
    "aimed_shot": "Ataque especial em raio; o alvo tem de estar a pelo menos 2 casas. Executa-se como SPELL, não como ATTACK básico.",
    "sentinel_shot": "Ataque especial em raio. Executa-se como SPELL, não como ATTACK básico.",
    "spectral_strike": "Ataque especial em L através de peças, classificado como SPELL.",
    "bone_v": "Ataque especial no padrão em V. Ao eliminar o alvo, cria um Bone na casa do alvo.",
    "ignite": "Escolhe uma casa até 3 linhas/colunas de distância; cria fogo numa cruz durante 3 turnos e pode aplicar stun.",
    "purify": "Remove o stun de um aliado dentro do alcance da habilidade.",
    "swap": "Troca de posição com outro aliado elegível dentro do alcance da spell.",
    "barricade": "Cria uma StoneWall numa casa adjacente livre.",
    "jump": "Salto até 2 casas em qualquer direção, respeitando as condições de salto/casa de destino.",
    "spawn_ghoul": "Invoca 1 Ghoul numa das três casas à frente, se estiver livre. A invocação aplica cooldown ao Lich.",
}


def _special_lines(name: str, data: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    behavior = data.get("behavior", {}) or {}
    if data.get("aura_radius") is not None:
        lines.append(f"Aura: raio {data['aura_radius']} — impede spells inimigas ao alcance.")
    if data.get("jump_max") is not None:
        lines.append(f"Salto máximo configurado: {data['jump_max']} casas.")
    if data.get("lifespan") is not None:
        lines.append(f"Unidade temporária: dura {data['lifespan']} turnos.")
    if data.get("spawn_cooldown"):
        lines.append(f"Cooldown inicial de invocação: {data['spawn_cooldown']} turnos.")
    if name == "Lich":
        lines.append("Quando a invocação é usada, o cooldown passa para 4 turnos; o spawn ocupa a única ação do turno.")
    if name == "FrostMage":
        lines.append("Não tem ataque básico. Nevada é a ação ofensiva especial e pode ser lançada uma vez por turno, desde que o mago possa agir e não esteja silenciado.")
        lines.append("Não existe limite de usos global nem cooldown configurado para Nevada.")
    if name == "Pyromancer":
        lines.append("Não tem ataque básico. Ignite não possui contagem de usos/cooldown configurada.")
    if name in {"Cleric", "Trickster", "Geomancer", "Dragoon"}:
        lines.append("A spell ocupa a ação do turno; não existe uma contagem global de usos na configuração atual.")
    if behavior.get("passives"):
        for passive in behavior["passives"]:
            lines.append(f"Passiva técnica: trigger={passive.get('trigger')}, efeito={passive.get('effect')}.")
    return lines


def desenhar_enciclopedia_detalhada(
    ecra: pygame.Surface,
    w: int,
    h: int,
    catalogo: list,
    selected_index: int = 0,
) -> tuple[pygame.Rect, list[tuple[pygame.Rect, int]]]:
    ecra.fill(COLORS["bg"])
    title_font = FontManager.get("arial", 42, bold=True)
    ecra.blit(title_font.render("Enciclopédia de Heróis", True, COLORS["text"]), (30, 24))
    subtitle = FontManager.get("arial", 16)
    ecra.blit(subtitle.render("Consulta as regras atualmente implementadas — custos, movimento, ataques, spells e passivas.", True, COLORS["text_muted"]), (32, 69))

    left = pygame.Rect(25, 100, min(335, int(w * 0.31)), h - 175)
    right = pygame.Rect(left.right + 18, 100, w - left.right - 43, h - 175)
    pygame.draw.rect(ecra, (22, 22, 30), left, border_radius=10)
    pygame.draw.rect(ecra, (22, 22, 30), right, border_radius=10)
    pygame.draw.rect(ecra, (80, 80, 100), left, 2, border_radius=10)
    pygame.draw.rect(ecra, (80, 80, 100), right, 2, border_radius=10)

    item_font = FontManager.get("arial", 17, bold=True)
    meta_font = FontManager.get("arial", 14)
    rects: list[tuple[pygame.Rect, int]] = []
    row_h = max(27, min(34, (left.height - 18) // max(1, len(catalogo))))
    for i, item in enumerate(catalogo):
        rect = pygame.Rect(left.x + 10, left.y + 9 + i * row_h, left.width - 20, row_h - 3)
        rects.append((rect, i))
        selected = i == selected_index
        pygame.draw.rect(ecra, (65, 85, 115) if selected else (40, 40, 52), rect, border_radius=5)
        ecra.blit(item_font.render(item["name"], True, COLORS["text"]), (rect.x + 8, rect.y + 3))
        ecra.blit(meta_font.render(f"{item['cost']} pts", True, COLORS["text_muted"]), (rect.right - 65, rect.y + 5))

    if catalogo:
        item = catalogo[selected_index]
        name = item["name"]
        data = HERO_DEFS[name]
        avatar = AssetManager.get_image(name, "brancas", 96)
        if avatar:
            avatar_rect = avatar.get_rect(topright=(right.right - 18, right.y + 18))
            ecra.blit(avatar, avatar_rect)
        headline = FontManager.get("arial", 30, bold=True)
        ecra.blit(headline.render(name, True, COLORS["white_team"]), (right.x + 20, right.y + 18))
        ecra.blit(meta_font.render(f"Custo de draft: {data.get('cost', 0)} pontos", True, COLORS["text"]), (right.x + 22, right.y + 53))

        y = right.y + 88
        label = FontManager.get("arial", 17, bold=True)
        body = FontManager.get("arial", 15)
        blocks = [
            ("Movimento", _movement_text(data), COLORS["text"]),
            ("Ataque básico", _attack_text(data), COLORS["text"]),
            ("Descrição", data.get("descricao", "Sem descrição."), COLORS["text"]),
            ("Passiva", data.get("passiva", "Nenhuma."), (150, 255, 170)),
        ]
        for heading, text, color in blocks:
            ecra.blit(label.render(heading + ":", True, (190, 200, 220)), (right.x + 20, y))
            y += 20
            y = draw_text_wrapped(ecra, text, body, color, right.x + 20, y, right.width - 40)
            y += 5

        spells = data.get("spells", []) or []
        if spells:
            ecra.blit(label.render("Spells:", True, (190, 200, 220)), (right.x + 20, y))
            y += 20
            for spell in spells:
                detail = SPELL_DETAILS.get(spell, "Detalhe especializado não documentado.")
                y = draw_text_wrapped(ecra, f"• {spell.upper()}: {detail}", body, (210, 180, 255), right.x + 20, y, right.width - 40)
                y += 2

        special = _special_lines(name, data)
        if special:
            ecra.blit(label.render("Regras especiais / limites:", True, (190, 200, 220)), (right.x + 20, y))
            y += 20
            for line in special:
                y = draw_text_wrapped(ecra, "• " + line, body, COLORS["warning"], right.x + 20, y, right.width - 40)
                y += 2

    btn_voltar = pygame.Rect(w - 150, h - 58, 120, 40)
    desenhar_botao(ecra, btn_voltar, "Voltar", COLORS["btn_danger"], font_size=22)
    return btn_voltar, rects
