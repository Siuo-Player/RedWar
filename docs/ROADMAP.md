# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `6aa5827a650cd623e9a74e9d4910cea2a5effcd9`  
**Data:** 2026-09-10

Este é o **único documento que define a ordem operacional do trabalho**. Não duplicar esta fila em snapshots, branches, backlogs ou conversas.

## Vocabulário obrigatório

`DOCUMENTED` = descrito.  
`IMPLEMENTED` = existe no código alvo.  
`TESTED` = existe teste executável relevante.  
`VALIDATED` = foi submetido à validação apropriada para a alegação.  
`PROVEN` = a evidência é suficiente para a alegação específica sob o protocolo vigente.

Uma fase só pode ser `CLOSED` quando os critérios de aceitação forem satisfeitos no `main` e a evidência relevante estiver ligada aqui. CI verde é necessária para mudanças de código, mas **CI verde ≠ correctness total**, benchmark ≠ strength e melhoria de dataset ≠ melhoria de strength.

## Estado atual — 1.0 gate chain

A execução corrente segue a cadeia de issues canónica:

```text
#370 Foundation
      ↓
#371 Gameplay
      ↓
#372 Ares
      ↓
#373 Product
      ↓
#374 Online
      ↓
#375 Release
```

#370 foi o primeiro gate. A auditoria #379 e os seus dois corrective follow-ups (#381 e #380) estão agora concluídos/merged. O trabalho de produto continua subordinado à cadeia; a preparação documental, investigação, testes e tooling dos gates seguintes podem decorrer em paralelo quando não alteram nem contornam um gate de correctness.

## Modelo de execução paralela

A cadeia acima continua a ser a **ordem dos gates de promoção**. Ela não significa que todo o trabalho tenha de ser executado serialmente.

Usar a seguinte regra:

```text
GATE DEPENDENCY
→ controla quando uma funcionalidade pode ser promovida

WORK DEPENDENCY
→ controla quando uma alteração precisa de outra alteração
```

Quando não existe work dependency real, trabalhar em paralelo.

Exemplo durante #371:

```text
#371 Gameplay
   │
   ├── gameplay fixes / regressions
   ├── gameplay corpus
   ├── Ares correctness harness preparation
   ├── NNUE differential/performance harness
   ├── Stockfish search experiments/design
   ├── Arena/statistical tooling
   ├── Product/UI validation
   ├── replay/telemetry preparation
   ├── Online architecture preparation
   └── Release/security/license preparation
```

Só a **promoção** permanece bloqueada pelo gate correspondente.

Plano detalhado: [`ROADMAP_1.0_PARALLEL_EXECUTION.md`](ROADMAP_1.0_PARALLEL_EXECUTION.md).

## #370 — Foundation

**Estado: CLOSED — 2026-09-10.**

### Evidência de saída

- **#386** — matriz de autoridade machine-readable + Markdown, merged em `b83e1b851911a295052802572b9fbb7369a462ff` com Test Suite #1964, CodeQL #692 e AI Quality Gate #707 verdes.
- **#381** — sincronização de `docs/CURRENT_STATE.md` e `docs/NNUE.md` com a evidência real de `main`, merged em `612221b88381cf740bab6d2ab9e31acfb98c6324` com Test Suite #1948, CodeQL #685 e AI Quality Gate #701 verdes.
- **#380** — eliminação da duplicação de vocabulário de spells em `_validate_transition()`, merged em `8534b2f59392b9e9779bb9ac8e55d7a8b3e53613` a partir do head `1d204482e118790f7fbd138e8fb1d6f8a40fbc15`, com Test Suite #1974, CodeQL #698 e AI Quality Gate #712 verdes.
- **#391 / #392** — surrender canónico + hardening do contrato, e segundo-STUN do Ignite com paridade Python/C++, merged em `1e137e6ae09a931ea5cef73771e7d753b3c75d53` e `2ea747c15c389640a77a8bb3aea6cf03b69c7424`, respetivamente, com as três gates relevantes verdes nos heads validados.

