"""Generate reproducible combat telemetry for balance/NNUE experiments."""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.bot import BOT_ALEATORIO, TREINO_AVANCADO, TREINO_INICIANTE, TREINO_INTERMEDIO
from engine.config import COLUNAS, LINHAS, ORCAMENTO_BRANCAS, ORCAMENTO_PRETAS
from engine.game_state import GameState
from engine.pieces import obter_catalogo_pecas

POOL_BOTS = [
    (BOT_ALEATORIO, 100),
    (TREINO_INICIANTE, 900),
    (TREINO_INTERMEDIO, 1500),
    (TREINO_AVANCADO, 2000),
]
MAX_TURNS_PER_GAME = 200
DEFAULT_OUTPUT = ROOT / "data" / "estatisticas_treino.json"


def formatar_tempo(segundos: float) -> str:
    segundos = max(0, int(segundos))
    dias = segundos // 86400
    horas = (segundos % 86400) // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    parts = []
    if dias:
        parts.append(f"{dias}d")
    if horas:
        parts.append(f"{horas}h")
    if minutos:
        parts.append(f"{minutos}m")
    parts.append(f"{segs}s")
    return " ".join(parts)


def preencher_draft_aleatorio(gs, team, linhas_validas, orcamento, rng) -> dict[str, int]:
    pontos = int(orcamento)
    catalogo = obter_catalogo_pecas()
    composicao = Counter()

    for row in linhas_validas:
        for col in range(COLUNAS):
            validas = [item for item in catalogo if item["cost"] <= pontos]
            if not validas:
                break
            escolha = rng.choice(validas)
            gs.board[row][col] = escolha["class"](team)
            pontos -= int(escolha["cost"])
            composicao[escolha["name"]] += 1

    return dict(composicao)


def executar_acao_treino(gs, parsed):
    if not isinstance(parsed, dict):
        raise ValueError("Bot returned a non-dict action")

    try:
        m_type = str(parsed["type"]).lower()
        start_r, start_c = parsed["start"]
        end_r, end_c = parsed["end"]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Malformed bot action") from exc

    if m_type == "stun":
        attacker = gs.board[start_r][start_c]
        area_stun = parsed.get("area", [])
        if not area_stun and attacker:
            valid_stuns = attacker.get_valid_stuns(
                start_r, start_c, gs.board, gs.tile_effects
            )
            if valid_stuns and (end_r, end_c) in valid_stuns:
                area_stun = valid_stuns[(end_r, end_c)].get("aoe", [])
        gs.make_action(
            (start_r, start_c),
            (end_r, end_c),
            "stun",
            affected_area=area_stun,
        )
    elif m_type == "spawn":
        gs.make_action(
            (start_r, start_c),
            (end_r, end_c),
            "spawn",
            spawn_name=parsed.get("spawn_name"),
        )
    elif m_type == "spell":
        gs.make_action(
            (start_r, start_c),
            (end_r, end_c),
            "spell",
            spell_name=parsed.get("spell_name"),
        )
    elif m_type in {"move", "attack"}:
        gs.make_action((start_r, start_c), (end_r, end_c), m_type)
    else:
        raise ValueError(f"Unknown action type: {m_type!r}")


def simular_jogo_treino(seed: int) -> dict:
    rng = random.Random(seed)
    gs = GameState(time_limit_seconds=99999)
    bot_brancas, elo_brancas = rng.choice(POOL_BOTS)
    bot_pretas, elo_pretas = rng.choice(POOL_BOTS)
    comp_pretas = preencher_draft_aleatorio(
        gs, "pretas", [0, 1], ORCAMENTO_PRETAS, rng
    )
    comp_brancas = preencher_draft_aleatorio(
        gs, "brancas", [LINHAS - 2, LINHAS - 1], ORCAMENTO_BRANCAS, rng
    )

    turnos = 0
    invalid_action = None
    invalid_action_bot = None
    while not gs.game_over and turnos < MAX_TURNS_PER_GAME:
        turnos += 1
        active_bot = bot_brancas if gs.white_to_move else bot_pretas
        parsed = active_bot.escolher_jogada(gs)
        if not parsed:
            gs.check_game_over()
            if not gs.game_over:
                gs.game_over, gs.winner = True, "Bloqueio Total"
            break
        try:
            executar_acao_treino(gs, parsed)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            invalid_action = str(exc)
            invalid_action_bot = active_bot.nome
            gs.game_over = True
            gs.winner = "Ação inválida do bot"
            break

    if not gs.game_over:
        gs.game_over = True
        gs.winner = f"Empate ({MAX_TURNS_PER_GAME} turnos)"

    result = 0.5
    if invalid_action is None:
        if "Brancas" in str(gs.winner):
            result = 1.0
        elif "Pretas" in str(gs.winner):
            result = 0.0

    match = {
        "white_elo": elo_brancas,
        "black_elo": elo_pretas,
        "white_draft": comp_brancas,
        "black_draft": comp_pretas,
        "result": result,
        "valid": invalid_action is None,
        "turns": turnos,
    }
    if invalid_action is not None:
        match["invalid_action"] = invalid_action
        match["invalid_action_bot"] = invalid_action_bot
    return match


def _atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    temp_path.replace(path)


def gerar_estatisticas_treino(
    num_jogos: int = 200,
    seed: int | None = None,
    output: Path = DEFAULT_OUTPUT,
) -> dict:
    if num_jogos <= 0:
        raise ValueError("num_jogos deve ser positivo")

    print(f"🧠 A gerar metadados de combate ({num_jogos} partidas)...")
    master_rng = random.Random(seed)
    historico_partidas = []
    invalid_matches = 0
    start_time = time.time()

    for index in range(num_jogos):
        result = simular_jogo_treino(master_rng.randrange(1, 10**12))
        if not result["valid"]:
            invalid_matches += 1
            print(
                f"\n⚠️ Partida {index + 1} descartada: "
                f"{result.get('invalid_action_bot', 'unknown')}: "
                f"{result.get('invalid_action', 'unknown')}"
            )
        historico_partidas.append(result)
        sys.stdout.write(f"\rProgresso: {index + 1}/{num_jogos}")
        sys.stdout.flush()

    stats = {
        "total_matches": num_jogos,
        "valid_matches": num_jogos - invalid_matches,
        "invalid_matches": invalid_matches,
        "seed": seed,
        "max_turns_per_game": MAX_TURNS_PER_GAME,
        "matches": historico_partidas,
    }
    _atomic_write_json(output, stats)

    elapsed = time.time() - start_time
    print(
        f"\n✅ {output} atualizado em {elapsed / 60:.1f} minutos "
        f"({stats['valid_matches']} válidas, {invalid_matches} inválidas)."
    )
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera telemetria reproduzível para RedWar")
    parser.add_argument("--jogos", type=int, default=200)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    gerar_estatisticas_treino(args.jogos, args.seed, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
