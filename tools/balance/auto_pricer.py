import argparse
import json
import math
import os
from collections import Counter

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARQUIVO_HEROES = os.path.join(ROOT_DIR, "engine", "heroes_config.json")
ARQUIVO_STATS = os.path.join(ROOT_DIR, "data", "estatisticas_treino.json")

MIN_COST = 5
MAX_COST = 200
ELO_SCALE = 400.0
ADJUSTMENT_K = 50.0
MAX_DRAFT_QUANTITY = 64
MIN_SAMPLES_FOR_ADJUSTMENT = 100


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


def _classificar_falha(match):
    """Preserva a proveniência de resultados descartados sem inferir causalidade."""
    explicit_reason = match.get("failure_reason")
    if isinstance(explicit_reason, str) and explicit_reason.strip():
        return explicit_reason.strip()

    winner = str(match.get("winner", ""))
    if "Timeout" in winner:
        return "timeout"
    if match.get("invalid_action"):
        return "invalid_action"
    if match.get("diagnostic_dir"):
        return "diagnostic_failure"
    return "invalid_unspecified"


def obter_partidas_validas(stats):
    """Filtra partidas válidas e mantém a proveniência dos resultados descartados."""
    matches = stats.get("matches", [])
    if not isinstance(matches, list):
        raise ValueError("Histórico de partidas inválido: 'matches' deve ser uma lista.")

    valid_matches = []
    for index, match in enumerate(matches):
        if not isinstance(match, dict):
            raise ValueError(f"Partida inválida no histórico no índice {index}: esperado objeto JSON.")
        if "valid" not in match or not isinstance(match["valid"], bool):
            raise ValueError(
                f"Partida {index} sem proveniência explícita: 'valid' deve ser booleano."
            )
        if match["valid"]:
            valid_matches.append(match)
    return valid_matches


def obter_proveniencia_invalidas(stats):
    """Resume razões explícitas das observações excluídas do cálculo."""
    matches = stats.get("matches", [])
    if not isinstance(matches, list):
        raise ValueError("Histórico de partidas inválido: 'matches' deve ser uma lista.")

    counts = Counter()
    for index, match in enumerate(matches):
        if not isinstance(match, dict):
            raise ValueError(f"Partida inválida no histórico no índice {index}: esperado objeto JSON.")
        if "valid" not in match or not isinstance(match["valid"], bool):
            raise ValueError(
                f"Partida {index} sem proveniência explícita: 'valid' deve ser booleano."
            )
        if not match["valid"]:
            counts[_classificar_falha(match)] += 1
    return dict(sorted(counts.items()))


def _validar_draft(draft, lado):
    if not isinstance(draft, dict):
        raise ValueError(f"Draft inválido para {lado}: esperado objeto JSON.")
    for peca, qtd in draft.items():
        if not isinstance(qtd, int) or isinstance(qtd, bool):
            raise ValueError(f"Quantidade inválida para {lado}/{peca}: {qtd!r}")
        if qtd < 0 or qtd > MAX_DRAFT_QUANTITY:
            raise ValueError(
                f"Quantidade fora de gama para {lado}/{peca}: {qtd!r} "
                f"(0..{MAX_DRAFT_QUANTITY})"
            )


def calcular_balanceamento(stats, heroes):
    """Calcula propostas heurísticas de preço sem pretender estimar poder causal."""
    if not isinstance(stats, dict) or not isinstance(heroes, dict):
        raise ValueError("Stats e configuração de heróis devem ser objetos JSON.")

    custos_atuais = {name: data.get("cost", 0) for name, data in heroes.items()}
    valid_matches = obter_partidas_validas(stats)
    total_matches = len(stats.get("matches", []))
    invalid_count = total_matches - len(valid_matches)
    invalid_provenance = obter_proveniencia_invalidas(stats)

    if not valid_matches:
        raise ValueError("Nenhuma partida válida disponível para balanceamento.")

    piece_score_delta = {peca: 0.0 for peca in custos_atuais}
    piece_volume = {peca: 0 for peca in custos_atuais}

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

        _validar_draft(w_draft, "white")
        _validar_draft(b_draft, "black")

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

    changes = []
    for peca in custos_atuais:
        if piece_volume[peca] == 0:
            continue

        custo_antigo = int(custos_atuais[peca])
        samples = piece_volume[peca]
        media_delta = piece_score_delta[peca] / samples
        eligible = samples >= MIN_SAMPLES_FOR_ADJUSTMENT
        ajuste = int(round(media_delta * ADJUSTMENT_K)) if eligible else 0
        novo_custo = max(MIN_COST, min(MAX_COST, custo_antigo + ajuste))
        changes.append(
            {
                "hero": peca,
                "samples": samples,
                "performance_delta": media_delta,
                "old_cost": custo_antigo,
                "new_cost": novo_custo,
                "eligible_for_adjustment": eligible,
                "changed": eligible and novo_custo != custo_antigo,
            }
        )

    return {
        "method": "elo_adjusted_occurrence_heuristic",
        "interpretation": "diagnostic_pricing_heuristic_not_causal_power_estimate",
        "total_matches": total_matches,
        "valid_matches": len(valid_matches),
        "invalid_matches": invalid_count,
        "invalid_provenance": invalid_provenance,
        "min_cost": MIN_COST,
        "max_cost": MAX_COST,
        "adjustment_k": ADJUSTMENT_K,
        "max_draft_quantity": MAX_DRAFT_QUANTITY,
        "min_samples_for_adjustment": MIN_SAMPLES_FOR_ADJUSTMENT,
        "changes": changes,
    }