A matriz final classifica os contratos críticos auditados como `CANONICAL_AND_TESTED` ou `JUSTIFIED_SPECIALIZATION`; não há um `DUPLICATED_AUTHORITY`, `DOCUMENTATION_DRIFT` ou `UNPROTECTED_GAP` remanescente identificado no inventário fundacional. A matriz não constitui alegação de balance, strength ou superioridade de search.

A fronteira fundacional agora consolidada é:

```text
input action
→ normalize canonical action
→ canonical resolution / membership
→ transition-domain validation
→ only then mutate
```

E inclui, entre outros, autoridades explícitas para action-space, resolution, transition mutation, hero design data, spell capability identity, state hash/repetition, native NNUE incremental mutation, `sync_board()` como oracle, terminal conditions e efeitos/timers.

`fast_clone()` permanece restrito a fixtures/replay/reference tooling em Python e fora do hot path C++ da Ares.

## Histórico de infraestrutura já concluído

Os lanes independentes anteriores B–G foram executados a partir do baseline comum `1f65f65d6b4827f0d403d8e6d2bb0f735eda0c42` e merged com as três gates do repositório:

- **#329** — determinismo do audit emparelhado; `29973ffb6e7d270ab8ccc9289307ab11e2f24506`.
- **#330** — ausência de `fast_clone` no C++ da Ares; `d08a700864d8ed0fe9dc274f8495a01f81105641`.
- **#331** — encoding NNUE por perspetiva; `fdd1c3516e410b53608a95e554597a577ef6610e`.
- **#332** — isolamento replay/telemetria; `d07f52f981de0eb0606bef1823beabca61348ae1`.
- **#333** — bounds do Auto-Pricer; `71bc812d170a8556b9dfde98b4f95202f36190b9`.
- **#334** — fundação de sessão autoritativa server-side; `845b00a500fff7b3aab2f0c35920bace5d198cc6`.

A tranche fecha infraestrutura/regressões específicas; não equivale a declarar concluídas as fases de produto, strength, balance ou online.

## #371 — Gameplay

**Estado: OPEN — em execução.**

Objetivo: tornar o ruleset 1.0 efetivamente jogável e estável sobre a fundação fechada.

Escopo canónico: board 8×8; orçamento draft atual de 200 pontos por cor; uma ação por turno; draft/placement secreto antes do match e sem compras durante o match; movimento, ataques, passivas, spells e invocações dos heróis; sequência STUN → segundo STUN enquanto stunned → morte; vitória/derrota/surrender; terminação sem ação legal; parâmetro de 50 turnos sem captura permanente; timing fire/ice/terrain; geração e execução determinísticas e sem autoridades duplicadas.

### Progresso atual

- **Concluído:** surrender canónico e hardening do fluxo terminal; segundo STUN do Ignite com TWC/paridade Python-C++; autoridade de spell declarations sem whitelist duplicada.
- **Concluído:** **#396** criou a autoridade de validação canónica de pre-match draft/placement e regressões para orçamento, home rows, unidades não-draftable, equipas e cópias duplicadas. O PR foi merged; **#397 também está concluído**, incluindo a integração nos chamadores Pygame e treino.
- **Em execução:** **#404/#405** — fazer a terminação sem ação consumir exclusivamente o action-space canónico, preservando surrender como comando não-board e a precedência das demais condições terminais.
- **Concluído no contrato:** timing de efeitos foi explicitado: a criação não consome o primeiro tick; o timer avança quando o lado proprietário se torna ativo. Fire aplica stun elegível na transição; ice impede passagem/centro Nevada. O contrato está em `docs/DECISIONS/2026-09-10-pre-match-and-effect-timing-contract.md` e há regressão explícita para a posse temporal.

Critério de saída: cada regra declarada tem uma implementação/especificação autorizada; cenários críticos passam pela ação canónica; efeitos, vitória e edges de turnos têm regressões executáveis; não existe ambiguidade conhecida que impeça jogo local; parâmetros de balance são explícitos.

## #372 — Ares

**Estado: BLOCKED UNTIL #371 CLOSES — research/preparation may proceed in parallel.**

Objetivo: correctness primeiro, depois capability/search/eval/classical baseline, optional NNUE, controlled benchmarks e Arena A/B com provenance. Benchmark ≠ strength; mais nodes ≠ strength; NNUE existente ≠ superioridade; dataset maior ≠ strength maior.

