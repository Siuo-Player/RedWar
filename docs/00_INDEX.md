# RedWar — Índice de Documentação

## Autoridade

```text
código + testes executáveis
        ↓
contrato canónico
        ↓
decisão histórica
        ↓
research / proposta
        ↓
roadmap
```

Não existe um `CURRENT_STATE.md`. O estado implementado deve ser obtido do `main`, dos testes e do CI; esta documentação não replica snapshots.

## Entrada operacional

1. [`README.md`](README.md)
2. [`ROADMAP.md`](ROADMAP.md)
3. documento canónico da área
4. [`DECISIONS/`](DECISIONS/) apenas para motivação histórica

## Contratos por domínio

| Área | Fonte canónica |
|---|---|
| Arquitetura | `ARCHITECTURE.md` |
| Regras | `GAME_RULES.md` |
| Design | `GAME_DESIGN.md` |
| Heróis | `HERO_SYSTEM.md` + configuração de engine |
| Ares | `AI_ENGINE.md` |
| NNUE | `NNUE.md` |
| Benchmarks | `AI_BENCHMARK_PROTOCOL.md` |
| Strength | `STRENGTH_EVALUATION.md` |
| Arena | `ARENA_STATISTICAL_METHODOLOGY.md` + `ARENA_HOLDOUT_CI.md` |
| Balanceamento | `BALANCE_METHODOLOGY.md` |
| Observabilidade | `OBSERVABILITY_CONTRACT.md` |
| UI | `BATTLE_UI_SIDEBAR.md` |
| Replay/telemetria | `REPLAY_STORAGE.md` + `TELEMETRY.md` |
| Online | `WEB_MULTIPLAYER.md` |
| Licenças | `LEGAL_AND_LICENSES.md` |

## Estados de evidência

`DOCUMENTED` ≠ `IMPLEMENTED` ≠ `TESTED` ≠ `VALIDATED` ≠ `PROVEN`.

## Decisões históricas

`DECISIONS/` é o arquivo de decisões. Uma decisão antiga pode ser mantida mesmo depois de superseded quando a sua motivação for necessária para compreender uma escolha ou considerar uma reversão.

Não duplicar uma decisão no roadmap, num snapshot ou num relatório de estado.