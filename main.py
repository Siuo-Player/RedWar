# main.py
import pygame
import time
import random
import threading
from engine.game_state import GameState, coords_para_notacao
from engine.pieces import obter_catalogo_pecas
from engine.config import ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS, LINHAS, COLUNAS

from ui.renderer import (
    desenhar_menu_principal, desenhar_selecao_dificuldade, 
    desenhar_tabuleiro, desenhar_pecas, 
    desenhar_loja_dinamica, desenhar_enciclopedia, desenhar_log, desenhar_analise,
    desenhar_coordenadas, desenhar_painel_heroi, desenhar_destaques_com_hover,
    C_FUNDO, C_VERMELHO, C_BRANCO, C_PRETO, C_AZUL, carregar_imagem_peca,
    desenhar_hud_jogadores, desenhar_eval_bar
)

from ai.bot import gerar_bot_por_elo
from ai.search import find_best_move
from ai.evaluator import avaliador_mestre

def auto_draft_ia(gs, orcamento):
    pontos = orcamento
    cat = obter_catalogo_pecas()
    for r in range(2):
        for c in range(COLUNAS):
            validas = [p for p in cat if p["cost"] <= pontos]
            if not validas: break
            esc = random.choice(validas)
            gs.board[r][c] = esc["class"]('pretas')
            pontos -= esc["cost"]

def animar_acao(ecra, gs, start_pos, end_pos, action_type, tam_casa, off_x, off_y, clock):
    sr, sc = start_pos
    er, ec = end_pos
    piece = gs.board[sr][sc]
    sx, sy = off_x + sc * tam_casa + tam_casa // 2, off_y + sr * tam_casa + tam_casa // 2
    ex, ey = off_x + ec * tam_casa + tam_casa // 2, off_y + er * tam_casa + tam_casa // 2
    
    if action_type in ["move", "attack"]: gs.board[sr][sc] = None
    for i in range(16):
        t = i / 15
        cx, cy = sx + (ex - sx) * t, sy + (ey - sy) * t
        ecra.fill(C_FUNDO)
        
        desenhar_tabuleiro(ecra, gs, tam_casa, off_x, off_y)
        desenhar_coordenadas(ecra, tam_casa, off_x, off_y)
        desenhar_pecas(ecra, gs.board, tam_casa, off_x, off_y)
        desenhar_log(ecra, gs, off_x + COLUNAS*tam_casa + 30, 20, 350, ecra.get_height() - 40)
        
        if action_type in ["move", "attack"]:
            img = carregar_imagem_peca(piece.name, piece.team, tam_casa)
            if img: ecra.blit(img, img.get_rect(center=(cx, cy)))
            else: pygame.draw.circle(ecra, (200,200,200), (cx, cy), int(tam_casa * 0.38))
        elif action_type == "stun": pygame.draw.circle(ecra, (0, 200, 255), (int(cx), int(cy)), 12)
        elif action_type == "spawn": pygame.draw.circle(ecra, (200, 100, 255), (int(cx), int(cy)), 12) 
        pygame.display.flip()
        clock.tick(60)
    if action_type in ["move", "attack"]: gs.board[sr][sc] = piece

resultados_analise = {}

def analisar_historico_thread(move_log):
    for id_jogada, log in enumerate(move_log):
        estado_congelado = log["estado_anterior"]
        melhor_jogada = find_best_move(estado_congelado, evaluator_func=avaliador_mestre, time_limit=1.0)
        if not melhor_jogada: continue
        
        s_alg = coords_para_notacao(*melhor_jogada["start"])
        e_alg = coords_para_notacao(*melhor_jogada["end"])
        str_jogada = f"{s_alg}-{e_alg}"
        
        gs_temp = estado_congelado.fast_clone()
        gs_temp.make_action(melhor_jogada["start"], melhor_jogada["end"], melhor_jogada["type"])
        score = avaliador_mestre(gs_temp)
        
        forced_mate = None
        if score > 90000 or score < -90000:
            forced_mate = "1" 
            
        resultados_analise[id_jogada] = {
            "best_move_str": str_jogada,
            "score": round(score, 1),
            "forced_mate": forced_mate
        }

