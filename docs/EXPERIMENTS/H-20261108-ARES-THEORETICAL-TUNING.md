# Relatório de Teste de Hipótese Ares AI: H-20261108-ARES-THEORETICAL-TUNING

## 📌 Sumário da Hipótese
- **ID**: `H-20261108-ARES-THEORETICAL-TUNING`
- **Título**: Theoretical Search & Domain Tuning with 3-Sigma Champion Gate
- **Data**: 2026-11-08 18:59:07
- **Gargalo Observado**: Static aspiration windows, flat stun horizon evaluation, and unaged history heuristics risk tactical blunders.
- **Melhoria Implementada**: Dynamic geometric aspiration widening (delta=75.0), distance-decay stun lethality, history gravity aging, adaptive NMP (R=3 at d>=6), and LMR killer protection.
- **Candidato (*Challenger*)**: `ares-theoretically-tuned-d2`
- **Campeão Atual (*Baseline*)**: `ares-depth1-baseline`

---

## 📊 Veredito e Resultados Estatísticos
> ### **Decisão Final: ❌ REJEITADO (HIPÓTESE FALSIFICADA)**
> **Justificação**: Sem evidência de melhoria (Score: 50.0%, ΔElo: -0.0).

| Métrica | Valor Obtido |
|---|---|
| **Total de Partidas (Pares Espelhados)** | 8 partidas (4 pares) |
| **Placar (Candidato vs Baseline)** | **+4** / **-4** / =0 |
| **Taxa de Pontuação (Score)** | **50.0%** |
| **Diferença de Elo ($\Delta$ Elo)** | **+-0.0** |
| **Margem de Erro (95% CI)** | **± 240.8** (`[-240.8, +240.8]`, 1.96σ) |
| **Portão de Campeão (99.73% CI)** | **± 368.5** (`[-368.5, +368.5]`, 3.0σ) |
| **Status do Portão 3-Sigma** | `⏳ PENDENTE / NÃO ATINGIDO` |
| **Razão de Log-Verossimilhança (LLR)** | **-0.01** (Limites: [-2.94, 2.94]) |
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
