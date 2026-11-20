# Relatório de Teste de Hipótese Ares AI: H-20261108-ARES-ASPIRATION-PV

## 📌 Sumário da Hipótese
- **ID**: `H-20261108-ARES-ASPIRATION-PV`
- **Título**: Aspiration Windows & PV Ordering vs Shallow Baseline
- **Data**: 2026-11-08 17:34:02
- **Gargalo Observado**: Shallow search horizons without aspiration windows risk tactical blindspots in stun windows.
- **Melhoria Implementada**: Iterative deepening with aspiration window (score +- 60) and PV move ordering bonus.
- **Candidato (*Challenger*)**: `ares-depth2-aspiration-challenger`
- **Campeão Atual (*Baseline*)**: `ares-depth1-baseline`

---

## 📊 Veredito e Resultados Estatísticos
> ### **Decisão Final: ❌ REJEITADO (HIPÓTESE FALSIFICADA)**
> **Justificação**: Sem evidência de melhoria (Score: 25.0%, ΔElo: -190.8).

| Métrica | Valor Obtido |
|---|---|
| **Total de Partidas (Pares Espelhados)** | 4 partidas (2 pares) |
| **Placar (Candidato vs Baseline)** | **+1** / **-3** / =0 |
| **Taxa de Pontuação (Score)** | **25.0%** |
| **Diferença de Elo ($\Delta$ Elo)** | **-190.8** |
| **Margem de Erro (95% CI)** | **± 393.2** |
| **Intervalo de Confiança 95%** | `[-584.0, +202.4]` |
| **Razão de Log-Verossimilhança (LLR)** | **-0.12** (Limites: [-2.94, 2.94]) |
| **Estado SPRT de Wald** | `CONTINUE` |

---

## 🔬 Protocolo Científico Stockfish Aplicado ao RedWar
1. **Duelos Espelhados**: Cada abertura foi jogada de Brancas e de Pretas para eliminar viés de cor.
2. **Modelo Bradley-Terry Binário**: Ausência de empates artificiais de xadrez; a pontuação reflete pura dominância letal por stun.
3. **Proteção Anti-Involução**: O motor campeão só é substituído perante prova estatística conclusiva ($H_1$).
