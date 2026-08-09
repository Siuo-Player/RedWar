import re

class ActionParser:
    """
    Tradutor universal de Ações.
    Converte Strings padronizadas vindas de qualquer IA (Python ou C++)
    em comandos interpretáveis pelo motor de jogo.
    """
    
    # Regex para Coordenadas (Ex: A1, J10)
    COORD = r"([A-Z][1-9][0-9]*)"
    
    PATTERN_MOVE = re.compile(rf"^MOVE\s+{COORD}\s+{COORD}$", re.IGNORECASE)
    PATTERN_ATTACK = re.compile(rf"^ATTACK\s+{COORD}\s+{COORD}$", re.IGNORECASE)
    PATTERN_STUN = re.compile(rf"^STUN\s+{COORD}\s+{COORD}$", re.IGNORECASE)
    # Spawn e Spell agora transportam a Origem e preservam o nome exato (ex: BoneLord)
    PATTERN_SPAWN = re.compile(rf"^SPAWN\s+([a-zA-Z_]+)\s+{COORD}\s+{COORD}$", re.IGNORECASE)
    PATTERN_SPELL = re.compile(rf"^SPELL\s+([a-zA-Z_]+)\s+{COORD}\s+{COORD}$", re.IGNORECASE)

    @staticmethod
    def parse(action_str: str) -> dict | None:
        action_str = action_str.strip()
        
        match = ActionParser.PATTERN_MOVE.match(action_str)
        if match: return {"action": "MOVE", "origin": match.group(1).upper(), "target": match.group(2).upper()}
            
        match = ActionParser.PATTERN_ATTACK.match(action_str)
        if match: return {"action": "ATTACK", "origin": match.group(1).upper(), "target": match.group(2).upper()}

        match = ActionParser.PATTERN_STUN.match(action_str)
        if match: return {"action": "STUN", "origin": match.group(1).upper(), "target": match.group(2).upper()}
            
        match = ActionParser.PATTERN_SPAWN.match(action_str)
        # O nome do Herói/Spell mantém as suas maiúsculas/minúsculas
        if match: return {"action": "SPAWN", "hero": match.group(1), "origin": match.group(2).upper(), "target": match.group(3).upper()}

        match = ActionParser.PATTERN_SPELL.match(action_str)
        if match: return {"action": "SPELL", "spell": match.group(1), "origin": match.group(2).upper(), "target": match.group(3).upper()}
            
        return None

    
    @staticmethod
    def alg_to_coords(alg: str, total_linhas: int) -> tuple[int, int]:
        """Converte Notação Algébrica (Ex: A8) para índices de matriz (linha, coluna)."""
        alg = alg.upper()
        col = ord(alg[0]) - 65
        row = total_linhas - int(alg[1:])
        return (row, col)