import pygame
import time
import random
from engine.game_state import GameState
from engine.pieces import obter_catalogo_pecas
from ui.renderer import desenhar_tabuleiro, desenhar_pecas, desenhar_loja_dinamica, desenhar_enciclopedia, C_FUNDO

ORCAMENTO_BRANCAS = 180 
ORCAMENTO_PRETAS = 200 

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

def main():
    pygame.init()
    ecra = pygame.display.set_mode((900, 800), pygame.RESIZABLE)
    pygame.display.set_caption("RedWar - Combat Engine")
    clock = pygame.time.Clock()
    
    gs = GameState(time_limit_seconds=180)
    fase_atual = "DRAFT"
    pontos_jogador = ORCAMENTO_BRANCAS
    peca_loja = None
    catalogo = obter_catalogo_pecas()
    
    # CORREÇÃO PYLANCE: Inicializar botões com retângulos vazios antes do loop
    btn_voltar = pygame.Rect(0, 0, 0, 0)
    btn_ready = pygame.Rect(0, 0, 0, 0)
    btn_info = pygame.Rect(0, 0, 0, 0)
    botoes_loja = {}
    
    correr = True
    while correr:
        w, h = ecra.get_size()
        h_tabuleiro = h - 160
        tam_casa = min(w // 8, h_tabuleiro // 8)
        off_x = (w - (8 * tam_casa)) // 2
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
                        elif peca_loja and off_y <= my < off_y + 8*tam_casa:
                            c = (mx - off_x) // tam_casa
                            r = (my - off_y) // tam_casa
                            if 0 <= c < 8 and r >= 6 and gs.board[r][c] is None:
                                p_data = next((p for p in catalogo if p["name"] == peca_loja), None)
                                if p_data and p_data["cost"] <= pontos_jogador:
                                    gs.board[r][c] = p_data["class"]('brancas')
                                    pontos_jogador -= p_data["cost"]
                                    peca_loja = None

        ecra.fill(C_FUNDO)
        
        if fase_atual == "INFO":
            btn_voltar = desenhar_enciclopedia(ecra, w, h, catalogo)
        else:
            desenhar_tabuleiro(ecra, tam_casa, off_x, off_y)
            desenhar_pecas(ecra, gs.board, tam_casa, off_x, off_y)
            if fase_atual == "DRAFT":
                botoes_loja, btn_ready, btn_info = desenhar_loja_dinamica(ecra, w, h, catalogo, pontos_jogador, peca_loja, off_loja)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()