# RedWar — Current State

**Snapshot:** 2026-09-10  
**Verified `main`:** `6aa5827a650cd623e9a74e9d4910cea2a5effcd9`

Este ficheiro é a fotografia operacional mínima do baseline atual. Os contratos pertencem aos documentos canónicos; a sequência pertence a [`ROADMAP.md`](ROADMAP.md); a cadeia causal transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## 1. Gate de produto atual

**Gate ativo: #371 Gameplay.**

A execução 1.0 segue **#370 Foundation → #371 Gameplay → #372 Ares → #373 Product → #374 Online → #375 Release**. #370 está fechado; #371 é o único gate principal em execução.

## 2. Fundação

A fronteira de execução consolidada é:

```text
input action
→ canonical normalization / resolution
→ action-space membership where applicable
→ transition-domain validation
→ only then mutate
```

A autoridade de action-space, resolução, mutation validation, hero design data, spell capability identity, state hash/repetition, NNUE incremental mutation, `sync_board()` como oracle, terminal conditions e efeitos/timers está documentada e testada para os contratos fechados.

`fast_clone()` é apenas tooling/reference Python e não pertence ao hot path C++ nem ao preflight de legalidade.

## 3. Gameplay

O escopo de #371 é o ruleset 1.0 jogável: board 8×8, draft de 200 por cor, uma ação por turno, setup pré-match canonicamente validado, ações dos heróis, STUN → segundo STUN → morte, vitória/derrota/surrender, no-legal-action termination, TWC de 50 como parâmetro e timing determinístico de fire/ice/terrain.

**Integrado:** #397 ligou a validação canónica de pre-match aos chamadores Pygame e treino.

**Ativo:** #404 / PR #405 elimina o segundo cálculo independente de legalidade em `GameState.check_game_over()`, fazendo a terminação por bloqueio consumir `engine.legal_actions.legal_actions()`.

## 4. Ares

Ares mantém C++ no hot path com alpha-beta/PVS, TT, Zobrist, iterative deepening, move ordering, killer/history, quiescence/tactical search e limites de nodes/tempo. A avaliação clássica é o baseline e NNUE é opcional.

Não existe ainda alegação de strength global aceite. A preparação de #372 pode avançar em paralelo com #371 sem alterar regras. O plano canónico está em [`ARES_EXECUTION_PLAN.md`](ARES_EXECUTION_PLAN.md), governado por #406.

## 5. Strength / Arena

A infraestrutura de Arena, provenance, rating/uncertainty e análise pareada existe. O dataset real persistido contém 100 jogos em 50 pares de inversão de cor; esses pares não representam 50 condições experimentais independentes.

**Não inferir:** benchmark/NPS ≠ strength; dataset maior ≠ strength; training loss menor ≠ strength; NNUE existente ≠ superioridade.

## 6. NNUE

Features, formato versionado, `sync_board()` e hooks incrementais existem. O caminho incremental nativo foi integrado/testado contra full-sync pelo PR #356. Isso não promove NNUE a default sem evidência competitiva/eficiência adicional.

## 7. Heróis / regras

O sistema continua híbrido entre `engine/heroes_config.json` e código especializado. A primeira tranche de nomes de spells duplicados foi corrigida; trabalho data-driven adicional permanece subordinado a contratos reutilizáveis e ao gate ativo.

## 8. UI / replay / telemetria

A arquitetura funcional da Battle Sidebar, Encyclopedia, geometria responsiva e tema semântico está integrada. Restam validação visual/UX, teclado/foco, captura determinística e os blocos de replay/telemetria dependentes dos respetivos contratos/corpus.

## 9. Execução paralela atual

```text
#371 Gameplay
     │
     ├─ #404 terminal/action-space hardening
     │
     └─ #372 / #406 Ares preparation
            ├─ capability corpus
            ├─ evaluator baseline
            ├─ NNUE parity/cost
            ├─ controlled benchmarks
            └─ Arena/provenance preparation
```

A preparação futura não pode contornar #371 nem transformar métricas de benchmark em prova de strength.