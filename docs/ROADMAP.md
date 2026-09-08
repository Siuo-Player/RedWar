# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `e17afcd54ad57635e222f3b3c9a5bb9966df9394`  
**Data:** 2026-09-08

Este é o **único documento que define a ordem operacional do trabalho**. Não duplicar esta fila em snapshots, branches, backlogs ou conversas.

## Como usar esta fila

Cada bloco segue a mesma estrutura:

```text
ID
→ OBJECTIVO
→ PORQUÊ
→ ESTADO
→ PRÉ-REQUISITOS
→ EVIDÊNCIA BASE
→ DOCUMENTOS CANÓNICOS
→ ACEITAÇÃO
→ PRÓXIMO BLOCO
```

### Vocabulário obrigatório

`DOCUMENTED` = descrito.  
`IMPLEMENTED` = existe no código alvo.  
`TESTED` = existe teste executável relevante.  
`VALIDATED` = foi submetido à validação apropriada para a alegação.  
`PROVEN` = a evidência é suficiente para a alegação específica sob o protocolo vigente.

Não promover um estado para outro sem evidência.

### Regra de gate

Uma fase só pode ser marcada `CLOSED` quando os critérios de aceitação dessa fase forem satisfeitos no `main` e a evidência relevante estiver ligada aqui. CI verde é necessária para mudanças de código, mas **CI verde ≠ correctness total**, benchmark ≠ strength e melhoria de dataset ≠ melhoria de strength.

---

# A — A0.1 Semantic Closure

**ID:** A0.1  
**Objetivo:** fechar as últimas fronteiras de autoridade semântica entre ação, execução e histórico de repetição antes de aceitar trabalho dependente delas.  
**Porquê:** a Ares usa regras/estado duplicados em Python e C++; qualquer ambiguidade residual pode produzir comportamento divergente ou invalidar medições posteriores.  
**Estado:** `OPEN — correctness/architecture blocker`.

### Pré-requisitos

A0 histórico passou. Os seguintes blocos já estão merged e servem de base: #292, #299, #300, #303, #306, #308, #310 e #321.

### Evidência base

- #299 — observação de repetição Python idempotente; o próprio PR preserva explicitamente o native history gap.
- #300 — remoção do bloco FrostMage inalcançável, sem alteração da mecânica ativa.
- #303 — special-spell legality parity.
- #306 — fronteira canónica `GameAction`.
- #308 — `execute_action()` normaliza para `GameAction`, preservando a compatibilidade legacy.
- #310 — terminal regression observa o `alpha_beta()` nativo real.
- #321 — `resolve_legal_action()` centraliza a resolução exacta e a compatibilidade legacy STUN; merged no `main` atual `e17afcd…`.
- #309 — não merged: contrato proposto para autoridade de legalidade no executor.
- #315 — não merged: tentativa posterior do mesmo boundary; a CI expôs que action-space não cobre todo o contrato de transição/compatibilidade.
- #317 — issue aberta que formaliza a lacuna entre action-space e transition validity.

### Documentos canónicos

- [`ARCHITECTURE.md`](ARCHITECTURE.md)
- [`HERO_SYSTEM.md`](HERO_SYSTEM.md)
- [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md)
- [`AI_ENGINE.md`](AI_ENGINE.md)
- [`A01_SEMANTIC_CLOSURE_2026-09-07.md`](A01_SEMANTIC_CLOSURE_2026-09-07.md)
- [`DECISIONS/2026-09-08-execution-boundary-no-fast-clone.md`](DECISIONS/2026-09-08-execution-boundary-no-fast-clone.md)

> `A01_SEMANTIC_CLOSURE_2026-09-07.md`: a normalização/resolução canónica não fecha por si só a autoridade de execução.

### Trabalho

**A.1 — authoritative execute legality**  
Estado: `OPEN / UNVERIFIED`.

A fronteira deve distinguir explicitamente dois predicados:

```text
canonical action-space resolution
        ↓
transition-domain validation
        ↓
only then mutate state
```

`legal_actions()` continua a representar o action-space canónico produzido pelas primitivas de peças. `resolve_legal_action()` resolve uma entrada para a representação canónica/legacy quando ela pertence a esse espaço. Condições de transição existentes em `GameState.make_action()` continuam a ser autoridade para rejeições de domínio e não devem ser duplicadas em `legal_actions()`.

O executor não deve usar `fast_clone()` para preflight. `fast_clone()` permanece ferramenta auxiliar de referência/replay/testes offline e não é parte da autoridade Ares.