A pesquisa de 2026-09-10, com prioridade em Stockfish e artigos clássicos de search/NNUE, está documentada em `docs/ARES_STOCKFISH_RESEARCH.md`. O plano operacional detalhado e a matriz de trabalho paralelo estão em `docs/ROADMAP_1.0_PARALLEL_EXECUTION.md`.

### Ordem de promoção do Ares

```text
A0  correctness baseline
 ↓
A1  NNUE incremental/full-sync equivalence + economics
 ↓
A2  move ordering/history experiments
 ↓
A3  LMR
 ↓
A4  aspiration / iterative-deepening economics
 ↓
A5  TT replacement/aging
 ↓
A6  carefully scoped pruning / NMP / LMP
 ↓
A7  quiescence frontier
 ↓
A8  time management
 ↓
A9  evaluator improvements / NNUE training
 ↓
A10 independent Arena strength evidence
```

Esta ordem é uma **ordem de dependência e promoção**, não uma fila que obrigue todas as investigações a esperar umas pelas outras. Por exemplo, A2/A3/A4/A5 podem ser investigados em paralelo a partir do mesmo baseline; após cada resultado individual, os vencedores são integrados e a composição final é novamente validada.

A primeira hipótese de implementação continua a ser o caminho NNUE incremental: o hot path atual ainda faz `sync_board()` antes de cada inferência. O objetivo é medir e, apenas se a paridade permanecer exata, eliminar o scan por nó mantendo `sync_board()` como oracle.

O princípio Stockfish aplicado é: patches pequenos, uma ideia por teste, benchmarks de custo separados de strength e promoção baseada em evidência estatística.

`fast_clone()` não pertence ao C++ hot path. Qualquer otimização exige regressão de correctness + benchmark controlado; qualquer alegação de strength exige avaliação Arena independente.

## #373 — Product

**Estado: BLOCKED UNTIL #372 CLOSES.**

Preparação pode decorrer em paralelo:

- validação visual/UX da Battle Sidebar;
- keyboard/focus;
- responsive layouts;
- Encyclopedia/contexto;
- stress scenes FrostMage/NEVADA;
- replay/telemetry corpus e reconstrução determinística.

A arquitetura funcional já existe; o objetivo agora é validar, não reabrir o desenho estrutural sem evidência.

A promoção de Product começa quando Ares atingir o seu critério de saída.

## #374 — Online

**Estado: BLOCKED UNTIL #373 CLOSES.**

Preparação pode decorrer em paralelo:

- servidor authoritative e command validation;
- session lifecycle;
- reconnect/recovery por replay/state reconstruction;
- time controls;
- matchmaking;
- rating/Elo separation;
- observability;
- security boundary.

O cliente nunca passa a ser autoridade de legalidade/final state. O contrato de observabilidade atual distingue DRAFT, onde o setup adversário é oculto, de BATALHA, onde o estado do combate é público e utilizável pela Ares.

## #375 — Release

**Estado: BLOCKED UNTIL #374 CLOSES.**

Preparação pode decorrer em paralelo:

- reproducible builds;
- dependency/security audit;
- licensing/provenance;
- failure/recovery QA;
- telemetry/logging;
- release candidate corpus.

Só a promoção final continua bloqueada por #374.

## Regras operacionais

Todo work package deve:

1. partir do `main` verificado;
2. trabalhar numa branch dedicada;
3. referenciar o issue canónico e o critério de aceitação;
4. implementar e testar antes do merge;
5. passar as gates aplicáveis do repositório;
6. atualizar a documentação canónica no mesmo pacote quando o estado mudou;
7. atualizar o issue com evidência concreta e fechar apenas após o resultado estar integrado em `main`.

### Paralelismo seguro

Quando existirem N work packages independentes:

```text
same baseline
├── package A
├── package B
├── package C
└── package D

→ test each independently
→ reject/accept independently
→ compose only accepted winners
→ revalidate the composition
```

Não fazer “mega-PRs” que misturam search, evaluator, gameplay e produto. A metodologia aplicada aqui privilegia patches focados e testes de uma ideia por vez.

Não criar outro roadmap para contornar esta sequência.
