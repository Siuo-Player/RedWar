# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `71bc812d170a8556b9dfde98b4f95202f36190b9`  
**Data:** 2026-09-08

Este é o **único documento que define a ordem operacional do trabalho**. Não duplicar esta fila em snapshots, branches, backlogs ou conversas.

## Vocabulário obrigatório

`DOCUMENTED` = descrito.  
`IMPLEMENTED` = existe no código alvo.  
`TESTED` = existe teste executável relevante.  
`VALIDATED` = foi submetido à validação apropriada para a alegação.  
`PROVEN` = a evidência é suficiente para a alegação específica sob o protocolo vigente.

Uma fase só pode ser `CLOSED` quando os critérios de aceitação forem satisfeitos no `main` e a evidência relevante estiver ligada aqui. CI verde é necessária para mudanças de código, mas **CI verde ≠ correctness total**, benchmark ≠ strength e melhoria de dataset ≠ melhoria de strength.

## Estado 2 — verificação paralela independente

Os lanes independentes foram executados a partir do baseline comum `1f65f65d6b4827f0d403d8e6d2bb0f735eda0c42` e merged apenas após CI da respetiva PR:

- **B #329** — regressão de determinismo para o audit emparelhado de strength; merged `29973ffb6e7d270ab8ccc9289307ab11e2f24506`.
- **C #330** — regressão que impede `fast_clone` no código C++ da Ares; merged `d08a700864d8ed0fe9dc274f8495a01f81105641`.
- **D #331** — regressão da codificação NNUE por perspetiva; merged `fdd1c3516e410b53608a95e554597a577ef6610e`.
- **E #332** — regressão de isolamento replay/telemetria; merged `d07f52f981de0eb0606bef1823beabca61348ae1`.
- **G #334** — fundação de sessão autoritativa server-side; merged `845b00a500fff7b3aab2f0c35920bace5d198cc6`.
- **F #333** — bounds do Auto-Pricer; o primeiro teste usava `100`, fora do contrato existente `0..64`; foi corrigido para `64`, rebaseado sobre o `main` atualizado e merged `71bc812d170a8556b9dfde98b4f95202f36190b9`.

Todos os seis lanes foram submetidos às três gates do repositório (`AI Quality Gate`, `Test Suite`, `CodeQL`) e a validação da cabeça final de F terminou com as três em `success` antes do merge. Estes resultados demonstram os contratos/regressões específicos de cada lane; **não fecham as fases B–G como um todo**.

A lane A desta tranche não foi artificialmente marcada como concluída: continua bloqueadora por A0.1.

# A — A0.1 Semantic Closure

**ID:** A0.1  
**Estado:** `OPEN — correctness/architecture blocker`.

### A.1 — authoritative execute legality

**Estado:** `OPEN / UNVERIFIED`.

Autoridade desejada:

```text
input action
→ normalize canonical action
→ action-space membership / canonical resolution
→ transition-domain validation
→ only then mutate
```

`legal_actions()` continua a representar o action-space canónico; `resolve_legal_action()` resolve entradas canónicas/legacy. As condições de transição de `GameState.make_action()` continuam autoridade para rejeições de domínio e não devem ser duplicadas em `legal_actions()`.

`fast_clone()` não é mecanismo de preflight nem autoridade de legalidade; continua permitido apenas em referência Python, replay, fixtures/property tests, tooling offline e comparação de estados, e não no hot path C++ da Ares.

**Aceitação A.1:** cobertura de todas as formas de execução aceites e intended-to-remain-compatible; membership canónico sem duplicação de regras; preservação de erros de domínio específicos; rejeição sem mutação observável; regressões legal/illegal; differential relevante verde.

A issue **#317** permanece a referência explícita para a lacuna entre action-space coverage e transition validity.

### A.2 — native repetition/history contract

**Estado:** `OPEN / ARCHITECTURAL DECISION REQUIRED`.

Definir explicitamente identidade de repetição, papel do TWC, ownership de history, interação com `make/unmake`, RWEN e search, e método de prova de equivalência.

**Gate de saída A:** A.1 e A.2 resolvidos, ou convertidos em fronteiras arquiteturais deliberadas, documentadas e testadas sem alegar uma equivalência inexistente.

**Próximo bloco:** B.

# B — Medição de força e calibração da Arena

**Estado:** `PARTIAL — infrastructure implemented; calibration not proven`.

**Pré-requisito:** A0.1 fechado para alterações dependentes da semântica.  
**Evidência relevante:** `STRENGTH_EVALUATION.md`, `ARENA_STATISTICAL_METHODOLOGY.md`, `ARENA_HOLDOUT_CI.md`, `ARENA_STRENGTH_DATASET.md`, mais #329 como regressão de determinismo do audit emparelhado.

**Aceitação:** protocolo reproduzível de `accept / reject / continue` para o regime real do RedWar, com unidade de resampling, condição experimental, incerteza e população explicitamente definidas.

**Não significa:** uma amostra dependente ou um run favorável torna-se automaticamente strength global.

# C — Ares: capability e eficiência de search

**Estado:** `BLOCKED by A0.1; then OPEN`.

Cada otimização precisa de regressão de correctness e benchmark controlado; alegações de strength exigem Arena A/B independente. #330 fixa uma fronteira arquitetural negativa importante: `fast_clone()` não pertence ao código C++ da Ares.

# D — NNUE

**Estado:** `INFRASTRUCTURE IMPLEMENTED; HOT-PATH INTEGRATION OPEN`.

Manter `sync_board()` como oracle até a integração incremental demonstrar equivalência. #331 adiciona uma regressão mínima sobre a codificação por perspetiva, mas **não** prova integração incremental nem benefício competitivo.

# E — Produto jogável: UI, replay e telemetria

**Estado:** `ARCHITECTURE IMPLEMENTED; VALIDATION OPEN`.

# F — Balanceamento

**Estado:** `DEPENDENT ON B AND RELEVANT DATA QUALITY`.

# G — Online / multiplayer

**Estado:** `FOUNDATION IMPLEMENTED; FULL CONTRACT OPEN`.

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

Toda PR deve declarar:

1. ID/fase do roadmap;
2. documento canónico que define o contrato;
3. hipótese ou correção;
4. tipo de evidência esperada;
5. critério de saída;
6. documentos canónicos atualizados no mesmo work package.

Não criar outro roadmap para contornar esta sequência.
