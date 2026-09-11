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

O estado implementado não é duplicado num `CURRENT_STATE.md` ou noutro snapshot.

## Entrada operacional

1. [`README.md`](README.md)
2. [`ROADMAP.md`](ROADMAP.md)
3. documento canónico da área
4. [`DECISIONS/`](DECISIONS/) quando a motivação histórica for relevante

## Contratos por domínio

| Área | Fonte canónica |
|---|---|
| Arquitetura | `ARCHITECTURE.md` |
| Regras | `GAME_RULES.md` |
| Design | `GAME_DESIGN.md` |
| Heróis | `HERO_SYSTEM.md` + configuração |
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

## Evidência

`DOCUMENTED` ≠ `IMPLEMENTED` ≠ `TESTED` ≠ `VALIDATED` ≠ `PROVEN`.

## Histórico de decisões

`DECISIONS/` preserva decisões anteriores que possam ser úteis para compreender ou reverter uma escolha. Uma decisão histórica não define o estado atual e não deve duplicar o roadmap ou um contrato atual.
