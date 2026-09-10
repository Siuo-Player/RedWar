# RedWar — Current State

**Snapshot:** 2026-09-10  
**Verified `main`:** `3a06d2edf1dc4f32b8719eb3d0da8167613424eb`

Este ficheiro é a fotografia operacional mínima do baseline atual. Os contratos pertencem aos documentos canónicos; a sequência pertence a [`ROADMAP.md`](ROADMAP.md); a cadeia causal transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## 1. Gate de produto atual

**Gate ativo: #372 Ares.**

A execução 1.0 segue **#370 Foundation → #371 Gameplay → #372 Ares → #373 Product → #374 Online → #375 Release**. #370 e #371 estão fechados; #372 é agora o único gate principal em execução.

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

**Integrado:** #404 / PR #405 eliminou o segundo cálculo independente de legalidade em `GameState.check_game_over()`, fazendo a terminação por bloqueio consumir `engine.legal_actions.legal_actions()`.

**Fechado:** #371 após a última tranche de Gameplay, sem alteração das fronteiras de balance/strength.

## 4. Ares

Ares mantém C++ no hot path com alpha-beta/PVS, TT, Zobrist, iterative deepening, move ordering, killer/history, quiescence/tactical search e limites de nodes/tempo. A avaliação clássica é o baseline e NNUE é opcional.

### Correctness integrada

- #418 CLOSED / PR #421 merged em `44da940f9291ebb3116df97365903eec02b0591e`.
- Test Suite #2122 passou incluindo `Run native reversibility contract`.
- CodeQL #762 passou.
- AI Quality Gate #764 passou.
- O helper nativo verifica identidade de `make/unmake` incluindo turno, TWC, hash, material/contagens, peças, efeitos e lifecycle fields em posições representativas.

### NNUE/performance groundwork

PR #420 foi integrado em `3a06d2edf1dc4f32b8719eb3d0da8167613424eb` e adiciona um microbenchmark controlado que compara avaliação NNUE incremental com o mesmo caminho usando `sync_board()`. O benchmark exige equivalência de avaliação e mede custo; não constitui evidência de strength.

### Próxima execução

A cadeia obrigatória é:

```text
correctness ✅
→ deterministic capability
→ controlled performance
→ independent Arena strength
→ promotion
```

Já existe infraestrutura determinística de capability em `tools/analytics/tactical_benchmark_suite.py`, com seis casos atuais. #431 é o próximo lane para validar estabilidade das referências de alto orçamento e só depois promovê-las a hard regressions.

Não existe ainda alegação de strength global aceite.

## 5. Strength / Arena

A infraestrutura de Arena, provenance, rating/uncertainty e análise pareada existe. O dataset real persistido contém 100 jogos em 50 pares de inversão de cor; esses pares não representam 50 condições experimentais independentes.

**Não inferir:** benchmark/NPS ≠ strength; dataset maior ≠ strength; training loss menor ≠ strength; NNUE existente ≠ superioridade.

## 6. NNUE

Features, formato versionado, `sync_board()` e hooks incrementais existem. O caminho incremental nativo foi integrado/testado contra full-sync pelo PR #356. O PR #420 acrescenta apenas a medição controlada de custo/equivalência desse caminho. NNUE continua opcional até existir evidência competitiva e de eficiência segundo o protocolo de #372.

## 7. Heróis / regras

O sistema continua híbrido entre `engine/heroes_config.json` e código especializado. A primeira tranche de nomes de spells duplicados foi corrigida; trabalho data-driven adicional permanece subordinado a contratos reutilizáveis e ao gate ativo.

## 8. UI / replay / telemetria

A arquitetura funcional da Battle Sidebar, Encyclopedia, geometria responsiva e tema semântico está integrada. Restam validação visual/UX, teclado/foco, captura determinística e os blocos de replay/telemetria dependentes dos respetivos contratos/corpus.

## 9. Execução atual

```text
#370 Foundation ✅
        ↓
#371 Gameplay ✅
        ↓
#372 Ares ACTIVE
        ├─ correctness ✅ #418/#421
        ├─ NNUE cost groundwork ✅ #420
        ├─ tactical capability #431
        ├─ evaluator baseline
        ├─ search hypotheses
        ├─ controlled benchmarks
        └─ Arena/provenance
        ↓
#373 Product BLOCKED
        ↓
#374 Online BLOCKED
        ↓
#375 Release BLOCKED
```

A preparação futura pode avançar em lanes independentes quando não altera uma gate anterior, mas nenhuma métrica de benchmark pode ser tratada como prova de strength.
