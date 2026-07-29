import random
import time
from engine.game_state import GameState
from ai.evaluator import avaliador_mestre

print('Iniciando simulação rápida...')
start = time.time()

gs = GameState()
print('Estado inicial OK')
try:
    score0 = avaliador_mestre(gs)
    print('Avaliador inicial OK, score:', score0)
except Exception as e:
    print('Erro ao avaliar estado inicial:', e)

moves_made = 0
max_moves = 100

while moves_made < max_moves and not gs.game_over:
    # coletar possíveis ações simples: move/attack/stun/spawn
    actions = []
    for r in range(len(gs.board)):
        for c in range(len(gs.board[0])):
            p = gs.board[r][c]
            if p and ((gs.white_to_move and p.team=='brancas') or (not gs.white_to_move and p.team=='pretas')):
                for mv in p.get_valid_moves(r, c, gs.board, gs.tile_effects):
                    actions.append(('move', (r,c), mv))
                for at in p.get_valid_attacks(r, c, gs.board, gs.tile_effects):
                    actions.append(('attack', (r,c), at))
                stuns = p.get_valid_stuns(r, c, gs.board, gs.tile_effects)
                for foco, info in stuns.items():
                    if info['has_enemy']:
                        actions.append(('stun', (r,c), foco, info['aoe']))
                for sp in p.get_valid_spawns(r, c, gs.board, gs.tile_effects):
                    actions.append(('spawn', (r,c), (sp[0], sp[1]), sp[2]))
    if not actions:
        # passar turno usando null-move
        gs.make_null_move()
        moves_made += 1
        continue
    act = random.choice(actions)
    try:
        if act[0] == 'move':
            gs.make_action(act[1], act[2], 'move')
        elif act[0] == 'attack':
            gs.make_action(act[1], act[2], 'attack')
        elif act[0] == 'stun':
            gs.make_action(act[1], act[2], 'stun', affected_area=act[3])
        elif act[0] == 'spawn':
            gs.make_action(act[1], act[2], 'spawn', spawn_name=act[3])
    except Exception as e:
        print('Erro ao executar ação:', e)
        break
    moves_made += 1

print('Simulação terminada. Movimentos feitos:', moves_made)
try:
    score1 = avaliador_mestre(gs)
    print('Avaliador final OK, score:', score1)
except Exception as e:
    print('Erro ao avaliar estado final:', e)

print('Tempo total:', time.time() - start)
print('OK - script concluído')