def executar_balanceamento_automatico(escrever_config=True, caminho_relatorio=None):
    print("📈 A executar heurística de pricing ajustada por ELO...")

    if not os.path.exists(ARQUIVO_STATS):
        raise FileNotFoundError("Ficheiro estatisticas_treino.json não encontrado.")

    with open(ARQUIVO_STATS, "r", encoding="utf-8") as f:
        stats = json.load(f)

    with open(ARQUIVO_HEROES, "r", encoding="utf-8") as f:
        heroes = json.load(f)

    relatorio = calcular_balanceamento(stats, heroes)
    print(
        f"🧪 Telemetria: {relatorio['valid_matches']} partidas válidas, "
        f"{relatorio['invalid_matches']} descartadas com proveniência explícita."
    )
    if relatorio["invalid_provenance"]:
        print(f"   Motivos: {relatorio['invalid_provenance']}")

    mudancas = False
    print("\n📊 Diagnóstico heurístico de pricing por ELO")
    print("-" * 76)

    for change in relatorio["changes"]:
        peca = change["hero"]
        custo_antigo = change["old_cost"]
        novo_custo = change["new_cost"]
        media_delta = change["performance_delta"]
        samples = change["samples"]
        if change["changed"]:
            mudancas = True
            sinal = "+" if media_delta > 0 else ""
            estado = "🔴 NERFADA" if media_delta > 0 else "🟢 BUFFADA"
            print(
                f"{peca.ljust(12)} | N={samples:.0f} | Performance: {sinal}{media_delta * 100:.1f}% | "
                f"{custo_antigo} -> {novo_custo} ({estado})"
            )
        elif not change["eligible_for_adjustment"]:
            print(
                f"{peca.ljust(12)} | N={samples:.0f} | Performance: {media_delta * 100:+.1f}% | "
                f"{custo_antigo} (Sem amostra suficiente; mínimo {MIN_SAMPLES_FOR_ADJUSTMENT})"
            )
        else:
            print(
                f"{peca.ljust(12)} | N={samples:.0f} | Performance: {media_delta * 100:+.1f}% | "
                f"{custo_antigo} (Estável)"
            )

    if mudancas:
        for change in relatorio["changes"]:
            if change["changed"]:
                heroes[change["hero"]]["cost"] = change["new_cost"]
        if escrever_config:
            with open(ARQUIVO_HEROES, "w", encoding="utf-8") as f:
                json.dump(heroes, f, indent=4, ensure_ascii=False)
            print("\n✅ heroes_config.json atualizado.")
        else:
            print("\nℹ️ Alterações calculadas, mas escrita de heroes_config.json desativada.")
    else:
        print("\n✅ Nenhum preço elegível requer alteração.")

    if caminho_relatorio:
        caminho_relatorio = os.path.abspath(caminho_relatorio)
        os.makedirs(os.path.dirname(caminho_relatorio), exist_ok=True)
        with open(caminho_relatorio, "w", encoding="utf-8") as f:
            json.dump(relatorio, f, indent=4, ensure_ascii=False)
        print(f"📄 Relatório escrito em: {caminho_relatorio}")

    return relatorio


def main():
    parser = argparse.ArgumentParser(description="Calcula e opcionalmente aplica preços heurísticos de heróis.")
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Calcula os preços sem modificar engine/heroes_config.json.",
    )
    parser.add_argument(
        "--report",
        metavar="PATH",
        help="Escreve o relatório JSON das alterações propostas.",
    )
    args = parser.parse_args()
    executar_balanceamento_automatico(
        escrever_config=not args.no_write,
        caminho_relatorio=args.report,
    )


if __name__ == "__main__":
    main()
