# RedWar — Current State

**Snapshot:** 2026-09-08  
**Verified `main`:** `73cf14bc0861bd3d6fdb4a437fe9f433b7322a07`

Este ficheiro é uma fotografia do baseline. A explicação causal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md); a sequência operacional está em [`ROADMAP.md`](ROADMAP.md).

## 1. Estado de correção

A0 foi fechado como gate histórico. O projeto está agora em **A0.1 Semantic Closure**.

Fechado no baseline:

- terminal differential e terminal score usam a implementação `alpha_beta()` real (#310);
- special-spell legality parity (#303);
- canonical `GameAction` boundary e normalização de `execute_action()` (#306, #308);
- Python analysis cobre MOVE/ATTACK/STUN/SPAWN/SPELL (#291);
- repetition observation Python tornou-se idempotente (#299);
- FrostMage unreachable code removido após cobertura (#300);
- fixed node-budget semantics testado (#285).

Ainda aberto:

- autoridade de execução deve rejeitar ações ilegais antes da mutação;
- repetição/threefold ainda não tem história nativa equivalente definida como contrato;
- novas alterações devem continuar a fechar a cadeia differential → transition → make/unmake → hash conforme a matriz de traceability.

Fonte canónica: [`A01_SEMANTIC_CLOSURE_2026-09-07.md`](A01_SEMANTIC_CLOSURE_2026-09-07.md).

## 2. Ares

Ares usa C++ no hot path com alpha-beta/PVS, TT, Zobrist, iterative deepening, move ordering, killer/history e quiescence/tactical search.

A avaliação clássica continua disponível como baseline. NNUE é opcional.

O NNUE tem infraestrutura de features e hooks incrementais, mas a integração completa desses hooks no caminho real de `BoardState` continua uma tarefa de engenharia. `sync_board()` permanece o oracle de correção até existir paridade incremental provada.

Fonte: [`AI_ENGINE.md`](AI_ENGINE.md), [`NNUE.md`](NNUE.md).

## 3. Strength / Arena

A infraestrutura de Arena, provenance, população, Elo-compatible rating, uncertainty, paired-game/pentanomial analysis, hold-out e SPRT isolado existe.

O primeiro dataset real persistido contém 100 jogos válidos em 50 pares de inversão de cor. Esses pares são unidades de resampling para a análise existente; não devem ser tratados como 50 condições experimentais independentes porque condições/openings/seeds são reutilizados.

A calibração de strength ainda exige replicação deliberada, variação de população/contexto e validação da incerteza antes de um gate automático de promoção.

Fontes: [`STRENGTH_EVALUATION.md`](STRENGTH_EVALUATION.md), [`ARENA_STATISTICAL_METHODOLOGY.md`](ARENA_STATISTICAL_METHODOLOGY.md), [`ARENA_STRENGTH_DATASET.md`](ARENA_STRENGTH_DATASET.md), e decisões de strength em [`DECISIONS/`](DECISIONS/).

## 4. Heróis e regras

O sistema continua híbrido: configuração declarativa define a estrutura suportada e código especializado cobre mecânicas que ainda não cabem no schema. Isto é uma decisão conhecida, não prova de que o sistema já seja totalmente data-driven.

A matriz de traceability continua a ser o mecanismo de verificação transversal. Especialmente importantes são STUN, spells, passivas, lifespan, cooldown, efeitos e TWC.

Fontes: [`GAME_RULES.md`](GAME_RULES.md), [`HERO_SYSTEM.md`](HERO_SYSTEM.md), [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md).

## 5. UI / replay / telemetria

A Battle Sidebar inicial e o contexto Encyclopedia já estão implementados; a validação visual/responsiva continua trabalho de produto.

A arquitetura de replay local já suporta retenção durável; as próximas tarefas são inspeção/exportação e telemetria estruturada com provenance.

Fontes: [`BATTLE_UI_SIDEBAR.md`](BATTLE_UI_SIDEBAR.md), `REPLAY_STORAGE.md` e documentos de telemetria.

## 6. Regra operacional

A ordem seguinte é sempre a de [`ROADMAP.md`](ROADMAP.md). Não usar snapshots antigos, branches documentais ou ficheiros de backlog para substituir essa ordem.
