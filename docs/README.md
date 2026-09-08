# RedWar — Documentação

A documentação segue uma regra simples: **não há múltiplos roadmaps nem múltiplos estados operacionais**.

## Entrada recomendada

A entrada operacional deve seguir esta ordem:

```text
00_INDEX.md
  ↓
CURRENT_STATE.md
  ↓
ROADMAP.md
  ↓
documento canónico do domínio
  ↓
PROJECT_REASONING.md (rationale transversal, quando necessário)
  ↓
DECISIONS/ (rationale histórico, quando necessário)
```

`00_INDEX.md` é o mapa da autoridade; não é substituído por snapshots ou handoffs.

## Principais documentos

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — fronteiras e invariantes do sistema.
- [`GAME_RULES.md`](GAME_RULES.md) — regras operacionais.
- [`GAME_DESIGN.md`](GAME_DESIGN.md) — intenção de design.
- [`HERO_SYSTEM.md`](HERO_SYSTEM.md) — contrato do sistema de heróis.
- [`AI_ENGINE.md`](AI_ENGINE.md) — Ares.
- [`NNUE.md`](NNUE.md) — avaliação NNUE.
- [`AI_BENCHMARK_PROTOCOL.md`](AI_BENCHMARK_PROTOCOL.md) — capability/regression benchmarks.
- [`STRENGTH_EVALUATION.md`](STRENGTH_EVALUATION.md) — strength/Arena.
- [`ARENA_STATISTICAL_METHODOLOGY.md`](ARENA_STATISTICAL_METHODOLOGY.md) — estatística.
- [`ARENA_HOLDOUT_CI.md`](ARENA_HOLDOUT_CI.md) — hold-out.
- [`BALANCE_METHODOLOGY.md`](BALANCE_METHODOLOGY.md) — balanceamento.
- [`OBSERVABILITY_CONTRACT.md`](OBSERVABILITY_CONTRACT.md) — informação legal por modo.
- [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md) — cobertura cross-backend.
- [`BATTLE_UI_SIDEBAR.md`](BATTLE_UI_SIDEBAR.md) — UI de batalha.
- [`WEB_MULTIPLAYER.md`](WEB_MULTIPLAYER.md) — online.

## Autoridade

Para **comportamento existente**, a prioridade é:

```text
implementação + testes executáveis
→ documento canónico
→ decisão histórica
→ research/audit
→ roadmap/proposta
→ snapshot histórico
```

Para **ordem de desenvolvimento**, a autoridade é exclusivamente [`ROADMAP.md`](ROADMAP.md).

Para **raciocínio transversal**, consultar [`PROJECT_REASONING.md`](PROJECT_REASONING.md), sem o tratar como segundo roadmap.

`DECISIONS/` é histórico; não se reescreve para alterar a narrativa posterior.
