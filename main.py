import pygame
import threading
import random
import os
import json
from collections import Counter
from engine.game_state import GameState, coords_para_notacao
from engine.pieces import obter_catalogo_pecas, criar_peca_por_nome
from engine.config import ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS, LINHAS, COLUNAS
from engine.setup import validate_complete_pre_match_setup

# Imports alinhados com o novo renderer.py
from ui.renderer import (
    desenhar_menu_principal, desenhar_definicoes,
    desenhar_selecao_modo, desenhar_selecao_tipo_ia, desenhar_selecao_dificuldade,
    desenhar_tabuleiro, desenhar_pecas,
    desenhar_loja_dinamica, desenhar_log, desenhar_analise,
    desenhar_coordenadas, desenhar_painel_heroi, desenhar_destaques_com_hover,
    desenhar_hud_jogadores, desenhar_eval_bar,
    COLORS, AssetManager, FontManager
)
from ui.hero_encyclopedia import desenhar_enciclopedia_detalhada

from ai.bot import CppEngineBot
from ai.search import analisar_posicao_continuamente
from tools.replay import (
    ReplayCorruptionError,
    ReplayStore,
    capture_initial,
    finalize_completed_game,
    reconstruct,
)
from tools.replay.hover_visuals import install_hover_visuals
from tools.replay.interaction import install_intent_interaction
from ui.audio import AudioManager, VOLUME_STEP

