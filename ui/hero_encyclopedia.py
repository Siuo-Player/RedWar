from __future__ import annotations

import pygame

from ui.hero_encyclopedia_model import hero_encyclopedia_context
from ui.renderer import AssetManager, COLORS, FontManager, draw_text_wrapped, desenhar_botao


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
        context = hero_encyclopedia_context(name)
        avatar = AssetManager.get_image(name, "brancas", 96)
        if avatar:
            avatar_rect = avatar.get_rect(topright=(right.right - 18, right.y + 18))
            ecra.blit(avatar, avatar_rect)
        headline = FontManager.get("arial", 30, bold=True)
        ecra.blit(headline.render(context.name, True, COLORS["white_team"]), (right.x + 20, right.y + 18))
        ecra.blit(meta_font.render(f"Custo de draft: {context.cost} pontos", True, COLORS["text"]), (right.x + 22, right.y + 53))

        y = right.y + 88
        label = FontManager.get("arial", 17, bold=True)
        body = FontManager.get("arial", 15)
        blocks = [
            ("Movimento", context.movement, COLORS["text"]),
            ("Ataque básico", context.attack, COLORS["text"]),
            ("Descrição", context.description, COLORS["text"]),
            ("Passiva", context.passive, (150, 255, 170)),
        ]
        for heading, text, color in blocks:
            ecra.blit(label.render(heading + ":", True, (190, 200, 220)), (right.x + 20, y))
            y += 20
            y = draw_text_wrapped(ecra, text, body, color, right.x + 20, y, right.width - 40)
            y += 5

        if context.spells:
            ecra.blit(label.render("Spells:", True, (190, 200, 220)), (right.x + 20, y))
            y += 20
            for spell in context.spells:
                detail = SPELL_DETAILS.get(spell, "Detalhe especializado não documentado.")
                y = draw_text_wrapped(ecra, f"• {spell.upper()}: {detail}", body, (210, 180, 255), right.x + 20, y, right.width - 40)
                y += 2

        if context.special_rules:
            ecra.blit(label.render("Regras especiais / limites:", True, (190, 200, 220)), (right.x + 20, y))
            y += 20
            for line in context.special_rules:
                y = draw_text_wrapped(ecra, "• " + line, body, COLORS["warning"], right.x + 20, y, right.width - 40)
                y += 2

    btn_voltar = pygame.Rect(w - 150, h - 58, 120, 40)
    desenhar_botao(ecra, btn_voltar, "Voltar", COLORS["btn_danger"], font_size=22)
    return btn_voltar, rects
