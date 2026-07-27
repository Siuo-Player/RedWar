import pygame
import time
import random
from engine.game_state import GameState
from engine.pieces import obter_catalogo_pecas
from ui.renderer import desenhar_tabuleiro, desenhar_destaques, desenhar_pecas, desenhar_loja_dinamica, desenhar_enciclopedia, desenhar_log, C_FUNDO, carregar_imagem_peca
from engine.config import ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS, LIMITE_TURNOS
from ai.search import find_best_move
from ai.evaluator import avaliador_guloso

def auto_draft_ia(gs, orcamento):
    pontos = orcamento
    cat = obter_catalogo_pecas()
    for r in range(2):
        for c in range(8):
            validas = [p for p in cat if p["cost"] <= pontos]
            if not validas: break
            esc = random.choice(validas)
            gs.board[r][c] = esc["class"]('pretas')
            pontos -= esc["cost"]

def animar_acao(ecra, gs, start_pos, end_pos, action_type, tam_casa, off_x, off_y, clock):
    """Anima o movimento da peça ou o lançamento de partículas de magias."""
    sr, sc = start_pos
    er, ec = end_pos
    piece = gs.board[sr][sc]
    
    sx = off_x + sc * tam_casa + tam_casa // 2
    sy = off_y + sr * tam_casa + tam_casa // 2
    ex = off_x + ec * tam_casa + tam_casa // 2
    ey = off_y + er * tam_casa + tam_casa // 2
    
    frames = 15
    
    # Esconde a peça temporariamente para não a desenhar duas vezes
    if action_type in ["move", "attack"]:
        gs.board[sr][sc] = None
        
    for i in range(frames + 1):
        t = i / frames
        cx = sx + (ex - sx) * t
        cy = sy + (ey - sy) * t
        
        ecra.fill(C_FUNDO)
        desenhar_tabuleiro(ecra, gs, tam_casa, off_x, off_y)
        desenhar_pecas(ecra, gs.board, tam_casa, off_x, off_y)
        
        # Desenha a aba do log para o ecrã não piscar preto
        w, h = ecra.get_size()
        desenhar_log(ecra, gs, off_x + 8*tam_casa + 20, 20, 350, h - 40)
        
        if action_type in ["move", "attack"]:
            img = carregar_imagem_peca(piece.name, piece.team, tam_casa)
            if img:
                ecra.blit(img, img.get_rect(center=(cx, cy)))
            else:
                pygame.draw.circle(ecra, (200,200,200), (cx, cy), int(tam_casa * 0.38))
        elif action_type == "stun":
            pygame.draw.circle(ecra, (0, 200, 255), (int(cx), int(cy)), 12) # Bola Mágica de Gelo
        elif action_type == "spawn":
            pygame.draw.circle(ecra, (200, 100, 255), (int(cx), int(cy)), 12) # Energia Negra
            
        pygame.display.flip()
        clock.tick(60)
        
    # Devolve a peça ao sítio original (o make_action vai tratá-la oficialmente)
    if action_type in ["move", "attack"]:
        gs.board[sr][sc] = piece