class JogoController:
    def __init__(self):
        pygame.init()
        self.ecra = pygame.display.set_mode((1300, 800), pygame.RESIZABLE)
        pygame.display.set_caption("RedWar - Combat Engine")
        self.clock = pygame.time.Clock()
        self.audio = AudioManager()
        self._terminal_sound_played = False

        self.fase_atual = "MENU"
        self.gs = GameState(time_limit_seconds=180.0)
        self.catalogo = obter_catalogo_pecas()

        self.pontos_jogador = ORCAMENTO_BRANCAS
        self.peca_loja = None
        self.casa_selecionada = None
        self.hover_pos = None

        # --- Configurações da IA ---
        self.elo_escolhido = 1500
        self.modo_predador = False
        self.modo_local_2p = False
        self.lado_draft_atual = "brancas"
        self.pondering_active = False
        self.bot_ativo = None
        # ---------------------------

        self.thread_ia = None
        self.resultado_ia = []

        self.thread_analise = None
        self.analise_resultados_top5 = []
        self.analise_depth_atual = 0
        self.review_index = 0
        self.display_gs = None

        # Enciclopédia
        self.info_hero_index = 0
        self.info_hero_rects = []
        self.btn_info_voltar = pygame.Rect(0, 0, 0, 0)

        # Variáveis Rect UI
        self.botoes_loja = {}
        self.btn_ready = self.btn_start = self.btn_info = self.btn_confirmar = pygame.Rect(0,0,0,0)
        self.btn_vs_ia = self.btn_multi = self.btn_voltar_modo = pygame.Rect(0,0,0,0)
        self.btn_ia_normal = self.btn_ia_predador = self.btn_voltar_tipo = pygame.Rect(0,0,0,0)
        self.btn_voltar_dificuldade = self.rect_elo = self.btn_prev = self.btn_next = pygame.Rect(0,0,0,0)
        self.btn_voltar_menu = pygame.Rect(0,0,0,0)
        self.btn_surrender = pygame.Rect(0, 0, 0, 0)
        self.btn_replays = pygame.Rect(0, 0, 0, 0)
        self.btn_settings = pygame.Rect(0, 0, 0, 0)
        self.btn_settings_back = pygame.Rect(0, 0, 0, 0)
        self.btn_sound_toggle = pygame.Rect(0, 0, 0, 0)
        self.btn_volume_down = pygame.Rect(0, 0, 0, 0)
        self.btn_volume_up = pygame.Rect(0, 0, 0, 0)
        self.btn_replays_back = pygame.Rect(0, 0, 0, 0)
        self.replay_buttons = {}
        self.replay_records = []
        self.replay_error = None

        self.arrastando_elo = False

    def _start_local_2p_draft(self):
        self.modo_local_2p = True
        self.bot_ativo = None
        self.modo_predador = False
        self.lado_draft_atual = "brancas"
        self.gs = GameState(time_limit_seconds=180.0)
        self.pontos_jogador = ORCAMENTO_BRANCAS
        self.peca_loja = None
        self.casa_selecionada = None
        self.hover_pos = None
        self.replay_error = None
        self.fase_atual = "DRAFT"
        self.thread_ia = None
        self.thread_analise = None
        self._terminal_sound_played = False
        pygame.display.set_caption("RedWar - Draft das Brancas")

    def calcular_nos_por_elo(self, elo):
        """Traduz o rating ELO para poder computacional no C++"""
        if elo < 500: return 2000
        if elo < 1000: return 10000
        if elo < 1500: return 50000
        if elo < 2000: return 150000
        return 250000

    def auto_draft_inimigo(self, orcamento: int):
        livro_path = os.path.join("data", "opening_book.json")
        aberturas_pretas = []

        if os.path.exists(livro_path):
            try:
                with open(livro_path, 'r', encoding='utf-8') as f:
                    livro = json.load(f)

                for assinatura, dados in livro.items():
                    equipa = dados.get("team", [])
                    if not equipa: continue

                    is_pretas = all(pos["r"] in [0, 1] for pos in equipa)
                    if is_pretas and dados.get("games", 0) > 0:
                        aberturas_pretas.append(dados)

            except Exception as e:
                print(f"⚠️ Erro ao ler Opening Book: {e}")

        if aberturas_pretas:
            aberturas_pretas.sort(key=lambda x: x["winrate"], reverse=True)
            melhores = aberturas_pretas[:min(3, len(aberturas_pretas))]
            abertura_escolhida = random.choice(melhores)

            nome_ia = self.bot_ativo.nome if self.bot_ativo else "StockWar"
            print(f"\n--- 📚 LIVRO DE ABERTURAS (IA: {nome_ia}) ---")
            print(f"Winrate Histórico: {abertura_escolhida['winrate']}% (em {abertura_escolhida['games']} jogos)")

            equipa = abertura_escolhida["team"]
            nomes_herois = []

            for pos in equipa:
                peca = criar_peca_por_nome(pos["class_name"], 'pretas')
                if peca:
                    self.gs.board[pos["r"]][pos["c"]] = peca
                    nomes_herois.append(peca.name)

            contagem = Counter(nomes_herois)
            equipa_str = " + ".join([f"{qtd}x {nome}" for nome, qtd in contagem.items()])
            print(f"Composição:        {equipa_str}")
            print("------------------------------------------------------\n")
            return

        if self.bot_ativo and hasattr(self.bot_ativo, 'gerar_draft_inteligente'):
            resultado = self.bot_ativo.gerar_draft_inteligente(orcamento, self.catalogo, 'pretas')

            nomes_herois = [pos["piece_class"].__name__ for pos in resultado["draft"]]
            contagem = Counter(nomes_herois)
            equipa_str = " + ".join([f"{qtd}x {nome}" for nome, qtd in contagem.items()])

            print(f"\n--- 🧠 ESTATÍSTICAS DE DRAFT DA IA ({self.bot_ativo.nome}) ---")
            print(f"Tempo de Cálculo: {resultado['tempo_ms']:.2f} ms")
            print(f"Pontos Gastos:    {resultado['pontos_gastos']}/{orcamento}")
            print(f"Desperdício:      {resultado['pontos_desperdicados']} pts")
            print(f"Composição:       {equipa_str}")
            print("------------------------------------------------------\n")

            for pos in resultado["draft"]:
                self.gs.board[pos["r"]][pos["c"]] = pos["piece_class"]('pretas')
        else:
            pts = orcamento
            for r in range(2):
                for c in range(COLUNAS):
                    validas = [p for p in self.catalogo if p["cost"] <= pts]
                    if validas:
                        esc = random.choice(validas)
                        self.gs.board[r][c] = esc["class"]('pretas')
                        pts -= esc["cost"]

    def extrair_acao_valida(self, gs, sr, sc, r, c):
        p = gs.board[sr][sc]
        if not p: return None

        acao = {"type": None, "start": (sr, sc), "end": (r, c)}
        if (r, c) in p.get_valid_moves(sr, sc, gs.board, gs.tile_effects): acao["type"] = "move"
        elif (r, c) in p.get_valid_attacks(sr, sc, gs.board, gs.tile_effects): acao["type"] = "attack"
        else:
            stuns = p.get_valid_stuns(sr, sc, gs.board, gs.tile_effects)
            if (r, c) in stuns and stuns[(r, c)]["has_enemy"]: acao["type"] = "stun"
            else:
                for sp in p.get_valid_spawns(sr, sc, gs.board, gs.tile_effects):
                    if (r, c) == (sp[0], sp[1]):
                        acao["type"] = "spawn"
                        acao["spawn_name"] = sp[2]
                        return acao
                if hasattr(p, 'get_valid_spells'):
                    for spell in p.get_valid_spells(sr, sc, gs.board, gs.tile_effects):
                        if isinstance(spell, dict):
                            target_pos = spell.get("target")
                            spell_name = spell.get("spell_type", "spell")
                        else:
                            target_pos = spell
                            spell_name = "spell"

                        if (r, c) == target_pos:
                            acao["type"] = "spell"
                            acao["spell_name"] = spell_name
                            return acao
        return acao if acao["type"] else None

    def desenhar_animacao(self, gs, start_pos, end_pos, action_type, tam_casa, off_x, off_y):
        sr, sc = start_pos
        er, ec = end_pos
        piece = gs.board[sr][sc] if gs.board[sr][sc] else gs.board[er][ec]

        sx, sy = off_x + sc * tam_casa + tam_casa // 2, off_y + sr * tam_casa + tam_casa // 2
        ex, ey = off_x + ec * tam_casa + tam_casa // 2, off_y + er * tam_casa + tam_casa // 2

        if action_type in ["move", "attack"]: gs.board[sr][sc] = None

        for i in range(16):
            t = i / 15
            cx, cy = sx + (ex - sx) * t, sy + (ey - sy) * t
            self.ecra.fill(COLORS["bg"])

            desenhar_tabuleiro(self.ecra, gs, tam_casa, off_x, off_y)
            desenhar_coordenadas(self.ecra, tam_casa, off_x, off_y)
            desenhar_pecas(self.ecra, gs.board, tam_casa, off_x, off_y)

            if action_type in ["move", "attack"] and piece:
                img = AssetManager.get_image(piece.name, piece.team, tam_casa)
                if img: self.ecra.blit(img, img.get_rect(center=(cx, cy)))
                else: pygame.draw.circle(self.ecra, (200,200,200), (cx, cy), int(tam_casa * 0.38))
            elif action_type == "stun": pygame.draw.circle(self.ecra, (0, 200, 255), (int(cx), int(cy)), 12)
            elif action_type == "spawn": pygame.draw.circle(self.ecra, (200, 100, 255), (int(cx), int(cy)), 12)
            elif action_type == "spell": pygame.draw.circle(self.ecra, (200, 50, 255), (int(cx), int(cy)), 12)

            pygame.display.flip()
            self.clock.tick(60)

        if action_type in ["move", "attack"]: gs.board[sr][sc] = piece

    def get_ui_metrics(self):
        w, h = self.ecra.get_size()
        off_y_tab, off_x = 80, 60
        tam_casa = min(w // (COLUNAS + 1), max(8, (h - off_y_tab - 120) // LINHAS))
        return off_y_tab, off_x, tam_casa

    def thread_de_analise(self, estado_congelado):
        for depth, top_moves in analisar_posicao_continuamente(estado_congelado):
            self.analise_depth_atual = depth
            self.analise_resultados_top5 = top_moves

    def run(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            if self.fase_atual == "BATALHA" and not self.gs.game_over:
                if self.gs.white_to_move: self.gs.white_time = max(0.0, self.gs.white_time - dt)
                else: self.gs.black_time = max(0.0, self.gs.black_time - dt)

            off_y_tab, off_x, tam_casa = self.get_ui_metrics()
            painel_x = off_x + COLUNAS * tam_casa + 30
            mx, my = pygame.mouse.get_pos()

            self.hover_pos = None
            if off_y_tab <= my < off_y_tab + LINHAS*tam_casa and off_x <= mx < off_x + COLUNAS*tam_casa:
                self.hover_pos = ((my - off_y_tab) // tam_casa, (mx - off_x) // tam_casa)

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    pygame.quit()
                    return
                elif evento.type == pygame.VIDEORESIZE:
                    self.ecra = pygame.display.set_mode((evento.w, evento.h), pygame.RESIZABLE)
                elif evento.type == pygame.MOUSEBUTTONUP:
                    self.arrastando_elo = False
                elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                    self.tratar_cliques(mx, my, evento.pos)
                elif evento.type == pygame.MOUSEMOTION:
                    if self.arrastando_elo:
                        perc = max(0.0, min(1.0, (mx - (self.ecra.get_width()//2 - 200)) / 400.0))
                        self.elo_escolhido = int(100 + perc * 2500)

            self.processar_ia()
            self.renderizar(w=self.ecra.get_width(), h=self.ecra.get_height(), off_x=off_x, off_y_tab=off_y_tab, tam_casa=tam_casa, painel_x=painel_x)
            pygame.display.flip()

    def tratar_cliques(self, mx, my, pos):
        if self.fase_atual == "MENU":
            if self.btn_start.collidepoint(mx, my): self.fase_atual = "MODO_JOGO"
            elif self.btn_info.collidepoint(mx, my):
                self.info_hero_index = 0
                self.fase_atual = "INFO"
            elif self.btn_replays.collidepoint(mx, my):
                self._load_recent_replays()
                self.fase_atual = "REPLAYS"
            elif self.btn_settings.collidepoint(mx, my):
                self.fase_atual = "SETTINGS"

        elif self.fase_atual == "SETTINGS":
            if self.btn_settings_back.collidepoint(pos):
                self.fase_atual = "MENU"
            elif self.btn_sound_toggle.collidepoint(pos):
                self.audio.toggle()
            elif self.btn_volume_down.collidepoint(pos):
                self.audio.change_volume(-VOLUME_STEP)
            elif self.btn_volume_up.collidepoint(pos):
                self.audio.change_volume(VOLUME_STEP)

        elif self.fase_atual == "MODO_JOGO":
            if self.btn_vs_ia.collidepoint(mx, my):
                self.modo_local_2p = False
                self.fase_atual = "TIPO_IA"
            elif self.btn_multi.collidepoint(mx, my):
                self._start_local_2p_draft()
            elif self.btn_voltar_modo.collidepoint(mx, my):
                self.fase_atual = "MENU"

        elif self.fase_atual == "TIPO_IA":
            if self.btn_ia_normal.collidepoint(mx, my):
                self.modo_predador = False
                self.fase_atual = "DIFICULDADE"
            elif self.btn_ia_predador.collidepoint(mx, my):
                self.modo_predador = True
                self.fase_atual = "DIFICULDADE"
            elif self.btn_voltar_tipo.collidepoint(mx, my):
                self.fase_atual = "MODO_JOGO"

        elif self.fase_atual == "DIFICULDADE":
            if self.rect_elo.collidepoint(mx, my):
                self.arrastando_elo = True
            elif self.btn_voltar_dificuldade.collidepoint(mx, my):
                self.fase_atual = "TIPO_IA"
            elif self.btn_confirmar.collidepoint(mx, my):
                nos_adequados = self.calcular_nos_por_elo(self.elo_escolhido)
                self.bot_ativo = CppEngineBot(nodes=nos_adequados)
                self.fase_atual = "DRAFT"
                pygame.display.set_caption(f"RedWar - VS {self.bot_ativo.nome}")
                self.gs.current_score = None

        elif self.fase_atual == "INFO":
            if self.btn_info_voltar.collidepoint(mx, my):
                self.fase_atual = "MENU"
            else:
                for rect, index in self.info_hero_rects:
                    if rect.collidepoint(mx, my):
                        self.info_hero_index = index
                        break

        elif self.fase_atual == "DRAFT":
            for nome, rect in self.botoes_loja.items():
                if rect.collidepoint(mx, my):
                    self.peca_loja = None if self.peca_loja == nome else nome
                    return

            draft_side = getattr(self, "lado_draft_atual", "brancas")
            local_2p = getattr(self, "modo_local_2p", False)
            budget = ORCAMENTO_BRANCAS if draft_side == "brancas" else ORCAMENTO_PRETAS
            if self.btn_ready.collidepoint(mx, my) and self.pontos_jogador < budget:
                try:
                    if getattr(self, "modo_local_2p", False):
                        validate_complete_pre_match_setup(self.gs.board)
                        if self.lado_draft_atual == "brancas":
                            self.lado_draft_atual = "pretas"
                            self.pontos_jogador = ORCAMENTO_PRETAS
                            self.peca_loja = None
                            pygame.display.set_caption("RedWar - Draft das Pretas")
                            return
                    else:
                        self.auto_draft_inimigo(ORCAMENTO_PRETAS)
                        validate_complete_pre_match_setup(self.gs.board)
                except ValueError as exc:
                    print(f"⚠️ Setup de pré-match inválido: {exc}")
                    if not local_2p:
                        for row in range(2):
                            for col in range(COLUNAS):
                                piece = self.gs.board[row][col]
                                if piece is not None and piece.team == "pretas":
                                    self.gs.board[row][col] = None
                    return

                self.fase_atual = "BATALHA"
                self._terminal_sound_played = False
                self.gs.replay_metadata = (
                    {"mode": "hotseat", "player_side": "both", "opponent": "Local 2P"}
                    if local_2p
                    else {"mode": "local", "player_side": "brancas", "opponent": "Ares"}
                )
                capture_initial(self.gs)
                self.replay_error = None
                self.peca_loja = None
                self.lado_draft_atual = "brancas"
                pygame.display.set_caption(
                    "RedWar - Turno das Brancas"
                    if local_2p
                    else f"RedWar - VS {self.bot_ativo.nome if self.bot_ativo else 'Ares'}"
                )

            elif self.peca_loja and self.hover_pos:
                r, c = self.hover_pos
                draft_side = getattr(self, "lado_draft_atual", "brancas")
                home_rows = range(LINHAS - 2, LINHAS) if draft_side == "brancas" else range(0, 2)
                team = draft_side
                if 0 <= c < COLUNAS and r in home_rows and self.gs.board[r][c] is None:
                    p_data = next((p for p in self.catalogo if p["name"] == self.peca_loja), None)
                    if p_data and p_data["cost"] <= self.pontos_jogador:
                        self.gs.board[r][c] = p_data["class"](team)
                        self.pontos_jogador -= p_data["cost"]

        elif self.fase_atual == "REPLAYS":
            if self.btn_replays_back.collidepoint(pos):
                self.fase_atual = "MENU"
                self.replay_error = None
                return
            for rect, record in self.replay_buttons.items():
                if rect.collidepoint(pos):
                    self._open_replay(record)
                    return

        elif self.fase_atual == "BATALHA":
            current_team = "brancas" if self.gs.white_to_move else "pretas"
            if self.btn_surrender.collidepoint(pos) and not self.gs.game_over:
                if not self.modo_local_2p and current_team != "brancas":
                    return
                if self.modo_predador and self.pondering_active and self.bot_ativo is not None and hasattr(self.bot_ativo, "stop_pondering"):
                    self.bot_ativo.stop_pondering()
                    self.pondering_active = False
                self._execute_action_with_sound({"type": "surrender", "actor_team": current_team})
                self.casa_selecionada = None
                return

            if (not self.modo_local_2p and not self.gs.white_to_move) or self.gs.game_over:
                return

            if self.hover_pos:
                r, c = self.hover_pos
                if not self.casa_selecionada:
                    if self.gs.board[r][c] and self.gs.board[r][c].team == current_team:
                        self.casa_selecionada = (r, c)
                else:
                    sr, sc = self.casa_selecionada
                    acao = self.extrair_acao_valida(self.gs, sr, sc, r, c)
                    if acao:
                        if self.modo_predador and self.pondering_active and self.bot_ativo is not None and hasattr(self.bot_ativo, 'stop_pondering'):
                            self.bot_ativo.stop_pondering()
                            self.pondering_active = False

                        _, off_x, tam_casa = self.get_ui_metrics()
                        self.desenhar_animacao(self.gs, acao["start"], acao["end"], acao["type"], tam_casa, off_x, 80)
                        self.gs.execute_action(acao)
                    self.casa_selecionada = None

        elif self.fase_atual == "ANALISE":
            total_estados = len(self.gs.move_log)
            if self.btn_prev.collidepoint(pos) and self.review_index > 0:
                estado_antigo = self.display_gs
                self.review_index -= 1
                if self.review_index == total_estados: self.display_gs = self.gs
                else: self.display_gs = self.gs.move_log[self.review_index]["estado_anterior"].fast_clone()
                acao = self.gs.move_log[self.review_index]["acao_escolhida"]
                _, off_x, tam_casa = self.get_ui_metrics()
                self.desenhar_animacao(estado_antigo, acao["end"], acao["start"], acao["type"], tam_casa, off_x, 80)

            elif self.btn_next.collidepoint(pos) and self.review_index < total_estados:
                acao = self.gs.move_log[self.review_index]["acao_escolhida"]
                _, off_x, tam_casa = self.get_ui_metrics()
                self.desenhar_animacao(self.display_gs, acao["start"], acao["end"], acao["type"], tam_casa, off_x, 80)
                self.review_index += 1
                if self.review_index == total_estados: self.display_gs = self.gs
                else: self.display_gs = self.gs.move_log[self.review_index]["estado_anterior"].fast_clone()

            elif self.btn_voltar_menu.collidepoint(pos):
                self.fase_atual = "MENU"
                self.gs = GameState(time_limit_seconds=180.0)
                self.modo_local_2p = False
                self.lado_draft_atual = "brancas"
                self.casa_selecionada = None
                self.hover_pos = None
                self.pontos_jogador = ORCAMENTO_BRANCAS
                self.bot_ativo = None
                self.thread_ia = None
                self.thread_analise = None
            else:
                if self.hover_pos and self.display_gs:
                    r, c = self.hover_pos
                    if not self.casa_selecionada and self.display_gs.board[r][c]:
                        self.casa_selecionada = (r, c)
                    elif self.casa_selecionada:
                        acao = self.extrair_acao_valida(self.display_gs, self.casa_selecionada[0], self.casa_selecionada[1], r, c)
                        if acao:
                            _, off_x, tam_casa = self.get_ui_metrics()
                            self.desenhar_animacao(self.display_gs, acao["start"], acao["end"], acao["type"], tam_casa, off_x, 80)
                            self.display_gs.execute_action(acao)
                            self.analise_resultados_top5 = []
                            self.analise_depth_atual = 0
                            self.thread_analise = threading.Thread(target=self.thread_de_analise, args=(self.display_gs.fast_clone(),))
                            self.thread_analise.daemon = True
                            self.thread_analise.start()
                        self.casa_selecionada = None

    def _execute_action_with_sound(self, action):
        self.gs.execute_action(action)
        self.audio.play_action(action.get("type", ""))
        if self.gs.game_over and not self._terminal_sound_played:
            self.audio.play_terminal()
            self._terminal_sound_played = True

    def processar_ia(self):
        if self.fase_atual == "BATALHA" and self.gs.white_to_move and not self.gs.game_over:
            if self.modo_predador and not self.pondering_active and self.bot_ativo is not None and hasattr(self.bot_ativo, 'start_pondering'):
                self.bot_ativo.start_pondering(self.gs)
                self.pondering_active = True

        if self.fase_atual == "BATALHA" and not self.gs.white_to_move and not self.gs.game_over:
            if self.thread_ia is None and self.bot_ativo is not None:
                def pensar(bot, estado):
                    self.resultado_ia.append(bot.escolher_jogada(estado))
                self.thread_ia = threading.Thread(target=pensar, args=(self.bot_ativo, self.gs.fast_clone()))
                self.thread_ia.daemon = True
                self.thread_ia.start()
                pygame.display.set_caption(f"RedWar - {self.bot_ativo.nome} a pensar...")
            elif self.thread_ia is not None and not self.thread_ia.is_alive():
                parsed = self.resultado_ia.pop() if self.resultado_ia else None
                if parsed:
                    _, off_x, tam_casa = self.get_ui_metrics()
                    self.desenhar_animacao(self.gs, parsed["start"], parsed["end"], parsed["type"], tam_casa, off_x, 80)
                    self._execute_action_with_sound(parsed)
                pygame.display.set_caption("RedWar - O Teu Turno")
                self.thread_ia = None

        if self.fase_atual == "BATALHA" and self.gs.game_over and not self.thread_analise:
            try:
                finalize_completed_game(self.gs)
            except Exception as exc:
                self.replay_error = f"Replay não guardado: {exc}"
                print(f"⚠️ {self.replay_error}")
            self.fase_atual = "ANALISE"
            self.review_index = len(self.gs.move_log)
            self.display_gs = self.gs.fast_clone()
            self.thread_analise = threading.Thread(target=self.thread_de_analise, args=(self.display_gs.fast_clone(),))
            self.thread_analise.daemon = True
            self.thread_analise.start()

    def _load_recent_replays(self):
        try:
            self.replay_records = [
                record for record in ReplayStore().recent() if record is not None
            ]
            self.replay_error = None
        except Exception as exc:
            self.replay_records = []
            self.replay_error = f"Não foi possível ler os replays: {exc}"
            print(f"⚠️ {self.replay_error}")

    def _open_replay(self, record):
        try:
            self.gs = reconstruct(record, include_history=True)
            self.display_gs = self.gs.fast_clone()
            self.review_index = len(self.gs.move_log)
            self.analise_resultados_top5 = []
            self.analise_depth_atual = 0
            self.thread_analise = None
            self.bot_ativo = None
            self.casa_selecionada = None
            self.replay_error = None
            self.fase_atual = "ANALISE"
        except ReplayCorruptionError as exc:
            self.replay_error = f"Replay inválido: {exc}"
            print(f"⚠️ {self.replay_error}")

    def _draw_recent_replays(self, w, h):
        self.ecra.fill(COLORS["bg"])
        title = FontManager.get("arial", 40, bold=True)
        self.ecra.blit(
            title.render("Replays Recentes", True, COLORS["text"]),
            (w // 2 - 175, 90),
        )

        self.replay_buttons = {}
        y = 170
        for record in self.replay_records:
            rect = pygame.Rect(w // 2 - 300, y, 600, 54)
            pygame.draw.rect(self.ecra, COLORS["btn_secondary"], rect, border_radius=8)
            winner = record.get("result", {}).get("winner", "Resultado desconhecido")
            created = str(record.get("created_at", "")).replace("T", " ").replace("+00:00", " UTC")
            label = f"{created[:19]} — {winner}"
            text = FontManager.get("arial", 17).render(label[:72], True, COLORS["text"])
            self.ecra.blit(text, (rect.x + 14, rect.y + 15))
            self.replay_buttons[rect] = record
            y += 66

        if not self.replay_records and not self.replay_error:
            msg = FontManager.get("arial", 20).render(
                "Ainda não existem replays guardados.",
                True,
                COLORS["text_muted"],
            )
            self.ecra.blit(msg, (w // 2 - msg.get_width() // 2, 180))

        if self.replay_error:
            msg = FontManager.get("arial", 18).render(
                self.replay_error[:90],
                True,
                COLORS["danger"],
            )
            self.ecra.blit(msg, (w // 2 - msg.get_width() // 2, h - 125))

        self.btn_replays_back = pygame.Rect(w // 2 - 100, h - 75, 200, 46)
        pygame.draw.rect(
            self.ecra,
            COLORS["btn_primary"],
            self.btn_replays_back,
            border_radius=8,
        )
        msg = FontManager.get("arial", 19, bold=True).render(
            "Voltar",
            True,
            COLORS["text"],
        )
        self.ecra.blit(msg, msg.get_rect(center=self.btn_replays_back.center))

    def renderizar(self, w, h, off_x, off_y_tab, tam_casa, painel_x):
        if self.fase_atual == "MENU":
            self.btn_start, self.btn_info, self.btn_replays, self.btn_settings = desenhar_menu_principal(self.ecra, w, h)
        elif self.fase_atual == "REPLAYS":
            self._draw_recent_replays(w, h)
        elif self.fase_atual == "SETTINGS":
            (self.btn_settings_back, self.btn_sound_toggle,
             self.btn_volume_down, self.btn_volume_up) = desenhar_definicoes(
                self.ecra, w, h, self.audio.enabled, self.audio.volume
            )
        elif self.fase_atual == "MODO_JOGO":
            self.btn_vs_ia, self.btn_multi, self.btn_voltar_modo = desenhar_selecao_modo(self.ecra, w, h)
        elif self.fase_atual == "TIPO_IA":
            self.btn_ia_normal, self.btn_ia_predador, self.btn_voltar_tipo = desenhar_selecao_tipo_ia(self.ecra, w, h)
        elif self.fase_atual == "DIFICULDADE":
            self.rect_elo, self.btn_confirmar, self.btn_voltar_dificuldade = desenhar_selecao_dificuldade(self.ecra, w, h, self.elo_escolhido)
        elif self.fase_atual == "INFO":
            self.btn_info_voltar, self.info_hero_rects = desenhar_enciclopedia_detalhada(
                self.ecra, w, h, self.catalogo, self.info_hero_index
            )
        else:
            self.ecra.fill(COLORS["bg"])
            try: desenhar_eval_bar(self.ecra, self.gs, off_x - 30, LINHAS * tam_casa, off_y_tab)
            except Exception: pass

            hud_name = "Jogador 2" if self.modo_local_2p else (self.bot_ativo.nome if self.bot_ativo else "StockWar")
            desenhar_hud_jogadores(self.ecra, off_x, 20, off_y_tab + LINHAS * tam_casa + 20, tam_casa, hud_name, self.gs)

            if self.gs.game_over:
                fonte_fim = FontManager.get("arial", 24, bold=True)
                txt = fonte_fim.render(f"FIM DE JOGO: {self.gs.winner}", True, COLORS["danger"])
                self.ecra.blit(txt, (off_x, off_y_tab - 35))

            to_draw = self.display_gs if (self.fase_atual == "ANALISE" and self.display_gs) else self.gs
            desenhar_tabuleiro(self.ecra, to_draw, tam_casa, off_x, off_y_tab)
            desenhar_coordenadas(self.ecra, tam_casa, off_x, off_y_tab)

            if self.fase_atual == "DRAFT":
                self.botoes_loja, self.btn_ready = desenhar_loja_dinamica(
                    self.ecra, painel_x, 20, 350, h - 40, self.catalogo,
                    self.pontos_jogador, self.peca_loja,
                    team=self.lado_draft_atual,
                )
                # O draft permite cópias do mesmo herói. Mostramos explicitamente
                # quantas cópias já foram colocadas, para não parecer um acidente da UI.
                colocados = Counter(
                    p.name
                    for row in self.gs.board[LINHAS - 2:]
                    for p in row
                    if p is not None and p.team == "brancas"
                )
                f_count = FontManager.get("arial", 14, bold=True)
                for nome, rect in self.botoes_loja.items():
                    qtd = colocados.get(nome, 0)
                    if qtd:
                        badge = pygame.Rect(rect.right - 38, rect.y + 4, 32, 18)
                        pygame.draw.rect(self.ecra, (25, 25, 25), badge, border_radius=7)
                        txt = f_count.render(f"×{qtd}", True, COLORS["warning"])
                        self.ecra.blit(txt, (badge.centerx - txt.get_width() // 2, badge.centery - txt.get_height() // 2))

            elif self.fase_atual == "ANALISE":
                pygame.draw.rect(self.ecra, (20, 20, 30), (painel_x, 20, 350, h - 40), border_radius=10)
                self.ecra.blit(FontManager.get("arial", 22, bold=True).render(f"Análise (Profundidade: {self.analise_depth_atual})", True, (150, 200, 255)), (painel_x + 15, 35))

                f_top = FontManager.get("arial", 16)
                yy = 80
                for rank, mv in enumerate(self.analise_resultados_top5):
                    c = COLORS["text"] if rank == 0 else (180, 180, 180)
                    str_alg = f"{coords_para_notacao(*mv['start'])}-{coords_para_notacao(*mv['end'])}"
                    txt = f"{rank+1}. {str_alg} (Score: {mv['score']:.1f})"
                    self.ecra.blit(f_top.render(txt, True, c), (painel_x + 20, yy))
                    yy += 30

                self.btn_prev = pygame.Rect(painel_x + 20, h - 80, 80, 40)
                self.btn_next = pygame.Rect(painel_x + 110, h - 80, 80, 40)
                self.btn_voltar_menu = pygame.Rect(painel_x + 200, h - 80, 130, 40)

                pygame.draw.rect(self.ecra, (80,80,80), self.btn_prev, border_radius=6)
                pygame.draw.rect(self.ecra, (80,80,80), self.btn_next, border_radius=6)
                pygame.draw.rect(self.ecra, COLORS["danger"], self.btn_voltar_menu, border_radius=6)

                fbtn = FontManager.get("arial", 20, bold=True)
                self.ecra.blit(fbtn.render("Anterior", True, COLORS["text"]), (self.btn_prev.x + 6, self.btn_prev.y + 8))
                self.ecra.blit(fbtn.render("Próximo", True, COLORS["text"]), (self.btn_next.x + 6, self.btn_next.y + 8))
                self.ecra.blit(fbtn.render("Sair / Menu", True, COLORS["text"]), (self.btn_voltar_menu.x + 12, self.btn_voltar_menu.y + 8))
            else:
                if self.fase_atual == "BATALHA":
                    self.btn_surrender = pygame.Rect(
                        off_x,
                        min(h - 42, off_y_tab + LINHAS * tam_casa + 54),
                        128,
                        34,
                    )
                    enabled = (self.modo_local_2p or self.gs.white_to_move) and not self.gs.game_over
                    pygame.draw.rect(
                        self.ecra,
                        COLORS["danger"] if enabled else (75, 75, 75),
                        self.btn_surrender,
                        border_radius=7,
                    )
                    pygame.draw.rect(
                        self.ecra,
                        COLORS["text"],
                        self.btn_surrender,
                        1,
                        border_radius=7,
                    )
                    f_surrender = FontManager.get("arial", 17, bold=True)
                    label = "Desistir" if enabled else "Desistir (turno IA)"
                    txt = f_surrender.render(label, True, COLORS["text"])
                    self.ecra.blit(txt, txt.get_rect(center=self.btn_surrender.center))
                elif self.hover_pos and self.gs.board[self.hover_pos[0]][self.hover_pos[1]]:
                    desenhar_painel_heroi(self.ecra, self.gs.board[self.hover_pos[0]][self.hover_pos[1]], painel_x, 20, 350, h - 40)
                else:
                    desenhar_log(self.ecra, self.gs, painel_x, 20, 350, h - 40)

            if self.casa_selecionada:
                desenhar_destaques_com_hover(self.ecra, to_draw, self.casa_selecionada, self.hover_pos, tam_casa, off_x, off_y_tab)
                pygame.draw.rect(self.ecra, (255, 255, 50), (off_x + self.casa_selecionada[1] * tam_casa, off_y_tab + self.casa_selecionada[0] * tam_casa, tam_casa, tam_casa), 3)

            desenhar_pecas(self.ecra, to_draw.board, tam_casa, off_x, off_y_tab)

if __name__ == "__main__":
    app = JogoController()
    install_hover_visuals(app)
    install_intent_interaction(app)
    app.run()
