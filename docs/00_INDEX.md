# RedWar Documentation Index

## Como reconstruir o projeto sem a conversa

A ordem operacional é:

1. [`README.md`](README.md)
2. [`PROJECT_REASONING.md`](PROJECT_REASONING.md) — eixo de raciocínio transversal
3. [`CURRENT_STATE.md`](CURRENT_STATE.md) — fotografia verificável do baseline
4. [`ROADMAP.md`](ROADMAP.md) — única sequência de trabalho
5. documento canónico do domínio da tarefa
6. `DECISIONS/` apenas para recuperar a razão histórica relevante

`PROJECT_REASONING.md` explica **por que** a ordem existe. `ROADMAP.md` diz **o que vem a seguir**. Os documentos de domínio dizem **qual é o contrato**.

## Documentos canónicos por domínio

| Área | Fonte de verdade operacional |
|---|---|
| Arquitetura | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| Regras | [`GAME_RULES.md`](GAME_RULES.md) |
| Design | [`GAME_DESIGN.md`](GAME_DESIGN.md) |
| Heróis | [`HERO_SYSTEM.md`](HERO_SYSTEM.md) + `engine/heroes_config.json` |
| Ares | [`AI_ENGINE.md`](AI_ENGINE.md) |
| NNUE | [`NNUE.md`](NNUE.md) |
| Benchmarks | [`AI_BENCHMARK_PROTOCOL.md`](AI_BENCHMARK_PROTOCOL.md) |
| Strength | [`STRENGTH_EVALUATION.md`](STRENGTH_EVALUATION.md) |
| Arena estatística | [`ARENA_STATISTICAL_METHODOLOGY.md`](ARENA_STATISTICAL_METHODOLOGY.md) |
| Hold-out | [`ARENA_HOLDOUT_CI.md`](ARENA_HOLDOUT_CI.md) |
| Balanceamento | [`BALANCE_METHODOLOGY.md`](BALANCE_METHODOLOGY.md) |
| Observabilidade | [`OBSERVABILITY_CONTRACT.md`](OBSERVABILITY_CONTRACT.md) |
| Traceability | [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md) |
| CI | [`CI_WORKFLOW_METHODOLOGY.md`](CI_WORKFLOW_METHODOLOGY.md) |
| Desenvolvimento | [`PROJECT_DEVELOPMENT_METHODOLOGY.md`](PROJECT_DEVELOPMENT_METHODOLOGY.md) + [`DEVELOPMENT_WORKFLOW.md`](DEVELOPMENT_WORKFLOW.md) |
| Decisões | [`DECISION_AND_KNOWLEDGE_PROTOCOL.md`](DECISION_AND_KNOWLEDGE_PROTOCOL.md) + `DECISIONS/` |
| UI | [`BATTLE_UI_SIDEBAR.md`](BATTLE_UI_SIDEBAR.md) |
| Online | [`WEB_MULTIPLAYER.md`](WEB_MULTIPLAYER.md) |
| Licenças | [`LEGAL_AND_LICENSES.md`](LEGAL_AND_LICENSES.md) |

## Hierarquia de evidência

```text
implementação atual + testes executáveis
        ↓
contrato canónico atual
        ↓
decisão histórica
        ↓
auditoria / investigação
        ↓
proposta / backlog
        ↓
snapshot histórico
```

Nenhum documento histórico ou de investigação altera silenciosamente o contrato atual.

## Regra contra duplicação

Não criar outro roadmap, “current state”, backlog ou audit paralelo para o mesmo assunto. Melhorar o documento canónico existente e atualizar [`ROADMAP.md`](ROADMAP.md).

`DECISIONS/` é histórico. Não se reescreve para fingir que o passado dizia o que hoje sabemos.

## Baseline atual

O `main` verificado em 2026-09-08 é `73cf14bc0861bd3d6fdb4a437fe9f433b7322a07`.

Qualquer documento com um SHA anterior é evidência histórica e não pode ser usado para declarar o estado atual.