def main():
    pygame.init()
    # Aumentei o tamanho da janela para 1300x800 para caber o Painel de Log
    ecra = pygame.display.set_mode((1300, 800), pygame.RESIZABLE)
    pygame.display.set_caption("RedWar - Combat Engine")
    clock = pygame.time.Clock()
    
    gs = GameState(time_limit_seconds=180)
    
    fase_atual = "DRAFT"
    pontos_jogador = ORCAMENTO_BRANCAS
    peca_loja = None
    casa_selecionada = None
    catalogo = obter_catalogo_pecas()
    
    btn_voltar = pygame.Rect(0, 0, 0, 0)
    btn_ready = pygame.Rect(0, 0, 0, 0)
    btn_info = pygame.Rect(0, 0, 0, 0)
    botoes_loja = {}
    
    correr = True
    while correr:
        w, h = ecra.get_size()
        h_tabuleiro = h - 160
        tam_casa = min(w // 8, h_tabuleiro // 8)
        # O tabuleiro encosta à esquerda, o painel de log fica à direita
        off_x = 20
        off_y = 20
        off_loja = off_y + (8 * tam_casa) + 20

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: 
                correr = False
            elif evento.type == pygame.VIDEORESIZE:
                ecra = pygame.display.set_mode((evento.w, evento.h), pygame.RESIZABLE)
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    
                    if fase_atual == "INFO":
                        if btn_voltar.collidepoint(mx, my):
                            fase_atual = "DRAFT"
                    
                    elif fase_atual == "DRAFT":
                        if my >= off_loja:
                            for nome, rect in botoes_loja.items():
                                if rect.collidepoint(mx, my): peca_loja = nome
                            if btn_ready.collidepoint(mx, my):
                                auto_draft_ia(gs, ORCAMENTO_PRETAS)
                                fase_atual = "BATALHA"
                            if btn_info.collidepoint(mx, my):
                                fase_atual = "INFO"
                        elif peca_loja and off_y <= my < off_y + 8*tam_casa and off_x <= mx < off_x + 8*tam_casa:
                            c = (mx - off_x) // tam_casa
                            r = (my - off_y) // tam_casa
                            if 0 <= c < 8 and r >= 6 and gs.board[r][c] is None:
                                p_data = next((p for p in catalogo if p["name"] == peca_loja), None)
                                if p_data and p_data["cost"] <= pontos_jogador:
                                    gs.board[r][c] = p_data["class"]('brancas')
                                    pontos_jogador -= p_data["cost"]
                                    peca_loja = None

                    elif fase_atual == "BATALHA" and gs.white_to_move and not gs.game_over:
                        if off_y <= my < off_y + 8*tam_casa and off_x <= mx < off_x + 8*tam_casa:
                            c = (mx - off_x) // tam_casa
                            r = (my - off_y) // tam_casa
                            
                            if not casa_selecionada:
                                p = gs.board[r][c]
                                if p and p.team == 'brancas':
                                    casa_selecionada = (r, c)
                            else:
                                sr, sc = casa_selecionada
                                p = gs.board[sr][sc]
                                if p:
                                    if (r, c) in p.get_valid_moves(sr, sc, gs.board, gs.tile_effects):
                                        animar_acao(ecra, gs, (sr, sc), (r, c), "move", tam_casa, off_x, off_y, clock)
                                        gs.make_action((sr, sc), (r, c), "move")
                                    elif (r, c) in p.get_valid_attacks(sr, sc, gs.board, gs.tile_effects):
                                        animar_acao(ecra, gs, (sr, sc), (r, c), "attack", tam_casa, off_x, off_y, clock)
                                        gs.make_action((sr, sc), (r, c), "attack")
                                    else:
                                        stuns = p.get_valid_stuns(sr, sc, gs.board, gs.tile_effects)
                                        if (r, c) in stuns and stuns[(r, c)]["has_enemy"]:
                                            animar_acao(ecra, gs, (sr, sc), (r, c), "stun", tam_casa, off_x, off_y, clock)
                                            gs.make_action((sr, sc), (r, c), "stun", affected_area=stuns[(r, c)]["aoe"])
                                        else:
                                            spawns = p.get_valid_spawns(sr, sc, gs.board, gs.tile_effects)
                                            for sp in spawns:
                                                if (r, c) == (sp[0], sp[1]):
                                                    animar_acao(ecra, gs, (sr, sc), (r, c), "spawn", tam_casa, off_x, off_y, clock)
                                                    gs.make_action((sr, sc), (r, c), "spawn", spawn_name=sp[2])
                                                    break
                                casa_selecionada = None

        if fase_atual == "BATALHA" and not gs.white_to_move and not gs.game_over:
            pygame.display.set_caption("RedWar - IA a pensar...")
            best_move = find_best_move(gs, depth=2, evaluator_func=avaliador_guloso)
            if best_move:
                animar_acao(ecra, gs, best_move["start"], best_move["end"], best_move["type"], tam_casa, off_x, off_y, clock)
                gs.make_action(best_move["start"], best_move["end"], best_move["type"], best_move.get("area"), best_move.get("spawn_name"))
            pygame.display.set_caption("RedWar - Combat Engine")

        ecra.fill(C_FUNDO)
        
        if fase_atual == "INFO":
            btn_voltar = desenhar_enciclopedia(ecra, w, h, catalogo)
        else:
            desenhar_tabuleiro(ecra, gs, tam_casa, off_x, off_y)
            
            if fase_atual == "BATALHA":
                desenhar_log(ecra, gs, off_x + 8*tam_casa + 20, 20, 350, h - 40)
            
            if casa_selecionada and fase_atual == "BATALHA":
                desenhar_destaques(ecra, gs, casa_selecionada, tam_casa, off_x, off_y)
            
            if casa_selecionada:
                r, c = casa_selecionada
                pygame.draw.rect(ecra, (255, 255, 50), (off_x + c * tam_casa, off_y + r * tam_casa, tam_casa, tam_casa), 3)

            desenhar_pecas(ecra, gs.board, tam_casa, off_x, off_y)
            
            if fase_atual == "DRAFT":
                botoes_loja, btn_ready, btn_info = desenhar_loja_dinamica(ecra, w, h, catalogo, pontos_jogador, peca_loja, off_loja)
            elif gs.game_over:
                fonte_fim = pygame.font.SysFont("arial", 48, bold=True)
                txt = fonte_fim.render(f"FIM DE JOGO: {gs.winner}", True, (255, 100, 100))
                s_fim = pygame.Surface((txt.get_width() + 40, txt.get_height() + 20), pygame.SRCALPHA)
                s_fim.fill((0, 0, 0, 200))
                ecra.blit(s_fim, (off_x + 4*tam_casa - s_fim.get_width()//2, off_y + 4*tam_casa - s_fim.get_height()//2))
                ecra.blit(txt, (off_x + 4*tam_casa - txt.get_width()//2, off_y + 4*tam_casa - txt.get_height()//2))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()