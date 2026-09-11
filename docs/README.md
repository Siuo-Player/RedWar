# RedWar — Documentação

A documentação descreve contratos, decisões e a ordem de desenvolvimento. O código e os testes no `main` são a autoridade sobre o comportamento implementado.

## Entrada

```text
README.md
  ↓
docs/00_INDEX.md
  ↓
docs/ROADMAP.md
  ↓
documento canónico do domínio
  ↓
docs/DECISIONS/  (apenas quando a motivação histórica for relevante)
```

Não manter `CURRENT_STATE`, roadmaps datados, handoffs, snapshots ou relatórios de execução como estado operacional permanente.

## Fontes canónicas

- `ARCHITECTURE.md` — fronteiras e invariantes.
- `GAME_RULES.md` — regras de jogo.
- `GAME_DESIGN.md` — intenção de design.
- `HERO_SYSTEM.md` — sistema de heróis.
- `AI_ENGINE.md` — Ares.
- `NNUE.md` — avaliação NNUE.
- `AI_BENCHMARK_PROTOCOL.md` — capability/regression benchmarks.
- `STRENGTH_EVALUATION.md` — strength/Arena.
- `ARENA_STATISTICAL_METHODOLOGY.md` — desenho estatístico.
- `BALANCE_METHODOLOGY.md` — balanceamento.
- `OBSERVABILITY_CONTRACT.md` — informação permitida por modo.
- `BATTLE_UI_SIDEBAR.md` — interação de batalha.
- `WEB_MULTIPLAYER.md` — online.

## Regra de autoridade

```text
código + testes
→ contrato canónico
→ decisão histórica
→ research/proposta
→ roadmap
```

`ROADMAP.md` é a única fila operacional. `DECISIONS/` preserva decisões anteriores e os motivos para elas poderem ser recuperadas ou revertidas; não deve ser usado como estado atual.

Antes de criar documentação nova, atualizar o proprietário canónico existente.
