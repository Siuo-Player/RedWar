# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `b1aadb8a26d8af0e80839e0149b693d6ca710f40`  
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

A0 histórico passou. Os seguintes blocos já estão merged e servem de base: #292, #299, #300, #303, #306, #308 e #310.

### Evidência base

- #299 — observação de repetição Python idempotente; o próprio PR preserva explicitamente o native history gap.
- #300 — remoção do bloco FrostMage inalcançável, sem alteração da mecânica ativa.
- #303 — special-spell legality parity.
- #306 — fronteira canónica `GameAction`.
- #308 — `execute_action()` normaliza para `GameAction`, preservando a compatibilidade legacy.
- #310 — terminal regression observa o `alpha_beta()` nativo real.
- #309 — não merged: contrato proposto para autoridade de legalidade no executor.
- #315 — não merged: tentativa posterior do mesmo boundary; não deve ser tratada como implementação presente.

### Documentos canónicos

- [`ARCHITECTURE.md`](ARCHITECTURE.md)
- [`HERO_SYSTEM.md`](HERO_SYSTEM.md)
- [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md)
- [`AI_ENGINE.md`](AI_ENGINE.md)
- [`A01_SEMANTIC_CLOSURE_2026-09-07.md`](A01_SEMANTIC_CLOSURE_2026-09-07.md)

> `A01_SEMANTIC_CLOSURE_2026-09-07.md`: “Não considerar este ponto fechado apenas porque `execute_action()` aceita `GameAction`.”

### Trabalho

**A.1 — authoritative execute legality**  
Estado: `OPEN / UNVERIFIED`.

A autoridade desejada é:

```text
input action
→ normalize canonical action
→ canonical legal-action membership
→ only then mutate state
```

### Aceitação A.1

- uma ação estruturalmente válida mas ilegal é rejeitada **antes** de qualquer mutação observável;
- a legalidade é derivada da autoridade canónica existente, sem duplicar regras por tipo de ação;
- inputs legacy continuam compatíveis quando legalmente equivalentes;
- legal e illegal paths têm regressão executável;
- differential relevante permanece verde.

**Gate:** apenas fechar A.1 quando a alteração estiver merged e testada no `main`.

**A.2 — native repetition/history contract**  
Estado: `OPEN / ARCHITECTURAL DECISION REQUIRED`.

Documentar e decidir explicitamente:

- identidade de repetição;
- papel do TWC nessa identidade;
- se history pertence à posição, ao search context ou a uma camada de adjudicação;
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

> `AI_BENCHMARK_PROTOCOL.md`: “Uma alteração de search que melhora apenas este benchmark fica classificada como `capability improved` até existir evidência de generalização e, para uma afirmação de força, Arena A/B.”

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

> `NNUE.md`: “A existência desses hooks não significa integração concluída.”

### Trabalho

- ligar hooks às mutações reais de `BoardState`;
- provar `incremental accumulator == full resync` após sequências e make/unmake;
- manter `sync_board()` como oracle;
- medir custo/evaluation/NPS;
- auditar dataset teacher, leakage e duplicação antes de conclusões de treino;
- comparar força em Arena.

### Nota sobre #314 / #316

#314 (`research: harden NNUE dataset validation...`) não foi merged: as alterações de split/auditoria aí propostas não são implementação atual do `main`. #316 foi merged e **apenas** classifica a estreita classe de metodologia de dataset na CI separadamente da promoção de strength.

> #316: “The deterministic build/diagnostic steps remain available; only the strength-promotion requirement is disabled for this narrowly defined maintenance class.”

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

> `BATTLE_UI_SIDEBAR.md`: “O trabalho restante é **validação visual/UX**, não redesenho arbitrário da arquitetura.”

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

> `BALANCE_METHODOLOGY.md`: “pricing heuristic ≠ global power estimate ≠ design judgement”.

### Aceitação

Uma alteração de balanceamento tem correctness, evidência de desenvolvimento controlada, validação protegida quando aplicável, análise contextual e decisão de design explícita.

**Não significa:** Auto-Pricer output ≠ causal hero power.

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
