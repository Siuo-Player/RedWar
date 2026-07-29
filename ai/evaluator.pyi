# ai/evaluator.pyi
from typing import Any

def obter_bonus_posicional(piece: Any, r: int, c: int) -> int: ...
def avaliador_mestre(gs: Any) -> int: ...

avaliador_guloso = avaliador_mestre
avaliador_estrategico = avaliador_mestre