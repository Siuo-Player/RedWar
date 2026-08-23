"""Headless A/B Arena for two explicit RedWar C++ engines."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.bot import CppEngineBot
from engine.game_state import GameState
from tools.analytics.opening_book import carregar_abertura_do_book


def verificar_promocao(vitorias_desafiante: int, vitorias_atual: int, margem: int = 10) -> bool:
    return vitorias_desafiante - vitorias_atual >= margem


def run_headless_match(bot_brancas, bot_pretas, opening_index: int = 0):
    gs = GameState(time_limit_seconds=99999)
    seed = carregar_abertura_do_book(gs, opening_index)

    turnos = 0
    while not gs.game_over and turnos < 200:
        turnos += 1
        bot = bot_brancas if gs.white_to_move else bot_pretas
        best_move = bot.play(gs)
        if best_move:
            gs.execute_action(best_move)
        else:
            gs.check_game_over()
            if not gs.game_over:
                gs.game_over, gs.winner = True, "Bloqueio"
            break
    return gs.winner, seed


def start_tournament(
    challenger_engine: str,
    baseline_engine: str,
    num_games: int,
    win_threshold: int,
    nodes: int,
) -> int:
    print(
        f"⚔️ A INICIAR A/B ARENA: {num_games} JOGOS "
        f"(margem exigida: {win_threshold}, nodes: {nodes})"
    )
    print(f"Challenger: {challenger_engine}")
    print(f"Baseline:   {baseline_engine}")

    wins_challenger = wins_baseline = draws = 0
    challenger = CppEngineBot(nodes=nodes, executable_path=challenger_engine)
    baseline = CppEngineBot(nodes=nodes, executable_path=baseline_engine)

    try:
        for i in range(num_games):
            opening_index = i % 16
            if i % 2 == 0:
                winner, seed = run_headless_match(challenger, baseline, opening_index)
                if winner and "Brancas" in str(winner):
                    wins_challenger += 1
                elif winner and "Pretas" in str(winner):
                    wins_baseline += 1
                else:
                    draws += 1
            else:
                winner, seed = run_headless_match(baseline, challenger, opening_index)
                if winner and "Pretas" in str(winner):
                    wins_challenger += 1
                elif winner and "Brancas" in str(winner):
                    wins_baseline += 1
                else:
                    draws += 1

            sys.stdout.write(
                f"\rJogos completados: {i + 1}/{num_games} (seed {seed})"
            )
            sys.stdout.flush()

        diferenca = wins_challenger - wins_baseline
        win_rate = wins_challenger / max(1, num_games) * 100.0
        promoted = verificar_promocao(wins_challenger, wins_baseline, win_threshold)

        print(
            f"\n\nResultados: Challenger {wins_challenger} | "
            f"Baseline {wins_baseline} | Empates {draws}"
        )
        print(f"Taxa de Vitória do Challenger: {win_rate:.2f}%")
        print(f"Margem Challenger-Baseline: {diferenca:+d}")
        if promoted:
            print(
                f"👑 SUCESSO: Challenger superou a baseline por >= {win_threshold} vitórias."
            )
            return 0

        print(
            f"❌ FALHA: Challenger não atingiu a margem de {win_threshold} vitórias."
        )
        return 1
    finally:
        # Explicitly terminate both engine processes even on a failed game.
        for bot in (challenger, baseline):
            bot.__del__()


def main() -> int:
    parser = argparse.ArgumentParser(description="A/B Arena entre duas engines RedWar")
    parser.add_argument("--challenger-engine", required=True)
    parser.add_argument("--baseline-engine", required=True)
    parser.add_argument("--jogos", type=int, default=100)
    parser.add_argument("--margem-vitorias", type=int, default=10)
    parser.add_argument("--nodes", type=int, default=10_000)
    args = parser.parse_args()

    return start_tournament(
        challenger_engine=args.challenger_engine,
        baseline_engine=args.baseline_engine,
        num_games=args.jogos,
        win_threshold=args.margem_vitorias,
        nodes=args.nodes,
    )


if __name__ == "__main__":
    raise SystemExit(main())