def main():
    pygame.init()
    ecra = pygame.display.set_mode((1300, 800), pygame.RESIZABLE)
    pygame.display.set_caption("RedWar - Combat Engine")
    clock = pygame.time.Clock()
    
    fase_atual = "MENU" 
    gs = GameState(time_limit_seconds=180)
    pontos_jogador = ORCAMENTO_BRANCAS
    peca_loja = casa_selecionada = hover_pos = None
    catalogo = obter_catalogo_pecas()
    
    elo_escolhido = 1500
    bot_ativo = gerar_bot_por_elo(elo_escolhido)
    
    # === VARIÁVEIS MULTITHREADING ===
    thread_analise = None
    thread_ia = None 
    resultado_ia = []
    review_index = 0
    display_gs = None

    def pensar_ia(bot, estado):
        move = bot.play(estado)
        resultado_ia.append(move)
    
    arrastando_elo = False
    botoes_loja = {}
    btn_voltar = btn_ready = pygame.Rect(0,0,0,0)
    btn_start = btn_info = pygame.Rect(0,0,0,0)
    btn_confirmar = rect_elo = pygame.Rect(0,0,0,0)
    btn_prev = btn_next = pygame.Rect(0,0,0,0)
    
    correr = True
    while correr:
        w, h = ecra.get_size()
        # Anchor the board with fixed offsets (prevents HUD overlap)
        off_y_tab = 80
        off_x = 60
        # Compute tile size fitting the anchored area
        available_h = h - off_y_tab - 120
        tam_casa = min(w // (COLUNAS + 1), max(8, available_h // LINHAS))
        painel_x = off_x + COLUNAS * tam_casa + 30

        # === CAPTURA DE HOVER CONTÍNUA ===
        mx, my = pygame.mouse.get_pos()
        hover_pos = None
        if off_y_tab <= my < off_y_tab + LINHAS*tam_casa and off_x <= mx < off_x + COLUNAS*tam_casa:
            hover_pos = ((my - off_y_tab) // tam_casa, (mx - off_x) // tam_casa)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: correr = False
            elif evento.type == pygame.VIDEORESIZE: ecra = pygame.display.set_mode((evento.w, evento.h), pygame.RESIZABLE)
            elif evento.type == pygame.MOUSEBUTTONUP:
                arrastando_elo = False
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    if fase_atual == "MENU":
                        if btn_start.collidepoint(mx, my): fase_atual = "DIFICULDADE"
                        elif btn_info.collidepoint(mx, my): fase_atual = "INFO"
                    
                    elif fase_atual == "DIFICULDADE":
                        if rect_elo.collidepoint(mx, my): arrastando_elo = True
                        elif btn_confirmar.collidepoint(mx, my):
                            bot_ativo = gerar_bot_por_elo(elo_escolhido)
                            fase_atual = "DRAFT"
                            pygame.display.set_caption(f"RedWar - A Jogar contra: {bot_ativo.nome}")
                            # recompute evaluator cache on new game start
                            gs.current_score = None
                    
                    elif fase_atual == "INFO":
                        if btn_voltar.collidepoint(mx, my): fase_atual = "MENU"
                        
                    elif fase_atual == "DRAFT":
                        if my >= off_y_tab + (LINHAS * tam_casa) + 20:
                            for nome, rect in botoes_loja.items():
                                if rect.collidepoint(mx, my): peca_loja = nome
                            if btn_ready.collidepoint(mx, my):
                                auto_draft_ia(gs, ORCAMENTO_PRETAS)
                                fase_atual = "BATALHA"
                    elif fase_atual == "ANALISE":
                        # Prev/Next review controls (set in render, handled here on clicks)
                        if btn_prev and btn_prev.collidepoint(evento.pos):
                            review_index = max(0, review_index - 1)
                            if 0 <= review_index < len(gs.move_log):
                                display_gs = gs.move_log[review_index]["estado_anterior"].fast_clone()
                            else:
                                display_gs = None
                        if btn_next and btn_next.collidepoint(evento.pos):
                            review_index = min(len(gs.move_log) - 1, review_index + 1) if gs.move_log else 0
                            if 0 <= review_index < len(gs.move_log):
                                display_gs = gs.move_log[review_index]["estado_anterior"].fast_clone()
                            else:
                                display_gs = None
                        elif peca_loja and hover_pos:
                            r, c = hover_pos
                            # Permite colocar apenas nas últimas duas linhas do teu lado do tabuleiro
                            if 0 <= c < COLUNAS and r >= LINHAS - 2 and gs.board[r][c] is None:
                                p_data = next((p for p in catalogo if p["name"] == peca_loja), None)
                                if p_data and p_data["cost"] <= pontos_jogador:
                                    gs.board[r][c] = p_data["class"]('brancas')
                                    pontos_jogador -= p_data["cost"]
                                    peca_loja = None

                    elif fase_atual == "BATALHA" and gs.white_to_move and not gs.game_over:
                        if hover_pos:
                            r, c = hover_pos
                            if not casa_selecionada:
                                if gs.board[r][c] and gs.board[r][c].team == 'brancas': 
                                    casa_selecionada = (r, c)
                            else:
                                sr, sc = casa_selecionada
                                p = gs.board[sr][sc]
                                if p:
                                    if (r, c) in p.get_valid_moves(sr, sc, gs.board, gs.tile_effects):
                                        animar_acao(ecra, gs, (sr, sc), (r, c), "move", tam_casa, off_x, off_y_tab, clock)
                                        gs.make_action((sr, sc), (r, c), "move")
                                    elif (r, c) in p.get_valid_attacks(sr, sc, gs.board, gs.tile_effects):
                                        animar_acao(ecra, gs, (sr, sc), (r, c), "attack", tam_casa, off_x, off_y_tab, clock)
                                        gs.make_action((sr, sc), (r, c), "attack")
                                    else:
                                        stuns = p.get_valid_stuns(sr, sc, gs.board, gs.tile_effects)
                                        if (r, c) in stuns and stuns[(r, c)]["has_enemy"]:
                                            animar_acao(ecra, gs, (sr, sc), (r, c), "stun", tam_casa, off_x, off_y_tab, clock)
                                            gs.make_action((sr, sc), (r, c), "stun", affected_area=stuns[(r, c)]["aoe"])
                                        else:
                                            for sp in p.get_valid_spawns(sr, sc, gs.board, gs.tile_effects):
                                                if (r, c) == (sp[0], sp[1]):
                                                    animar_acao(ecra, gs, (sr, sc), (r, c), "spawn", tam_casa, off_x, off_y_tab, clock)
                                                    gs.make_action((sr, sc), (r, c), "spawn", spawn_name=sp[2])
                                                    break
                                casa_selecionada = None

            elif evento.type == pygame.MOUSEMOTION:
                if arrastando_elo:
                    perc = max(0.0, min(1.0, (mx - (w//2 - 200)) / 400.0))
                    elo_escolhido = int(100 + perc * 2500)

        # === GESTÃO ASSÍNCRONA DA IA (Sem Bloquear Ecrã) ===
        if fase_atual == "BATALHA" and not gs.white_to_move and not gs.game_over:
            if thread_ia is None:
                thread_ia = threading.Thread(target=pensar_ia, args=(bot_ativo, gs.fast_clone()))
                thread_ia.daemon = True
                thread_ia.start()
                pygame.display.set_caption(f"RedWar - {bot_ativo.nome} a esmagar a árvore tática...")
            elif not thread_ia.is_alive():
                best_move = resultado_ia.pop() if resultado_ia else None
                if best_move:
                    animar_acao(ecra, gs, best_move["start"], best_move["end"], best_move["type"], tam_casa, off_x, off_y_tab, clock)
                    gs.make_action(best_move["start"], best_move["end"], best_move["type"], best_move.get("area"), best_move.get("spawn_name"))
                pygame.display.set_caption(f"RedWar - O Teu Turno")
                thread_ia = None

        if fase_atual == "BATALHA" and gs.game_over and not thread_analise:
            fase_atual = "ANALISE"
            thread_analise = threading.Thread(target=analisar_historico_thread, args=(gs.move_log,))
            thread_analise.daemon = True
            thread_analise.start()

        # === RENDERIZAÇÃO ===
        if fase_atual == "MENU":
            btn_start, btn_info = desenhar_menu_principal(ecra, w, h)
        elif fase_atual == "DIFICULDADE":
            rect_elo, btn_confirmar = desenhar_selecao_dificuldade(ecra, w, h, elo_escolhido)
        elif fase_atual == "INFO":
            btn_voltar = desenhar_enciclopedia(ecra, w, h, catalogo)
        else:
            ecra.fill(C_FUNDO)
            
            # HUD e Eval Bar (use cached score; do not call evaluator per-frame)
            try:
                desenhar_eval_bar(ecra, gs, off_x - 30, LINHAS * tam_casa, off_y_tab)
            except Exception:
                pass
            desenhar_hud_jogadores(ecra, off_x, 20, off_y_tab + LINHAS * tam_casa + 20, tam_casa, bot_ativo.nome, gs)

            # Tabuleiro base
            # Em modo ANÁLISE usamos a posição do índice de revisão se existir
            to_draw_gs = display_gs if (fase_atual == "ANALISE" and display_gs is not None) else gs
            desenhar_tabuleiro(ecra, to_draw_gs, tam_casa, off_x, off_y_tab)
            desenhar_coordenadas(ecra, tam_casa, off_x, off_y_tab)
            
            # Painel Lateral Dinâmico (Log de Batalha vs Info do Herói)
            if fase_atual == "ANALISE":
                # desenha painel de análise e controles Prev/Next
                desenhar_analise(ecra, painel_x, 20, 350, h - 40, gs.move_log, resultados_analise)
                # controls
                btn_prev = pygame.Rect(painel_x + 20, h - 80, 80, 40)
                btn_next = pygame.Rect(painel_x + 120, h - 80, 80, 40)
                pygame.draw.rect(ecra, (80,80,80), btn_prev, border_radius=6)
                pygame.draw.rect(ecra, (80,80,80), btn_next, border_radius=6)
                fbtn = pygame.font.SysFont("arial", 20, bold=True)
                ecra.blit(fbtn.render("Anterior", True, C_BRANCO), (btn_prev.x + 6, btn_prev.y + 8))
                ecra.blit(fbtn.render("Próximo", True, C_BRANCO), (btn_next.x + 6, btn_next.y + 8))
                # set display_gs from current review_index
                if 0 <= review_index < len(gs.move_log):
                    display_gs = gs.move_log[review_index]["estado_anterior"].fast_clone()
                else:
                    display_gs = None
            else:
                if hover_pos and gs.board[hover_pos[0]][hover_pos[1]]:
                    desenhar_painel_heroi(ecra, gs.board[hover_pos[0]][hover_pos[1]], painel_x, 20, 350, h - 40)
                else:
                    desenhar_log(ecra, gs, painel_x, 20, 350, h - 40)
            
            # Destaques e Previsão de Movimento (Hover Intent)
            if casa_selecionada and fase_atual == "BATALHA":
                desenhar_destaques_com_hover(ecra, gs, casa_selecionada, hover_pos, tam_casa, off_x, off_y_tab)
                r, c = casa_selecionada
                pygame.draw.rect(ecra, (255, 255, 50), (off_x + c * tam_casa, off_y_tab + r * tam_casa, tam_casa, tam_casa), 3)

            # Desenha as Peças por cima de tudo
            desenhar_pecas(ecra, gs.board, tam_casa, off_x, off_y_tab)
            
            if fase_atual == "DRAFT":
                botoes_loja, btn_ready, _ = desenhar_loja_dinamica(ecra, w, h, catalogo, pontos_jogador, peca_loja, off_y_tab + (LINHAS * tam_casa) + 20)
            
            elif gs.game_over:
                fonte_fim = pygame.font.SysFont("arial", 48, bold=True)
                txt = fonte_fim.render(f"FIM: {gs.winner}", True, C_VERMELHO)
                s_fim = pygame.Surface((txt.get_width() + 40, txt.get_height() + 20), pygame.SRCALPHA)
                s_fim.fill((0, 0, 0, 200))
                centro_x = off_x + (COLUNAS * tam_casa) // 2
                centro_y = off_y_tab + (LINHAS * tam_casa) // 2
                ecra.blit(s_fim, (centro_x - s_fim.get_width()//2, centro_y - s_fim.get_height()//2))
                ecra.blit(txt, (centro_x - txt.get_width()//2, centro_y - txt.get_height()//2))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()