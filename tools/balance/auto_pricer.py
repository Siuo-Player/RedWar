# tools/balance/auto_pricer.py
import json
import math
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARQUIVO_HEROES = os.path.join(ROOT_DIR, "engine", "heroes_config.json")
ARQUIVO_STATS = os.path.join(ROOT_DIR, "data", "estatisticas_treino.json")

MIN_COST = 5
MAX_COST = 200
ELO_SCALE = 400.0
ADJUSTMENT_K = 50.0


def calcular_win_esperada(elo_a, elo_b):
    """Retorna a probabilidade de vitória de A sobre B sem overflow numérico."""
    try:
        elo_a = float(elo_a)
        elo_b = float(elo_b)
    except (TypeError, ValueError) as exc:
        raise ValueError("ELO deve ser numérico") from exc

    if not math.isfinite(elo_a) or not math.isfinite(elo_b):
        raise ValueError("ELO deve ser finito")

    x = (elo_b - elo_a) / ELO_SCALE
    if x >= 50.0:
        return 0.0
    if x <= -50.0:
        return 1.0
    return 1.0 / (1.0 + math.pow(10.0, x))


def obter_partidas_validas(stats):
    """Filtra partidas descartadas pelo trainer sem alterar o histórico original."""
    matches = stats.get("matches", [])
    return [match for match in matches if match.get("valid", True)]


def executar_balanceamento_automatico():
    print("📈 A executar Avaliação Económica Ponderada por ELO...")

    if not os.path.exists(ARQUIVO_STATS):
        print("❌ Ficheiro estatisticas_treino.json não encontrado.")
        return

    with open(ARQUIVO_STATS, "r", encoding="utf-8") as f:
        stats = json.load(f)

    with open(ARQUIVO_HEROES, "r", encoding="utf-8") as f:
        heroes = json.load(f)

    custos_atuais = {name: data.get("cost", 0) for name, data in heroes.items()}

    valid_matches = obter_partidas_validas(stats)
    total_matches = len(stats.get("matches", []))
    invalid_count = total_matches - len(valid_matches)

    print(
        f"🧪 Telemetria: {len(valid_matches)} partidas válidas, "
        f"{invalid_count} descartadas por ação inválida."
    )

    if not valid_matches:
        print("❌ Nenhuma partida válida disponível para balanceamento.")
        return

    piece_score_delta = {peca: 0.0 for peca in custos_atuais}
    piece_volume = {peca: 0.0 for peca in custos_atuais}

    for match in valid_matches:
        try:
            w_elo = match["white_elo"]
            b_elo = match["black_elo"]
            w_draft = match["white_draft"]
            b_draft = match["black_draft"]
            result = float(match["result"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Partida inválida no histórico: {match!r}") from exc

        if result not in (0.0, 0.5, 1.0):
            raise ValueError(f"Resultado inválido no histórico: {result!r}")

        e_white = calcular_win_esperada(w_elo, b_elo)
        e_black = 1.0 - e_white
        delta_white = result - e_white
        delta_black = (1.0 - result) - e_black

        for peca, qtd in w_draft.items():
            if peca in piece_score_delta:
                piece_score_delta[peca] += delta_white * qtd
                piece_volume[peca] += qtd

        for peca, qtd in b_draft.items():
            if peca in piece_score_delta:
                piece_score_delta[peca] += delta_black * qtd
                piece_volume[peca] += qtd

    mudancas = False
    print("\n📊 Análise de Performance Absoluta (Impacto sobre ELO Base)")
    print("-" * 65)

    for peca in custos_atuais:
        if piece_volume[peca] == 0:
            continue

        custo_antigo = int(custos_atuais[peca])
        media_delta = piece_score_delta[peca] / piece_volume[peca]
        ajuste = int(round(media_delta * ADJUSTMENT_K))
        novo_custo = max(MIN_COST, min(MAX_COST, custo_antigo + ajuste))

        if novo_custo != custo_antigo:
            custos_atuais[peca] = novo_custo
            heroes[peca]["cost"] = novo_custo
            mudancas = True
            sinal = "+" if media_delta > 0 else ""
            estado = "🔴 NERFADA" if media_delta > 0 else "🟢 BUFFADA"
            print(
                f"{peca.ljust(12)} | Performance: {sinal}{media_delta * 100:.1f}% | "
                f"{custo_antigo} -> {novo_custo} ({estado})"
            )
        else:
            print(
                f"{peca.ljust(12)} | Performance: {media_delta * 100:+.1f}% | "
                f"{custo_antigo} (Estável)"
            )

    if mudancas:
        with open(ARQUIVO_HEROES, "w", encoding="utf-8") as f:
            json.dump(heroes, f, indent=4, ensure_ascii=False)
        print("\n✅ heroes_config.json atualizado com precisão matemática!")
    else:
        print("\n✅ Preços perfeitamente equilibrados. Sem mudanças.")


if __name__ == "__main__":
    executar_balanceamento_automatico()
