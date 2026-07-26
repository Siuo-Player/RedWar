import pygame
import sys
from ui.window import TAMANHO_CASA, COLUNAS, LINHAS, LARGURA, ALTURA, desenhar_tabuleiro
from ui.renderer import desenhar_pecas, desenhar_destaques
from engine.game_state import GameState

def main():
    pygame.init()
    ecra = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("RedWar - Combat Engine")
    
    gs = GameState()
    casa_selecionada = None
    movimentos, ataques, stuns = [], [], {}
    correr = True
    
    while correr:
        # Obter posição atual do rato (para o efeito Hover do Stun)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        hover_pos = (mouse_y // TAMANHO_CASA, mouse_x // TAMANHO_CASA)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                correr = False
                
            elif evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    x, y = pygame.mouse.get_pos()
                    coluna = x // TAMANHO_CASA
                    linha = y // TAMANHO_CASA
                    alvo = (linha, coluna)
                    
                    # 1. Tentar executar ação se já tivermos uma peça selecionada
                    if casa_selecionada:
                        if alvo in movimentos:
                            gs.make_action(casa_selecionada, alvo, "move")
                            casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                            continue
                        elif alvo in ataques:
                            gs.make_action(casa_selecionada, alvo, "attack")
                            casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                            continue
                        elif alvo in stuns:
                            gs.make_action(casa_selecionada, alvo, "stun", affected_area=stuns[alvo])
                            casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                            continue

                    # 2. Selecionar uma peça nova
                    if casa_selecionada == alvo:
                        # Duplo clique desmarca
                        casa_selecionada, movimentos, ataques, stuns = None, [], [], {}
                    else:
                        peca_clicada = gs.board[linha][coluna]
                        # Apenas deixa selecionar se houver peça, se for a vez da equipa dela, e se não estiver atordoada
                        is_white = (peca_clicada and peca_clicada.team == 'brancas')
                        if peca_clicada and peca_clicada.can_act() and (is_white == gs.white_to_move):
                            casa_selecionada = alvo
                            movimentos = peca_clicada.get_valid_moves(linha, coluna, gs.board)
                            ataques = peca_clicada.get_valid_attacks(linha, coluna, gs.board)
                            stuns = peca_clicada.get_valid_stuns(linha, coluna, gs.board)
                        else:
                            casa_selecionada, movimentos, ataques, stuns = None, [], [], {}

        # Ordem de desenho é crítica: Tabuleiro -> Destaques (Overlays) -> Peças
        desenhar_tabuleiro(ecra, casa_selecionada)
        desenhar_destaques(ecra, movimentos, ataques, stuns, hover_pos)
        desenhar_pecas(ecra, gs.board)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()