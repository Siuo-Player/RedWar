# RedWar — Current State

**Snapshot:** 2026-09-10  
**Verified `main`:** `218fd115864629a79c82c72c729fa0faff831664`

Este ficheiro é a fotografia operacional mínima do baseline atual. Os contratos pertencem aos documentos canónicos; a sequência pertence a [`ROADMAP.md`](ROADMAP.md); a explicação causal transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## 1. Gate de produto atual

**Gate ativo: #370 Foundation.**

A execução 1.0 segue a cadeia contratual **#370 Foundation → #371 Gameplay → #372 Ares → #373 Product → #374 Online → #375 Release**. O gate atual não declara o produto 1.0 completo: fecha primeiro a fundação necessária para que regras, estado, legalidade, transições e infraestruturas tenham autoridade única e evidência executável.

### Estado da fundação já consolidada

| Fronteira | Estado | Evidência atual |
|---|---|---|
| Inquisitor silence/stun | TESTED / CLOSED para a afirmação específica | #292 + regressão C3/Python/native |
| terminal differential | TESTED / CLOSED para a afirmação específica | #310 observa o `alpha_beta()` real |
| special-spell legality | TESTED / CLOSED para a afirmação específica | #303 cobre as special actions atuais |
| canonical `GameAction` boundary | IMPLEMENTED / TESTED / CLOSED | #306 + #308 |
| canonical action resolution seam | IMPLEMENTED / TESTED / CLOSED | #321 + #351 |
| generator → canonical action-space coverage | TESTED / VALIDATED / CLOSED | #351 cobre os heróis configurados em variantes determinísticas |
| canonical ↔ legacy execution compatibility | TESTED / VALIDATED / CLOSED | #348 + #349 + #351 |
| execute-time domain-error contract | TESTED / VALIDATED / CLOSED | #350 + #352 |
| Python repetition observation | IMPLEMENTED / TESTED / CLOSED | #299 tornou observação idempotente |
| FrostMage unreachable block | IMPLEMENTED / TESTED / CLOSED | #300 + AST regression |
| fixed node-budget semantics | TESTED / CLOSED | cobertura dedicada existente |
| native repetition/history contract | ARCHITECTURAL DECISION / TESTED BOUNDARY / CLOSED | #338 define `BoardState` como posição/search state e não como owner da sequência de repetição |
| incremental NNUE mutation path | IMPLEMENTED / TESTED | PR #356, merge `f2e7155d150b4cc0be79d4b86beb5005941ef180` |
| canonical spell-name metadata in specialized Python generators | IMPLEMENTED / TESTED / MERGED | PR #367, merge `218fd115864629a79c82c72c729fa0faff831664` |

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

A cobertura de #351 exerceu os heróis configurados em estados determinísticos e verificou que as ações produzidas diretamente pelos geradores aparecem no action-space canónico, sobrevivem à resolução legacy e executam através de `execute_action()`. #352 fixa os erros específicos do domínio e a não-mutação em rejeições. A existência de #367 acrescenta a primeira correção controlada de metadado duplicado: os cinco geradores especializados passaram a consumir a declaração canónica de `spells`.

`fast_clone()` não é mecanismo de preflight nem autoridade de legalidade. Continua permitido apenas em contextos auxiliares de referência Python, replay, fixtures/property tests, tooling offline e comparação de estados; não entra no hot path C++ da Ares.

Fonte: [`A01_SEMANTIC_CLOSURE_2026-09-07.md`](A01_SEMANTIC_CLOSURE_2026-09-07.md).

## 2. Ares

Ares mantém C++ no hot path com alpha-beta/PVS, TT, Zobrist, iterative deepening, move ordering, killer/history, quiescence/tactical search e limites de nodes/tempo.

**Estado do conhecimento:** IMPLEMENTED para a arquitetura documentada; TESTED para os contratos cobertos pela suite; não há aqui uma alegação de STRENGTH improvement.

A avaliação clássica permanece baseline. NNUE é opcional. A integração incremental do caminho nativo foi ligada ao caminho real de mutação e validada pelo PR #356 contra a referência de full resync; `sync_board()` permanece explícito como oracle/recovery path. A aceitação desta correção não implica superioridade competitiva da NNUE.

