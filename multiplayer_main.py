# multiplayer_main.py
import pygame
import sys
from network.client import NetworkClient
from ui.renderer import desenhar_tabuleiro, C_FUNDO
import types
from engine.config import LINHAS, COLUNAS

# Como não temos um objeto "Piece" físico, apenas dicionários vindos do JSON,
# precisamos de um renderizador ligeiramente adaptado para a rede:
def desenhar_pecas_rede(ecra, board_data, tam_casa, off_x, off_y):
    if not board_data: return
    fonte = pygame.font.Font(None, int(tam_casa * 0.4))
    
    for r in range(LINHAS):
        for c in range(COLUNAS):
            p_data = board_data[r][c]
            if p_data:
                cx, cy = off_x + c * tam_casa + tam_casa//2, off_y + r * tam_casa + tam_casa//2
                cor_peca = (220, 220, 220) if p_data["team"] == 'brancas' else (40, 40, 40)
                pygame.draw.circle(ecra, cor_peca, (cx, cy), int(tam_casa * 0.4))
                
                cor_texto = (0, 0, 0) if p_data["team"] == 'brancas' else (255, 255, 255)
                # Pega na 1ª e 2ª letra do nome para fazer a sigla
                sigla = p_data["name"][:2].capitalize() if p_data["name"] != "BoneLord" else "BL"
                texto = fonte.render(sigla, True, cor_texto)
                
                rect_texto = texto.get_rect(center=(cx, cy))
                ecra.blit(texto, rect_texto)
                
                if p_data["stun_timer"] > 0:
                    pygame.draw.circle(ecra, (0, 200, 255), (cx, cy), int(tam_casa * 0.45), 3)

def main():
    pygame.init()
    ecra = pygame.display.set_mode((900, 800), pygame.RESIZABLE)
    
    # Deteta se passaste um IP pelo terminal; se não, usa localhost por precaução
    ip_servidor = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    
    pygame.display.set_caption(f"RedWar - A ligar a {ip_servidor}...")
    clock = pygame.time.Clock()
    
    cliente = NetworkClient(host=ip_servidor, port=8765)
    
    # Variáveis de interação
    casa_selecionada = None
    
    correr = True
    while correr:
        estado_rede = cliente.latest_state
        
        # Atualizar título da janela
        if cliente.cor_atribuida:
            turno = "O TEU TURNO" if (estado_rede and (
                (estado_rede["white_to_move"] and cliente.cor_atribuida == 'brancas') or 
                (not estado_rede["white_to_move"] and cliente.cor_atribuida == 'pretas')
            )) else "A AGUARDAR ADVERSÁRIO"
            pygame.display.set_caption(f"RedWar Multiplayer | {cliente.cor_atribuida.upper()} | {turno}")
            
        w, h = ecra.get_size()
        tam_casa = min(w // COLUNAS, h // LINHAS) - 10
        off_x = (w - (COLUNAS * tam_casa)) // 2
        off_y = (h - (LINHAS * tam_casa)) // 2

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: 
                correr = False
            elif evento.type == pygame.VIDEORESIZE:
                ecra = pygame.display.set_mode((evento.w, evento.h), pygame.RESIZABLE)
            
            elif evento.type == pygame.MOUSEBUTTONDOWN and estado_rede and not estado_rede["game_over"]:
                if evento.button == 1:
                    mx, my = pygame.mouse.get_pos()
                    
                    if off_y <= my < off_y + LINHAS*tam_casa and off_x <= mx < off_x + COLUNAS*tam_casa:
                        c = (mx - off_x) // tam_casa
                        r = (my - off_y) // tam_casa
                        
                        # VERIFICAÇÃO SIMPLIFICADA PARA TESTE (Envia um movimento)
                        # Num cenário ideal, a UI desenha os quadrados verdes (get_valid_moves) lendo do estado local.
                        # Para já, ao clicar na peça e depois noutra casa, envia a tentativa ao Servidor.
                        if not casa_selecionada:
                            peca_clicada = estado_rede["board"][r][c]
                            if peca_clicada and peca_clicada["team"] == cliente.cor_atribuida:
                                casa_selecionada = (r, c)
                        else:
                            # Tenta mover/atacar a casa clicada. O servidor validará e aprovará (ou ignorará).
                            cliente.enviar_acao(
                                start=casa_selecionada, 
                                end=(r, c), 
                                action_type="move" # Por defeito envia move, o server pode ser adaptado para inferir ataque
                            )
                            casa_selecionada = None

        ecra.fill(C_FUNDO)
        # desenhar_tabuleiro espera um objeto `gs`; como aqui usamos estado em JSON
        # criamos um objeto mínimo que satisfaça os atributos lidos pelo renderer.
        dummy_gs = types.SimpleNamespace(last_move=None, tile_effects=None)
        desenhar_tabuleiro(ecra, dummy_gs, tam_casa, off_x, off_y)
        
        if casa_selecionada:
            r, c = casa_selecionada
            pygame.draw.rect(ecra, (150, 150, 50), (off_x + c * tam_casa, off_y + r * tam_casa, tam_casa, tam_casa), 4)

        if estado_rede:
            desenhar_pecas_rede(ecra, estado_rede["board"], tam_casa, off_x, off_y)
        else:
            fonte = pygame.font.Font(None, 48)
            txt = fonte.render("A conectar ao Servidor...", True, (255,255,255))
            ecra.blit(txt, (w//2 - txt.get_width()//2, h//2))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()