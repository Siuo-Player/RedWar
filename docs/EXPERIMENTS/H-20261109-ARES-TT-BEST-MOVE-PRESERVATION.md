# Relatório de Teste de Hipótese Ares AI: H-20261109-ARES-TT-BEST-MOVE-PRESERVATION

## 📌 Sumário da Hipótese
- **ID**: `H-20261109-ARES-TT-BEST-MOVE-PRESERVATION`
- **Título**: Stockfish Transposition Table Best Move Retention on Fail-Lows
- **Data**: 2026-11-09 11:57:14
- **Gargalo Observado**: When a node fails low (UPPERBOUND), best_move is None, erasing the valid best_move from shallower iterations and blinding future move ordering.
- **Melhoria Implementada**: Preserve existing best_move if new search has best_move=None on same-hash TT updates, keeping PV/TT move ordering informed across iterations.
- **Candidato (*Challenger*)**: `ares-d2-enable_tt_move_retention-on`
- **Campeão Atual (*Baseline*)**: `ares-d2-enable_tt_move_retention-off`

---

## 📊 Veredito e Resultados Estatísticos
> ### **Decisão Final: ⏳ INCONCLUSIVO (CONTINUAR)**
> **Justificação**: Tendência positiva (+43.7 Elo), mas requer mais partidas para confirmação formal (CI95%: [-183.0, 270.4], 3σ: [-303.3, 390.7]).

| Métrica | Valor Obtido |
|---|---|
| **Total de Partidas (Pares Espelhados)** | 8 partidas (4 pares) |
| **Placar (Candidato vs Baseline)** | **+4** / **-3** / =1 |
| **Taxa de Pontuação (Score)** | **56.2%** |
| **Diferença de Elo ($\Delta$ Elo)** | **+43.7** |
| **Margem de Erro (95% CI)** | **± 226.7** (`[-183.0, +270.4]`, 1.96σ) |
| **Portão de Campeão (99.73% CI)** | **± 347.0** (`[-303.3, +390.7]`, 3.0σ) |
| **Status do Portão 3-Sigma** | `⏳ PENDENTE / NÃO ATINGIDO` |
| **Razão de Log-Verossimilhança (LLR)** | **+0.04** (Limites: [-2.94, 2.94]) |
| **Estado SPRT de Wald** | `CONTINUE` |

---

## 🔬 Protocolo Científico Stockfish & Governança de Sigmas
1. **Duelos Espelhados**: Cada abertura foi jogada de Brancas e de Pretas para eliminar viés de cor e assimetrias de tabuleiro.
2. **Modelo Bradley-Terry Binário**: Ausência de empates artificiais de xadrez; a pontuação reflete pura dominância tática por stun.
3. **Por que 3-Sigma ($3\sigma$) e não 5-Sigma ($5\sigma$)?**:
   - No CERN/LHC, $5\sigma$ ($p < 3 \times 10^{-7}$) é obrigatório devido ao *Look-Elsewhere Effect* (varredura de milhões de canais energéticos).
   - Em motores de jogo, requerer $5\sigma$ aumentaria o número de partidas necessárias por $(5.0/1.96)^2 \approx 6.5\times$, gerando fadiga amostral extrema e alto erro Tipo II (rejeição de melhorias reais de +3 Elo).
   - O padrão **3-Sigma ($3\sigma$, 99.73% de confiança, $p < 0.0027$)** é o ponto ideal da engenharia de alta confiabilidade (*Six Sigma*), garantindo que a probabilidade de um falso positivo na promoção de um campeão seja inferior a 0.14%.
4. **Proteção Anti-Involução**: O motor campeão só é substituído perante prova estatística conclusiva ($H_1$ ou $3\sigma$ com limite inferior positivo).
