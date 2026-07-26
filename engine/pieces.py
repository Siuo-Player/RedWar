class Piece:
    def __init__(self, team, name, cost):
        self.team = team  # 'brancas' ou 'pretas' (ou 'jogador1'/'jogador2')
        self.name = name
        self.cost = cost  # Essencial para a IA calcular a vantagem material
        
        # Estados temporários
        self.is_frozen = False
        self.frozen_timers = 0

    def get_valid_moves(self, r, c, board):
        # Cada peça específica (ex: Cavaleiro, Mago) vai reescrever esta função.
        # Retorna uma lista de tuplos com as coordenadas (linha, coluna) válidas.
        return []

    def __repr__(self):
        # Representação em texto para debug na consola
        return f"{self.name[0]}{'B' if self.team == 'brancas' else 'P'}"
