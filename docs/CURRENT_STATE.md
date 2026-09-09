# RedWar — Current State

**Snapshot:** 2026-09-09  
**Verified `main`:** `010b14b6251ce131409e660df95c6d920c76af58`

Este ficheiro é a fotografia operacional mínima do baseline atual. Os contratos pertencem aos documentos canónicos; a sequência pertence a [`ROADMAP.md`](ROADMAP.md); a explicação causal transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## 1. Fase atual

**A0 histórico: CLOSED. A0.1 Semantic Closure: CLOSED.**

O `main` atual contém a fundação de action-space/execução resultante das tranches A0.1. `legal_actions()` fornece a enumeração canónica derivada dos geradores das peças; `resolve_legal_action()` é o seam de resolução canónica/legacy; `GameState._validate_transition()` mantém as restrições específicas de transição; `execute_action()` só entrega uma ação resolvida à mutação depois dessas fronteiras.

### Matriz A0.1

| Fronteira | Estado | Evidência atual |
|---|---|---|
| Inquisitor silence/stun | TESTED / CLOSED | #292 + regressão C3/Python/native |
| terminal differential | TESTED / CLOSED | #310 observa o `alpha_beta()` real |
| special-spell legality | TESTED / CLOSED | #303 cobre as special actions atuais |
| canonical `GameAction` boundary | IMPLEMENTED / TESTED / CLOSED | #306 + #308 |
| canonical action resolution seam | IMPLEMENTED / TESTED / CLOSED | #321 + #351 |
| generator → canonical action-space coverage | TESTED / VALIDATED / CLOSED | #351 cobre todos os heróis configurados em variantes determinísticas |
| canonical ↔ legacy execution compatibility | TESTED / VALIDATED / CLOSED | #348 + #349 + #351 |
| execute-time domain-error contract | TESTED / VALIDATED / CLOSED | #350 + #352 |
| Python repetition observation | IMPLEMENTED / TESTED / CLOSED | #299 tornou observação idempotente |
| FrostMage unreachable block | IMPLEMENTED / TESTED / CLOSED | #300 + AST regression |
| fixed node-budget semantics | TESTED / CLOSED | cobertura dedicada existente |
| native repetition/history contract | ARCHITECTURAL DECISION / TESTED BOUNDARY / CLOSED | #338 define `BoardState` como posição/search state e não como owner da sequência de repetição |

**Importante:** “closed” acima significa fechado para a afirmação específica sustentada pela evidência indicada. Não significa correctness total do projeto, nem paridade total em todos os estados matematicamente possíveis.

A fronteira de execução consolidada é:

```text
input action
        ↓
canonical normalization / resolution
        ↓
action-space membership where applicable
        ↓
transition-domain validation
        ↓
only then mutate
```

A cobertura de #351 exerceu todos os heróis configurados em estados determinísticos e verificou que as ações produzidas diretamente pelos geradores aparecem no action-space canónico, sobrevivem à resolução legacy e executam através de `execute_action()`. #352 fixa os erros específicos do domínio e a não-mutação em rejeições. Assim, a alegação de A.1 é agora sobre a fronteira `execute_action()` + action-space canónico, não sobre transformar `make_action()` numa segunda implementação da legalidade.

`fast_clone()` não é mecanismo de preflight nem autoridade de legalidade. Continua permitido apenas em contextos auxiliares de referência Python, replay, fixtures/property tests, tooling offline e comparação de estados; não entra no hot path C++ da Ares.

Fonte: [`A01_SEMANTIC_CLOSURE_2026-09-07.md`](A01_SEMANTIC_CLOSURE_2026-09-07.md).

## 2. Ares

Ares mantém C++ no hot path com alpha-beta/PVS, TT, Zobrist, iterative deepening, move ordering, killer/history, quiescence/tactical search e limites de nodes/tempo.

**Estado do conhecimento:** IMPLEMENTED para a arquitetura documentada; TESTED para os contratos cobertos pela suite; não há aqui uma alegação de STRENGTH improvement.

A avaliação clássica permanece baseline. NNUE é opcional e `sync_board()` continua oracle de correção até que a integração incremental real demonstre equivalência.

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

Ações canónicas da fronteira atual: `MOVE`, `ATTACK`, `STUN`, `SPAWN`, `SPELL`. A relação entre geradores de peça, action-space canónico, resolução legacy e validação de transição está agora coberta como contrato de execução; isso não duplica as regras de herói.

Fontes: [`HERO_SYSTEM.md`](HERO_SYSTEM.md), [`GAME_RULES.md`](GAME_RULES.md), [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md).

## 6. UI / replay / telemetria

A arquitetura funcional da Battle Sidebar, contexto Encyclopedia, geometria responsiva e tema semântico estão integrados. O trabalho restante documentado é validação visual/UX, teclado/foco e captura determinística, além de replay/telemetria quando os respetivos corpus e contratos o justificarem.

Isto é **IMPLEMENTED architecture + remaining VALIDATION work**, não uma declaração de UX totalmente validada.

Fonte: [`BATTLE_UI_SIDEBAR.md`](BATTLE_UI_SIDEBAR.md).

## 7. Próximo bloco operacional

Com A0.1 fechado, o próximo bloco da sequência é [`ROADMAP.md`](ROADMAP.md) → **B: strength measurement / calibration**, sem saltar os critérios de evidência. C, D, E, F e G continuam condicionados pelos respetivos gates.
