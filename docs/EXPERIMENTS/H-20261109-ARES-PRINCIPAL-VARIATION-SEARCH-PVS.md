# Relatório de Teste de Hipótese Ares AI: H-20261109-ARES-PRINCIPAL-VARIATION-SEARCH-PVS

## 📌 Sumário da Hipótese
- **ID**: `H-20261109-ARES-PRINCIPAL-VARIATION-SEARCH-PVS`
- **Título**: Principal Variation Search (PVS) with Zero-Window Scouting
- **Data**: 2026-11-09 00:16:59
- **Gargalo Observado**: Standard alpha-beta evaluates all non-PV moves with the full [alpha, beta] window, causing unnecessary tree branching and shallow search horizons.
- **Melhoria Implementada**: PVS scouts all non-PV moves with a zero-window [-alpha-1, -alpha] to force rapid beta-cutoffs, only re-searching with full window when a move fails high.
- **Candidato (*Challenger*)**: `ares-d2-pvs-on`
- **Campeão Atual (*Baseline*)**: `ares-d2-pvs-off`

---

## 📊 Veredito e Resultados Estatísticos
> ### **Decisão Final: ❌ REJEITADO (HIPÓTESE FALSIFICADA)**
> **Justificação**: Sem evidência de melhoria (Score: 25.0%, ΔElo: -190.8).

| Métrica | Valor Obtido |
|---|---|
| **Total de Partidas (Pares Espelhados)** | 8 partidas (4 pares) |
| **Placar (Candidato vs Baseline)** | **+1** / **-5** / =2 |
| **Taxa de Pontuação (Score)** | **25.0%** |
| **Diferença de Elo ($\Delta$ Elo)** | **-190.8** |
| **Margem de Erro (95% CI)** | **± 227.0** (`[-417.8, +36.2]`, 1.96σ) |
| **Portão de Campeão (99.73% CI)** | **± 347.4** (`[-538.2, +156.6]`, 3.0σ) |
| **Status do Portão 3-Sigma** | `⏳ PENDENTE / NÃO ATINGIDO` |
| **Razão de Log-Verossimilhança (LLR)** | **-0.36** (Limites: [-2.94, 2.94]) |
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