Fontes: [`AI_ENGINE.md`](AI_ENGINE.md), [`NNUE.md`](NNUE.md), [`AI_BENCHMARK_PROTOCOL.md`](AI_BENCHMARK_PROTOCOL.md), [`DECISIONS/2026-09-08-execution-boundary-no-fast-clone.md`](DECISIONS/2026-09-08-execution-boundary-no-fast-clone.md).

## 3. Strength / Arena

A infraestrutura de Arena, provenance, população, Elo-compatible rating, uncertainty, paired-game/pentanomial analysis, hold-out e SPRT isolado existe.

O primeiro dataset real persistido contém 100 jogos organizados em 50 pares de inversão de cor. Os pares são unidades de resampling/observação pareada; **não são 50 condições experimentais independentes**, porque parte das combinações de opening/seed é reutilizada.

**Estado do conhecimento:** infraestrutura IMPLEMENTED; metodologia DOCUMENTED; calibração de strength global ainda UNVERIFIED.

A existência de um run, intervalo bootstrap, Elo delta ou SPRT isolado não autoriza por si só uma promoção de força.

Fontes: [`STRENGTH_EVALUATION.md`](STRENGTH_EVALUATION.md), [`ARENA_STATISTICAL_METHODOLOGY.md`](ARENA_STATISTICAL_METHODOLOGY.md), [`ARENA_STRENGTH_DATASET.md`](ARENA_STRENGTH_DATASET.md).

## 4. NNUE

As features, formato versionado, `sync_board()` e hooks incrementais existem. **O caminho incremental nativo foi integrado e testado no caminho real de `make_move()` / `unmake_move()` pelo PR #356.**

`sync_board()` continua como referência de ressincronização completa e oracle de correção. A equivalência incremental/full-sync foi exercida em alterações de movimento, turno/TWC, stun/lifespan/spawn-cooldown e efeitos, sem promover a NNUE a alegação de strength.

**Não inferir:** dataset methodology improvement ≠ strength improvement; lower training loss ≠ stronger Ares; correctness parity ≠ competitive superiority.

Fontes: [`NNUE.md`](NNUE.md), PR #356.

## 5. Heróis / regras

O sistema continua híbrido: `engine/heroes_config.json` fornece estrutura declarativa e código especializado cobre mecânicas ainda não expressas integralmente no schema.

Ações canónicas da fronteira atual: `MOVE`, `ATTACK`, `STUN`, `SPAWN`, `SPELL`. A relação entre geradores de peça, action-space canónico, resolução legacy e validação de transição está coberta como contrato de execução, mas a auditoria #379 identificou uma dívida restante: parte da validação de spells em `GameState` mantém vocabulário/dispatch textual separado da configuração. Essa dívida está rastreada no #380 e continua aberta.

A auditoria #318 permanece também aberta para a análise hero-by-hero e para refatorações data-driven que demonstrem contrato reutilizável. PR #367 fechou apenas a primeira tranche de nomes de spells duplicados nos cinco geradores especializados.

Fontes: [`HERO_SYSTEM.md`](HERO_SYSTEM.md), [`GAME_RULES.md`](GAME_RULES.md), [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md).

## 6. UI / replay / telemetria

A arquitetura funcional da Battle Sidebar, contexto Encyclopedia, geometria responsiva e tema semântico estão integrados. O trabalho restante documentado é validação visual/UX, teclado/foco e captura determinística, além de replay/telemetria quando os respetivos corpus e contratos o justificarem.

Isto é **IMPLEMENTED architecture + remaining VALIDATION work**, não uma declaração de UX totalmente validada.

Fonte: [`BATTLE_UI_SIDEBAR.md`](BATTLE_UI_SIDEBAR.md).

## 7. Próximo bloco operacional

A execução corrente segue **#370 Foundation**. O child ativo para a próxima correção de runtime é **#380**, precedido pelo audit #379. O trabalho de documentação de baseline é o **#381**. A passagem para #371 Gameplay só ocorre depois de #370 satisfazer a sua aceitação integral; #372 Ares continua depois da gate de Gameplay.