### Aceitação A.1

- uma ação fora do action-space é rejeitada antes de qualquer mutação observável;
- ações canónicas e inputs legacy equivalentes resolvem através de `resolve_legal_action()`;
- uma ação no action-space que falhe uma condição específica de transição é rejeitada pelo contrato de `GameState`, preservando o erro de domínio;
- nenhuma validação de execução depende de clone especulativo;
- rejeições deixam board, hash e metadata observável inalterados;
- legal e illegal paths têm regressão executável;
- differential relevante permanece verde;
- nenhum novo hardcoding por herói é introduzido no adapter de ações.

**Gate:** apenas fechar A.1 quando a alteração estiver merged e testada no `main`.

**A.2 — native repetition/history contract**  
Estado: `OPEN / ARCHITECTURAL DECISION REQUIRED`.

Documentar e decidir explicitamente:

- identidade de repetição;
- papel do TWC nessa identidade;
- se history pertence à posição, ao search context ou à adjudicação;
- interação de history com `make/unmake`, RWEN e search;
- como a equivalência deve ser provada.

**Aceitação A.2:** decisão explícita + implementação, se necessária, + regressões + diferencial adequado. Uma implementação ad hoc não fecha o gate.

**Gate de saída A:** A.1 e A.2 resolvidos, ou convertidos em fronteiras arquiteturais deliberadas, documentadas e testadas sem alegar uma paridade que não existe.

**Próximo bloco:** B — Strength measurement/calibration.

---

# B — Medição de força e calibração da Arena

**ID:** B  
**Objetivo:** tornar a medição competitiva suficientemente calibrada para suportar decisões de strength.  
**Porquê:** a infraestrutura existente já mede; ainda falta demonstrar que o regime experimental, a incerteza e o contexto suportam decisões robustas.  
**Estado:** `PARTIAL — infrastructure implemented; calibration not proven`.

### Pré-requisitos

A0.1 fechado para alterações que dependam da semântica de jogo. Instrumento de Arena/hold-out utilizável.

### Evidência base

- [`STRENGTH_EVALUATION.md`](STRENGTH_EVALUATION.md)
- [`ARENA_STATISTICAL_METHODOLOGY.md`](ARENA_STATISTICAL_METHODOLOGY.md)
- [`ARENA_HOLDOUT_CI.md`](ARENA_HOLDOUT_CI.md)
- [`ARENA_STRENGTH_DATASET.md`](ARENA_STRENGTH_DATASET.md)

> `STRENGTH_EVALUATION.md`: “Um benchmark, uma métrica de treino ou um run isolado não substituem Arena.”

> `ARENA_STATISTICAL_METHODOLOGY.md`: `50 paired game units ≠ 50 independent experimental conditions`.

### Trabalho

- replicar experiências preservando commit, regras, budget, cor, opening/seed e validade;
- separar unidade de resampling de condição experimental independente;
- medir estabilidade por população/contexto e procurar intransitividade sem tratá-la como facto estratégico;
- calibrar incerteza do rating;
- validar operating characteristics do SPRT com draws, invalidez e dependência real;
- manter hold-out protegido e raw Arena provenance.

### Aceitação

Existe protocolo reproduzível de `accept / reject / continue` para o regime real do RedWar, com incerteza e população explicitamente definidas.

**Não significa:** um resultado favorável numa amostra dependente torna-se automaticamente strength global.

**Próximo bloco:** C — Ares capability/efficiency.

---

# C — Ares: capability e eficiência de search

**ID:** C  
**Objetivo:** melhorar a pesquisa sem alterar silenciosamente a semântica do jogo.  
**Porquê:** depois de correctness e instrumentação de força, search pode ser otimizado com hipóteses mensuráveis.  
**Estado:** `BLOCKED by A0.1; then OPEN`.

### Pré-requisitos

A0.1 fechado. B com instrumento de medição operacional quando uma alegação de strength for feita.

### Evidência base / documentos

- [`AI_ENGINE.md`](AI_ENGINE.md)
- [`AI_BENCHMARK_PROTOCOL.md`](AI_BENCHMARK_PROTOCOL.md)
- [`ENGINEERING_METHODOLOGY_AND_RESEARCH.md`](ENGINEERING_METHODOLOGY_AND_RESEARCH.md)

> [`AI_BENCHMARK_PROTOCOL.md`](AI_BENCHMARK_PROTOCOL.md): uma melhoria apenas no benchmark permanece capability evidence até haver generalização e, para força, Arena A/B.

