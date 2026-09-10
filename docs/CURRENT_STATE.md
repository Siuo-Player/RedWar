# RedWar — Current State

**Snapshot:** 2026-09-10  
**Verified `main`:** `7095258388ef71e4dad2dd178c5be6f95e061337`

Este ficheiro é a fotografia operacional mínima do baseline atual. Os contratos pertencem aos documentos canónicos; a sequência pertence a [`ROADMAP.md`](ROADMAP.md); a explicação causal transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## 1. Gate de produto atual

**Gate ativo: #371 Gameplay.**

A execução 1.0 segue a cadeia contratual **#370 Foundation → #371 Gameplay → #372 Ares → #373 Product → #374 Online → #375 Release**. #370 Foundation está fechado; #371 é o único gate principal em execução.

### Fundação consolidada

A fronteira de execução é:

```text
input action
→ canonical normalization / resolution
→ action-space membership where applicable
→ transition-domain validation
→ only then mutate
```

Os contratos fundacionais auditados têm autoridade explícita para action-space, resolution, transition mutation, hero design data, spell capability identity, state hash/repetition, native NNUE incremental mutation, `sync_board()` como oracle, terminal conditions e efeitos/timers.

`fast_clone()` permanece restrito a contextos auxiliares de referência Python, replay, fixtures/property tests, tooling offline e comparação de estados; não entra no hot path C++ da Ares.

A matriz fundacional e os corrective follow-ups de #370 estão integrados em `main`.

## 2. Gameplay

O escopo ativo de #371 é o ruleset 1.0 jogável e estável: board 8×8, orçamento draft de 200 por cor, uma ação por turno, setup pré-match validado canonicamente, movimentos/ataques/passivas/spells/invocações, sequência STUN → segundo STUN enquanto stunned → morte, vitória/derrota/surrender, no-legal-action termination, TWC de 50 como parâmetro, timing de fire/ice/terrain e progressão determinística.

**Recentemente integrado:** #397 ligou a autoridade de validação de pre-match draft/placement aos chamadores de Pygame e treino. O próximo hardening identificado é #404: fazer a terminação por ausência de ações consumir diretamente o action-space canónico, eliminando o segundo cálculo independente de legalidade em `GameState.check_game_over()`.

## 3. Ares

Ares mantém C++ no hot path com alpha-beta/PVS, TT, Zobrist, iterative deepening, move ordering, killer/history, quiescence/tactical search e limites de nodes/tempo. A avaliação clássica é o baseline; NNUE é opcional.

**Estado:** arquitetura e vários contratos estão IMPLEMENTED/TESTED; a alegação de melhoria global de strength continua UNVERIFIED até à validação Arena definida em #372.

A preparação pode decorrer em paralelo com #371 sem alterar o ruleset. O plano canónico está em [`ARES_EXECUTION_PLAN.md`](ARES_EXECUTION_PLAN.md), governado por #372/#406.

## 4. Strength / Arena

A infraestrutura de Arena, provenance, população, Elo-compatible rating, uncertainty e análise pareada existe. O primeiro dataset real persistido contém 100 jogos em 50 pares de inversão de cor; esses pares não equivalem a 50 condições experimentais independentes.

**Não inferir:** benchmark ≠ strength; mais nodes ≠ strength; dataset maior ≠ strength; training loss menor ≠ strength; NNUE existente ≠ superioridade.

## 5. NNUE

Features, formato versionado, `sync_board()` e hooks incrementais existem. O caminho incremental nativo foi integrado e testado pelo PR #356 contra full-sync/reference. A aceitação dessa paridade não promove NNUE a default sem evidência competitiva/eficiência adicional.

## 6. Heróis / regras

O sistema continua híbrido: `engine/heroes_config.json` fornece estrutura declarativa e código especializado cobre mecânicas ainda não expressas integralmente no schema. A primeira tranche de nomes de spells duplicados foi corrigida; expansões data-driven adicionais permanecem subordinadas ao gate de Gameplay e ao contrato de reutilização demonstrado.

## 7. UI / replay / telemetria

A arquitetura funcional da Battle Sidebar, contexto Encyclopedia, geometria responsiva e tema semântico está integrada. Permanecem validação visual/UX, teclado/foco, captura determinística e os trabalhos de replay/telemetria ainda dependentes dos respetivos contratos/corpus.

## 8. Próxima execução

**Gameplay primeiro:** #404 é o child técnico atual do #371. Em paralelo, #406 prepara as lanes de evidência da futura gate Ares sem promover nem invalidar #371.
