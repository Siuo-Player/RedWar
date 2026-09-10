# RedWar — Current State

**Snapshot:** 2026-09-10  
**Verified `main` baseline:** `6aa5827a650cd623e9a74e9d4910cea2a5effcd9`

Este ficheiro é a fotografia operacional mínima do baseline atual. Os contratos pertencem aos documentos canónicos; a sequência pertence a [`ROADMAP.md`](ROADMAP.md); a explicação causal transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## 1. Gate de produto atual

**Gate ativo: #371 Gameplay.**

A execução 1.0 segue a cadeia contratual **#370 Foundation → #371 Gameplay → #372 Ares → #373 Product → #374 Online → #375 Release**. A fundação #370 está fechada. O trabalho de investigação, testes, tooling e preparação dos gates seguintes pode decorrer em paralelo quando não altera nem contorna os critérios do gate ativo.

### Estado da fundação consolidada

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
| incremental NNUE mutation path | IMPLEMENTED / TESTED | PR #356, merge `4ef04f8bf98bb380f773bebdb225cd16787c6c29` |
| canonical spell-name metadata in specialized Python generators | IMPLEMENTED / TESTED / MERGED | PR #367, merge `218fd115864629a79c82c72c729fa0faff831664` |
| canonical pre-match setup validator | IMPLEMENTED / TESTED / MERGED | #396 + #397 |

**Importante:** “closed” acima significa fechado para a afirmação específica sustentada pela evidência indicada. Não significa correctness total do projeto, nem paridade total em todos os estados matematicamente possíveis.

## 2. Gameplay — #371

#371 é o gate ativo. **#397 está concluído**; o próximo child de correctness em execução é o #404/#405, que consolida a terminação sem ação através do action-space canónico.

A aceitação de #371 exige:

```text
rules declared in 1.0
→ canonical authority exists
→ executable regressions cover critical mechanics
→ local match cannot start from invalid setup
→ effects/timers/win/terminal edges are deterministic
→ Python/C++ agree where both implement the same rule
```

Preparação de corpus, Ares harness, UI validation, replay/telemetry e online/release design podem avançar sem declarar #371 fechado.

## 3. Ares

Ares mantém C++ no hot path com alpha-beta/PVS, TT, Zobrist, iterative deepening, move ordering, killer/history, quiescence/tactical search e limites de nodes/tempo.

**Estado do conhecimento:** arquitetura implementada; não há alegação de melhoria global de strength.

A pesquisa Stockfish de 2026-09-10 está em [`ARES_STOCKFISH_RESEARCH.md`](ARES_STOCKFISH_RESEARCH.md) e o plano de execução paralelo até 1.0 está em [`ROADMAP_1.0_PARALLEL_EXECUTION.md`](ROADMAP_1.0_PARALLEL_EXECUTION.md).

A primeira hipótese de performance é medir o caminho NNUE incremental sem `sync_board()` por nó, mantendo `sync_board()` como oracle. Depois, os experimentos de LMR, aspiration, history/context, TT e pruning devem ser feitos como patches independentes antes de qualquer composição.

Não inferir strength de NPS, depth ou benchmark isolado.

## 4. Strength / Arena

A infraestrutura de Arena, provenance, população, Elo-compatible rating, uncertainty, paired-game/pentanomial analysis, hold-out e SPRT isolado existe.

O primeiro dataset real persistido contém 100 jogos organizados em 50 pares de inversão de cor. Os pares são unidades de resampling/observação pareada; **não são 50 condições experimentais independentes**, porque parte das combinações de opening/seed é reutilizada.

**Estado do conhecimento:** infraestrutura IMPLEMENTED; metodologia DOCUMENTED; calibração de strength global ainda UNVERIFIED.

A existência de um run, intervalo bootstrap, Elo delta ou SPRT isolado não autoriza por si só uma promoção de força.

## 5. NNUE

As features, formato versionado, `sync_board()` e hooks incrementais existem. **O caminho incremental nativo foi integrado e testado no caminho real de `make_move()` / `unmake_move()` pelo PR #356.**

`sync_board()` continua como referência de ressincronização completa e oracle de correção. A próxima pergunta de performance é económica: quanto custa o resync completo dentro de `evaluate_board()` e quanto desse custo desaparece quando o acumulador incremental é usado diretamente?

**Não inferir:** dataset methodology improvement ≠ strength improvement; lower training loss ≠ stronger Ares; correctness parity ≠ competitive superiority.

## 6. Heróis / regras

O sistema continua híbrido: `engine/heroes_config.json` fornece estrutura declarativa e código especializado cobre mecânicas ainda não expressas integralmente no schema.

Ações canónicas da fronteira atual: `MOVE`, `ATTACK`, `STUN`, `SPAWN`, `SPELL`. A relação entre geradores de peça, action-space canónico, resolução legacy e validação de transição está coberta como contrato de execução.

## 7. UI / replay / telemetria

A arquitetura funcional da Battle Sidebar, contexto Encyclopedia, geometria responsiva e tema semântico estão integrados. O trabalho restante documentado é validação visual/UX, teclado/foco e captura determinística, além de replay/telemetria quando os respetivos corpus e contratos o justificarem.

Isto é **IMPLEMENTED architecture + remaining VALIDATION work**, não uma declaração de UX totalmente validada.

## 8. Próxima execução

A ordem operacional agora é orientada por dependências:

```text
#371 Gameplay gate
      │
      ├── #404/#405 terminal action-space
      ├── gameplay corpus
      ├── Ares research/preparation (#402)
      ├── Arena tooling
      ├── Product validation
      ├── Online preparation
      └── Release preparation

#371 close
      ↓
#372 Ares promotion
      ↓
#373 Product promotion
      ↓
#374 Online promotion
      ↓
#375 Release
```

Consultar `ROADMAP.md` para a ordem canónica e `ROADMAP_1.0_PARALLEL_EXECUTION.md` para a decomposição de trabalho paralelo.