### Aceitação por alteração

Cada otimização precisa de:

- regressão de correctness;
- benchmark de capability/performance controlado;
- Arena A/B independente quando a afirmação for de strength.

**Próximo bloco:** D — NNUE incremental/evaluation quality.

---

# D — NNUE

**ID:** D  
**Objetivo:** integrar e avaliar NNUE no hot path sem perder uma referência de correção verificável.  
**Porquê:** os hooks existem, mas a existência da infraestrutura não prova integração incremental correta nem benefício competitivo.  
**Estado:** `INFRASTRUCTURE IMPLEMENTED; HOT-PATH INTEGRATION OPEN`.

### Documentos canónicos

- [`NNUE.md`](NNUE.md)
- [`AI_ENGINE.md`](AI_ENGINE.md)
- [`AI_BENCHMARK_PROTOCOL.md`](AI_BENCHMARK_PROTOCOL.md)

### Trabalho

- ligar hooks às mutações reais de `BoardState`;
- provar `incremental accumulator == full resync` após sequências e make/unmake;
- manter `sync_board()` como oracle;
- medir custo/evaluation/NPS;
- auditar dataset teacher, leakage e duplicação antes de conclusões de treino;
- comparar força em Arena.

### Nota sobre #314 / #316

#314 não foi merged: as alterações aí propostas não são implementação atual do `main`. #316 foi merged e apenas classifica a estreita classe de metodologia de dataset NNUE na CI separadamente da promoção de strength.

**Aceitação:** paridade incremental/full-resync provada + benchmark de custo + treino reproduzível + evidência competitiva suficiente para a alegação feita.

**Próximo bloco:** E — produto jogável/replay/telemetria.

---

# E — Produto jogável: UI, replay e telemetria

**ID:** E  
**Objetivo:** validar e endurecer a camada jogável já implementada.  
**Estado:** `ARCHITECTURE IMPLEMENTED; VALIDATION OPEN`.

### Documentos canónicos

- [`BATTLE_UI_SIDEBAR.md`](BATTLE_UI_SIDEBAR.md)
- `REPLAY_STORAGE.md`
- documentação de telemetria

### Aceitação

UI validada nos tamanhos suportados e estados de interação; keyboard/focus verificados; cenas determinísticas cobertas; replay reproduzível e telemetria com provenance.

**Próximo bloco:** F — Balance/state-of-game.

---

# F — Balanceamento

**ID:** F  
**Objetivo:** converter dados válidos em decisões de balanceamento contextual sem tratar heurísticas como oráculos.  
**Estado:** `DEPENDENT ON B AND RELEVANT DATA QUALITY`.

### Documentos canónicos

- [`BALANCE_METHODOLOGY.md`](BALANCE_METHODOLOGY.md)
- `BALANCE_STATE_OF_GAME_AUDIT.md`
- [`ARENA_STATISTICAL_METHODOLOGY.md`](ARENA_STATISTICAL_METHODOLOGY.md)

**Próximo bloco:** G — online/server-authoritative.

---

# G — Online / multiplayer

**ID:** G  
**Objetivo:** evoluir para multiplayer com servidor autoritativo sem reabrir ambiguidades do núcleo.  
**Estado:** `FUTURE / DEPENDS ON STABLE ACTION-STATE CONTRACT`.

### Documento canónico

- `WEB_MULTIPLAYER.md`
- [`OBSERVABILITY_CONTRACT.md`](OBSERVABILITY_CONTRACT.md)

### Aceitação

Servidor autoritativo sobre legalidade, estado, resultado e RNG relevante; reconexão, timeout, rematch e histórico definidos por contrato.

---

# Ordem global

```text
A0.1 Semantic Closure
        ↓
B — Strength measurement / calibration
        ↓
C — Ares search capability + efficiency
        ↓
D — NNUE incremental + evaluation quality
        ↓
E — UI / replay / telemetry validation
        ↓
F — Balance / state-of-game audit
        ↓
G — Server-authoritative online
```

UI/replay pode avançar em paralelo quando não atravessar um correctness blocker. A ordem acima é a sequência operacional; um gate de correctness bloqueia trabalho dependente mesmo que outro benchmark ou feature tenha evoluído.

## Regra de referência para cada PR

A PR deve declarar:

1. ID/fase do roadmap;
2. documento canónico que define o contrato;
3. hipótese ou correção;
4. tipo de evidência esperada;
5. critério de saída;
6. documentos canónicos atualizados no mesmo work package.

Não criar outro roadmap para contornar esta sequência.
