# multiplayer_main.py
from __future__ import annotations

import sys
import types
import pygame

from engine.config import COLUNAS, LINHAS
from online.network.client import NetworkClient
from ui.renderer import COLORS, desenhar_tabuleiro

C_FUNDO = COLORS["bg"]


def formatar_segundos(s: float) -> str:
    m = int(max(0, s)) // 60
    sec = int(max(0, s)) % 60
    return f"{m:02d}:{sec:02d}"


def desenhar_relogios_rede(ecra, clock_data, w, h):
    if not clock_data:
        return
    fonte = pygame.font.Font(None, 34)

    # Relógio das Pretas (Topo)
    tempo_p = formatar_segundos(clock_data.get("black_time", 0))
    ativo_p = not clock_data.get("white_to_move", True)
    cor_borda_p = (100, 255, 100) if ativo_p else (80, 80, 80)
    surf_p = fonte.render(f"Pretas: {tempo_p}", True, (240, 240, 240))
    rect_p = surf_p.get_rect(topright=(w - 40, 24))
    pygame.draw.rect(ecra, (24, 24, 24), rect_p.inflate(16, 8), border_radius=6)
    pygame.draw.rect(ecra, cor_borda_p, rect_p.inflate(16, 8), width=2, border_radius=6)
    ecra.blit(surf_p, rect_p)

    # Relógio das Brancas (Fundo)
    tempo_b = formatar_segundos(clock_data.get("white_time", 0))
    ativo_b = bool(clock_data.get("white_to_move", True))
    cor_borda_b = (100, 255, 100) if ativo_b else (80, 80, 80)
    surf_b = fonte.render(f"Brancas: {tempo_b}", True, (240, 240, 240))
    rect_b = surf_b.get_rect(bottomright=(w - 40, h - 24))
    pygame.draw.rect(ecra, (24, 24, 24), rect_b.inflate(16, 8), border_radius=6)
    pygame.draw.rect(ecra, cor_borda_b, rect_b.inflate(16, 8), width=2, border_radius=6)
    ecra.blit(surf_b, rect_b)


def desenhar_pecas_rede(ecra, board_data, tam_casa, off_x, off_y):
    if not board_data:
        return
    fonte = pygame.font.Font(None, int(tam_casa * 0.4))

    rows = len(board_data)
    cols = len(board_data[0]) if rows > 0 else 0

    for r in range(rows):
        for c in range(cols):
            p_data = board_data[r][c]
            if p_data:
                cx, cy = off_x + c * tam_casa + tam_casa // 2, off_y + r * tam_casa + tam_casa // 2
                cor_peca = (220, 220, 220) if p_data["team"] == "brancas" else (40, 40, 40)
                pygame.draw.circle(ecra, cor_peca, (cx, cy), int(tam_casa * 0.4))

                cor_texto = (0, 0, 0) if p_data["team"] == "brancas" else (255, 255, 255)
                sigla = p_data["name"][:2].capitalize() if p_data["name"] != "BoneLord" else "BL"
                texto = fonte.render(sigla, True, cor_texto)

                rect_texto = texto.get_rect(center=(cx, cy))
                ecra.blit(texto, rect_texto)

                if p_data.get("stun_timer", 0) > 0:
                    pygame.draw.circle(ecra, (0, 200, 255), (cx, cy), int(tam_casa * 0.45), 3)


def main():
    pygame.init()
    ecra = pygame.display.set_mode((900, 800), pygame.RESIZABLE)

    ip_servidor = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    room_id = sys.argv[2] if len(sys.argv) > 2 else None

    pygame.display.set_caption(f"RedWar - A ligar a {ip_servidor}...")
    clock = pygame.time.Clock()

    cliente = NetworkClient(host=ip_servidor, port=8765, room_id=room_id)
    casa_selecionada = None

    correr = True
    while correr:
        estado_rede = cliente.latest_state
        relogio_rede = cliente.latest_clock

        if cliente.cor_atribuida:
            turno = "O TEU TURNO" if (estado_rede and (
                (estado_rede["white_to_move"] and cliente.cor_atribuida == "brancas") or
                (not estado_rede["white_to_move"] and cliente.cor_atribuida == "pretas")
            )) else "A AGUARDAR ADVERSÁRIO"
            sala_str = f" | Sala: {room_id}" if room_id else ""
            pygame.display.set_caption(f"RedWar Multiplayer | {cliente.cor_atribuida.upper()}{sala_str} | {turno}")

        w, h = ecra.get_size()
        rows = len(estado_rede["board"]) if estado_rede and "board" in estado_rede else LINHAS
        cols = len(estado_rede["board"][0]) if estado_rede and "board" in estado_rede and len(estado_rede["board"]) > 0 else COLUNAS

        tam_casa = min(w // cols, h // rows) - 10
        off_x = (w - (cols * tam_casa)) // 2
        off_y = (h - (rows * tam_casa)) // 2

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                correr = False
            elif evento.type == pygame.VIDEORESIZE:
                ecra = pygame.display.set_mode((evento.w, evento.h), pygame.RESIZABLE)

            elif evento.type == pygame.MOUSEBUTTONDOWN and estado_rede and not estado_rede["game_over"]:
                if evento.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    if off_y <= my < off_y + rows * tam_casa and off_x <= mx < off_x + cols * tam_casa:
                        c = (mx - off_x) // tam_casa
                        r = (my - off_y) // tam_casa

                        if not casa_selecionada:
                            peca_clicada = estado_rede["board"][r][c]
                            if peca_clicada and peca_clicada["team"] == cliente.cor_atribuida:
                                casa_selecionada = (r, c)
                        else:
                            cliente.enviar_acao(
                                start=casa_selecionada,
                                end=(r, c),
                                action_type="move",
                            )
                            casa_selecionada = None

        ecra.fill(C_FUNDO)
        dummy_gs = types.SimpleNamespace(last_move=None, tile_effects=None)
        desenhar_tabuleiro(ecra, dummy_gs, tam_casa, off_x, off_y)

        if casa_selecionada:
            r, c = casa_selecionada
            pygame.draw.rect(ecra, (150, 150, 50), (off_x + c * tam_casa, off_y + r * tam_casa, tam_casa, tam_casa), 4)

        if estado_rede:
            desenhar_pecas_rede(ecra, estado_rede["board"], tam_casa, off_x, off_y)
            desenhar_relogios_rede(ecra, relogio_rede, w, h)
        else:
            fonte = pygame.font.Font(None, 48)
            txt = fonte.render("A conectar ao Servidor...", True, (255, 255, 255))
            ecra.blit(txt, (w // 2 - txt.get_width() // 2, h // 2))

        pygame.display.flip()
        clock.tick(60)

    cliente.fechar()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
