# RedWar — Current State

**Snapshot:** 2026-09-08  
**Verified `main`:** `e17afcd54ad57635e222f3b3c9a5bb9966df9394`

Este ficheiro é a fotografia operacional mínima do baseline atual. Os contratos pertencem aos documentos canónicos; a sequência pertence a [`ROADMAP.md`](ROADMAP.md); a explicação causal transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## 1. Fase atual

**A0 histórico: CLOSED. A0.1 Semantic Closure: OPEN.**

O `main` atual contém o baseline funcional anterior e o PR #321, merged como `e17afcd54ad57635e222f3b3c9a5bb9966df9394`, que introduziu e testou `engine.legal_actions.resolve_legal_action()` como seam de resolução canónica/legacy.

### Matriz A0.1

| Fronteira | Estado | Evidência atual |
|---|---|---|
| Inquisitor silence/stun | TESTED / CLOSED | #292 + regressão C3/Python/native |
| terminal differential | TESTED / CLOSED | #310 observa o `alpha_beta()` real |
| special-spell legality | TESTED / CLOSED | #303 cobre as special actions atuais |
| canonical `GameAction` boundary | IMPLEMENTED / TESTED / CLOSED | #306 + #308 |
| canonical action resolution seam | IMPLEMENTED / TESTED | #321 — `resolve_legal_action()` centraliza resolução exacta e compatibilidade legacy STUN |
| Python repetition observation | IMPLEMENTED / TESTED / CLOSED | #299 tornou observação idempotente |
| FrostMage unreachable block | IMPLEMENTED / TESTED / CLOSED | #300 + AST regression |
| fixed node-budget semantics | TESTED / CLOSED | cobertura dedicada existente |
| execute-time legal-action authority | DOCUMENTED / UNVERIFIED / OPEN | #317 continua aberta; #309/#315 não foram merged |
| native repetition/history contract | DOCUMENTED / UNVERIFIED / OPEN | não existe contrato nativo de history equivalente estabelecido |

**Importante:** “closed” acima significa fechado para a afirmação específica sustentada pela evidência indicada. Não significa correctness total do projeto nem paridade total em todos os estados possíveis.

A separação necessária em A.1 é:

```text
canonical action-space resolution
        ↓
transition-domain validation
        ↓
only then mutate
```

`legal_actions()` fornece o action-space canónico e `resolve_legal_action()` resolve a representação canónica/legacy. As condições de transição já existentes no `GameState` continuam relevantes e não podem ser substituídas cegamente por membership no action-space.

Fonte: [`A01_SEMANTIC_CLOSURE_2026-09-07.md`](A01_SEMANTIC_CLOSURE_2026-09-07.md).

## 2. Ares

Ares mantém C++ no hot path com alpha-beta/PVS, TT, Zobrist, iterative deepening, move ordering, killer/history, quiescence/tactical search e limites de nodes/tempo.

**Estado do conhecimento:** IMPLEMENTED para a arquitetura documentada; TESTED para os contratos cobertos pela suite; não há aqui uma alegação de STRENGTH improvement.

A avaliação clássica permanece baseline. NNUE é opcional e `sync_board()` continua oracle de correção até que a integração incremental real demonstre equivalência.

`fast_clone()` não faz parte do hot path C++ da Ares e não é mecanismo aceite de preflight de `execute_action()`. Permanece permitido apenas como ferramenta auxiliar em contextos de referência Python, replay, fixtures/property tests, tooling offline e comparação de estados, conforme a decisão estrutural de 2026-09-08.

Fontes: [`AI_ENGINE.md`](AI_ENGINE.md), [`NNUE.md`](NNUE.md), [`AI_BENCHMARK_PROTOCOL.md`](AI_BENCHMARK_PROTOCOL.md), [`DECISIONS/2026-09-08-execution-boundary-no-fast-clone.md`](DECISIONS/2026-09-08-execution-boundary-no-fast-clone.md).

## 3. Strength / Arena

A infraestrutura de Arena, provenance, população, Elo-compatible rating, uncertainty, paired-game/pentanomial analysis, hold-out e SPRT isolado existe.

O primeiro dataset real persistido contém 100 jogos organizados em 50 pares de inversão de cor. Os pares são unidades de resampling/observação pareada; **não são 50 condições experimentais independentes**, porque parte das combinações de opening/seed é reutilizada.

**Estado do conhecimento:** infraestrutura IMPLEMENTED; metodologia DOCUMENTED; calibração de strength global ainda UNVERIFIED.

A existência de um run, intervalo bootstrap, Elo delta ou SPRT isolado não autoriza por si só uma promoção de força.

Fontes: [`STRENGTH_EVALUATION.md`](STRENGTH_EVALUATION.md), [`ARENA_STATISTICAL_METHODOLOGY.md`](ARENA_STATISTICAL_METHODOLOGY.md), [`ARENA_STRENGTH_DATASET.md`](ARENA_STRENGTH_DATASET.md).

## 4. NNUE

As features, formato versionado, `sync_board()` e hooks incrementais existem. **A integração hot-path incremental não está concluída/provada.**

O PR #316 foi merged e separa na CI a classe estreita de alterações metodológicas de dataset NNUE da promoção de strength. O PR #314, que propunha endurecer split/deduplicação/auditoria de dataset, não foi merged e portanto não é implementação corrente.

**Não inferir:** dataset methodology improvement ≠ strength improvement; lower training loss ≠ stronger Ares.

Fonte: [`NNUE.md`](NNUE.md).

## 5. Heróis / regras

O sistema continua híbrido: `engine/heroes_config.json` fornece estrutura declarativa e código especializado cobre mecânicas ainda não expressas integralmente no schema.

Ações canónicas cobertas pela fronteira atual: `MOVE`, `ATTACK`, `STUN`, `SPAWN`, `SPELL`. Special-spell legality está explicitamente testada; `resolve_legal_action()` agora fornece a resolução canónica/legacy, mas isso não equivale a autorizar mutation antes da validação de transição.

Fontes: [`HERO_SYSTEM.md`](HERO_SYSTEM.md), [`GAME_RULES.md`](GAME_RULES.md), [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md).

## 6. UI / replay / telemetria

A arquitetura funcional da Battle Sidebar, contexto Encyclopedia, geometria responsiva e tema semântico estão integrados. O trabalho restante documentado é validação visual/UX, teclado/foco e captura determinística, além de replay/telemetria quando os respetivos corpus e contratos o justificarem.

Isto é **IMPLEMENTED architecture + remaining VALIDATION work**, não uma declaração de UX totalmente validada.

Fonte: [`BATTLE_UI_SIDEBAR.md`](BATTLE_UI_SIDEBAR.md).

## 7. Próximo bloco operacional

O próximo bloco autorizado é [`ROADMAP.md`](ROADMAP.md) → **A0.1: authoritative execution legality + explicit native repetition/history contract**.

A.1 deve primeiro fechar a relação entre action-space canonical e transition validation; não introduzir preflight por clone. Não iniciar search tuning ou strength promotion para contornar esse correctness blocker. UI/replay pode avançar em paralelo apenas onde não atravesse esse blocker.
