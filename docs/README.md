# RedWar — Documentação

A documentação segue uma regra simples: **não há múltiplos roadmaps nem múltiplos estados operacionais**.

## Entrada recomendada

1. [`00_INDEX.md`](00_INDEX.md)
2. [`PROJECT_REASONING.md`](PROJECT_REASONING.md)
3. [`CURRENT_STATE.md`](CURRENT_STATE.md)
4. [`ROADMAP.md`](ROADMAP.md)
5. documento canónico do domínio da tarefa

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

Para comportamento existente, a prioridade é:

```text
implementação + testes executáveis
→ documento canónico
→ decisão histórica
→ research/audit
→ roadmap/proposta
```

Para **ordem de desenvolvimento**, a autoridade é exclusivamente [`ROADMAP.md`](ROADMAP.md).

Para **raciocínio transversal**, a autoridade é [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

`DECISIONS/` é histórico; não se reescreve para alterar a narrativa posterior.
