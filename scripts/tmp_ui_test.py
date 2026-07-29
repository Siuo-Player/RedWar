import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
import pygame
from engine.game_state import GameState
from engine.config import LINHAS, COLUNAS
from ui.renderer import desenhar_tabuleiro, desenhar_pecas, desenhar_eval_bar, desenhar_hud_jogadores, desenhar_coordenadas, desenhar_log

pygame.init()
w,h = 1100, 700
screen = pygame.display.set_mode((w,h))

# prepare a game state
gs = GameState()
# compute tile size
tam_casa = min(w // (COLUNAS + 1), (h - 160) // LINHAS)
off_x, off_y = 40, 20

# draw
desenhar_eval_bar(screen, gs, 0, tam_casa, off_y)
desenhar_hud_jogadores(screen, w, off_x, off_y, tam_casa, 'TestBot', gs)
desenhar_tabuleiro(screen, gs, tam_casa, off_x, off_y)
desenhar_coordenadas(screen, tam_casa, off_x, off_y)
desenhar_pecas(screen, gs.board, tam_casa, off_x, off_y)
desenhar_log(screen, gs, off_x + COLUNAS * tam_casa + 30, 20, 350, h - 40)

os.makedirs('ui', exist_ok=True)
out = os.path.join('ui','test_screenshot.png')
pygame.image.save(screen, out)
print('OK:'+out)
pygame.quit()
