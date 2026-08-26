"""Generate reproducible combat telemetry for balance/NNUE experiments."""
from __future__ import annotations

import argparse
import json
import os
import random
import subprocess
import sys
import threading
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
DEFAULT_BOT_MOVE_TIMEOUT_SECONDS = 60.0
DEFAULT_OUTPUT = ROOT / "data" / "estatisticas_treino.json"
DEFAULT_DIAGNOSTIC_DIR = ROOT / "logs" / "trainer_failures"
DIAGNOSTIC_TIMEOUT_SECONDS = 15.0


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


def _bot_nodes(bot) -> int | None:
    value = getattr(bot, "nodes", None)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _reset_cpp_bot_process(bot) -> None:
    process = getattr(bot, "process", None)
    if process is None:
        return
    try:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=2)
    except Exception:
        pass
    try:
        bot.process = None
    except Exception:
        pass


def _safe_diagnostic_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in value)[:80] or "bot"


def _capture_cpp_search_diagnostic(
    bot,
    gs: GameState,
    reason: str,
    turn: int,
    elapsed_seconds: float,
) -> Path | None:
    """Re-run one failed C++ search in an isolated process with bounded tracing."""
    exe_path = getattr(bot, "exe_path", None)
    nodes = _bot_nodes(bot)
    if not exe_path or nodes is None:
        return None

    failure_id = f"turn_{turn:03d}_{int(time.time() * 1000)}_{_safe_diagnostic_name(getattr(bot, 'nome', 'bot'))}"
    failure_dir = DEFAULT_DIAGNOSTIC_DIR / failure_id
    failure_dir.mkdir(parents=True, exist_ok=True)
    rwen_path = failure_dir / "position.rwen"
    trace_path = failure_dir / "search_trace.log"
    metadata_path = failure_dir / "metadata.json"
    stdout_path = failure_dir / "engine_stdout.log"
    stderr_path = failure_dir / "engine_stderr.log"
    rwen = gs.to_rwen()
    rwen_path.write_text(rwen + "\n", encoding="utf-8")

    metadata = {
        "reason": reason,
        "bot": getattr(bot, "nome", bot.__class__.__name__),
        "nodes": nodes,
        "turn": turn,
        "elapsed_seconds": round(elapsed_seconds, 6),
        "rwen": rwen,
        "executable": str(exe_path),
        "diagnostic_timeout_seconds": DIAGNOSTIC_TIMEOUT_SECONDS,
        "trace_file": str(trace_path),
    }

    process = None
    stdout_text = ""
    stderr_text = ""
    status = "not_started"
    try:
        if not os.path.exists(exe_path):
            raise FileNotFoundError(exe_path)

        env = os.environ.copy()
        env["ARES_SEARCH_TRACE_PATH"] = str(trace_path.resolve())
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(exe_path)))
        process = subprocess.Popen(
            [exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            cwd=project_root,
            env=env,
        )
        commands = f"isready\nposition rwen {rwen}\ngo nodes {nodes}\n"
        stdout_text, stderr_text = process.communicate(
            commands,
            timeout=DIAGNOSTIC_TIMEOUT_SECONDS,
        )
        status = "completed"
    except subprocess.TimeoutExpired as exc:
        stdout_text = exc.stdout or ""
        stderr_text = exc.stderr or ""
        status = "diagnostic_timeout"
        if process is not None:
            process.kill()
            try:
                tail_stdout, tail_stderr = process.communicate(timeout=2)
                stdout_text += tail_stdout or ""
                stderr_text += tail_stderr or ""
            except Exception:
                pass
    except Exception as exc:
        status = "diagnostic_error"
        stderr_text = f"{type(exc).__name__}: {exc}\n"
    finally:
        if process is not None and process.poll() is None:
            try:
                process.kill()
                process.wait(timeout=2)
            except Exception:
                pass

    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")
    metadata["status"] = status
    metadata["bestmove_seen"] = any(line.startswith("bestmove") for line in stdout_text.splitlines())
    metadata["stdout_lines"] = len(stdout_text.splitlines())
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return failure_dir


def _run_bot_move_with_timeout(bot, gs, timeout_seconds: float):
    result_queue: list[tuple[bool, object]] = []

    def worker() -> None:
        try:
            result_queue.append((True, bot.escolher_jogada(gs)))
        except BaseException as exc:
            result_queue.append((False, exc))

    worker_thread = threading.Thread(
        target=worker,
        name=f"trainer-bot-{getattr(bot, 'nome', 'bot')}",
        daemon=True,
    )
    worker_thread.start()
    worker_thread.join(timeout_seconds)
    if worker_thread.is_alive():
        _reset_cpp_bot_process(bot)
        raise TimeoutError(
            f"Bot '{getattr(bot, 'nome', 'unknown')}' exceeded {timeout_seconds:.1f}s "
            f"for a single move"
        )

    if not result_queue:
        raise RuntimeError(f"Bot '{getattr(bot, 'nome', 'unknown')}' returned without a result")
    ok, payload = result_queue[0]
    if not ok:
        if isinstance(payload, OSError):
            _reset_cpp_bot_process(bot)
        raise payload
    return payload


def simular_jogo_treino(seed: int, bot_move_timeout_seconds: float = DEFAULT_BOT_MOVE_TIMEOUT_SECONDS) -> dict:
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
    invalid_action_nodes = None
    invalid_action_elapsed = None
    diagnostic_dir = None
    engine_time_seconds = 0.0
    while not gs.game_over and turnos < MAX_TURNS_PER_GAME:
        turnos += 1
        active_bot = bot_brancas if gs.white_to_move else bot_pretas
        last_bot_name = getattr(active_bot, "nome", active_bot.__class__.__name__)
        last_bot_nodes = _bot_nodes(active_bot)
        move_start = time.perf_counter()
        try:
            parsed = _run_bot_move_with_timeout(active_bot, gs, bot_move_timeout_seconds)
        except (KeyError, IndexError, TypeError, ValueError, TimeoutError, RuntimeError, OSError) as exc:
            elapsed = time.perf_counter() - move_start
            engine_time_seconds += elapsed
            invalid_action = str(exc)
            invalid_action_bot = last_bot_name
            invalid_action_nodes = last_bot_nodes
            invalid_action_elapsed = elapsed
            diagnostic_dir = _capture_cpp_search_diagnostic(
                active_bot, gs, invalid_action, turnos, elapsed
            )
            _reset_cpp_bot_process(active_bot)
            gs.game_over = True
            gs.winner = "Ação inválida do bot" if not isinstance(exc, TimeoutError) else "Timeout do bot"
            break
        engine_time_seconds += time.perf_counter() - move_start
        if not parsed:
            elapsed = time.perf_counter() - move_start
            _reset_cpp_bot_process(active_bot)
            gs.check_game_over()
            if not gs.game_over:
                gs.game_over, gs.winner = True, "Bloqueio Total"
            invalid_action = "Bot returned no action"
            invalid_action_bot = last_bot_name
            invalid_action_nodes = last_bot_nodes
            invalid_action_elapsed = elapsed
            diagnostic_dir = _capture_cpp_search_diagnostic(
                active_bot, gs, invalid_action, turnos, elapsed
            )
            break
        try:
            executar_acao_treino(gs, parsed)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            invalid_action = str(exc)
            invalid_action_bot = active_bot.nome
            invalid_action_nodes = _bot_nodes(active_bot)
            invalid_action_elapsed = time.perf_counter() - move_start
            diagnostic_dir = _capture_cpp_search_diagnostic(
                active_bot, gs, invalid_action, turnos, invalid_action_elapsed
            )
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
        "engine_time_seconds": round(engine_time_seconds, 6),
    }
    if invalid_action is not None:
        match["invalid_action"] = invalid_action
        match["invalid_action_bot"] = invalid_action_bot
        match["invalid_action_nodes"] = invalid_action_nodes
        match["invalid_action_elapsed_seconds"] = round(invalid_action_elapsed or 0.0, 6)
        if diagnostic_dir is not None:
            match["diagnostic_dir"] = str(diagnostic_dir)
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
    bot_move_timeout_seconds: float = DEFAULT_BOT_MOVE_TIMEOUT_SECONDS,
) -> dict:
    if num_jogos <= 0:
        raise ValueError("num_jogos deve ser positivo")
    if bot_move_timeout_seconds <= 0:
        raise ValueError("bot_move_timeout_seconds deve ser positivo")

    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        output.unlink()
    except FileNotFoundError:
        pass

    print(f"🧠 A gerar metadados de combate ({num_jogos} partidas)...")
    master_rng = random.Random(seed)
    historico_partidas = []
    invalid_matches = 0
    start_time = time.time()

    for index in range(num_jogos):
        result = simular_jogo_treino(
            master_rng.randrange(1, 10**12),
            bot_move_timeout_seconds=bot_move_timeout_seconds,
        )
        if not result["valid"]:
            invalid_matches += 1
            print(
                f"\n⚠️ Partida {index + 1} descartada: "
                f"{result.get('invalid_action_bot', 'unknown')}: "
                f"{result.get('invalid_action', 'unknown')}"
            )
            if result.get("diagnostic_dir"):
                print(f"   🔎 diagnóstico: {result['diagnostic_dir']}")
        historico_partidas.append(result)
        sys.stdout.write(f"\rProgresso: {index + 1}/{num_jogos}")
        sys.stdout.flush()

    stats = {
        "total_matches": num_jogos,
        "valid_matches": num_jogos - invalid_matches,
        "invalid_matches": invalid_matches,
        "seed": seed,
        "max_turns_per_game": MAX_TURNS_PER_GAME,
        "bot_move_timeout_seconds": bot_move_timeout_seconds,
        "diagnostic_dir": str(DEFAULT_DIAGNOSTIC_DIR),
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
    parser.add_argument("--bot-timeout", type=float, default=DEFAULT_BOT_MOVE_TIMEOUT_SECONDS)
    args = parser.parse_args()
    gerar_estatisticas_treino(
        args.jogos,
        args.seed,
        args.output,
        bot_move_timeout_seconds=args.bot_timeout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
