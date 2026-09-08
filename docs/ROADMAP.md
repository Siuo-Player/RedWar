# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `c93a6c659451b86d9d32d73b5f5a1ba66a879f2f`  
**Data:** 2026-09-08

Este é o **único documento que define a ordem operacional do trabalho**. Não duplicar esta fila em snapshots, branches, backlogs ou conversas.

## Vocabulário obrigatório

`DOCUMENTED` = descrito.  
`IMPLEMENTED` = existe no código alvo.  
`TESTED` = existe teste executável relevante.  
`VALIDATED` = foi submetido à validação apropriada para a alegação.  
`PROVEN` = a evidência é suficiente para a alegação específica sob o protocolo vigente.

Uma fase só pode ser `CLOSED` quando os critérios de aceitação forem satisfeitos no `main` e a evidência relevante estiver ligada aqui. CI verde é necessária para mudanças de código, mas **CI verde ≠ correctness total**, benchmark ≠ strength e melhoria de dataset ≠ melhoria de strength.

## Estado 2 — verificação paralela independente: FECHADO

Os seis lanes independentes foram executados a partir do baseline comum `1f65f65d6b4827f0d403d8e6d2bb0f735eda0c42` e merged apenas após as três gates do repositório:

- **B #329** — determinismo do audit emparelhado; merged `29973ffb6e7d270ab8ccc9289307ab11e2f24506`.
- **C #330** — ausência de `fast_clone` no C++ da Ares; merged `d08a700864d8ed0fe9dc274f8495a01f81105641`.
- **D #331** — encoding NNUE por perspetiva; merged `fdd1c3516e410b53608a95e554597a577ef6610e`.
- **E #332** — isolamento replay/telemetria; merged `d07f52f981de0eb0606bef1823beabca61348ae1`.
- **F #333** — bounds do Auto-Pricer; primeiro fixture inválido corrigido de `100` para o limite existente `64`; rebaseado e merged `71bc812d170a8556b9dfde98b4f95202f36190b9`.
- **G #334** — fundação de sessão autoritativa server-side; merged `845b00a500fff7b3aab2f0c35920bace5d198cc6`.

As PRs acima tiveram `AI Quality Gate`, `Test Suite` e `CodeQL` verdes antes do respetivo merge. Isto fecha a tranche de infraestrutura/regressões, não as fases B–G completas.

## Estado 3 — A0.1: FECHADO COMO FRONTEIRAS DELIBERADAS; BLOCKER DE COBERTURA REMANESCENTE

### A.1 — authoritative execute legality

**Estado:** `PARTIAL — boundary hardened; full action-space closure still OPEN`.

PR #336 foi merged como `ecefc111a4068848373167d4e59e68ac9a002464`. A implementação passou a rejeitar SPELLs cujo nome não é declarado pelo herói de origem, usando o catálogo canónico `HERO_DEFS`; isto elimina um bypass sem copiar regras de alvo para o resolver. A validação de domínio de `GameState` continua a ser a autoridade para condições específicas de transição.

A primeira versão de #336 falhou em três testes porque tratava a lista exata de targets de `get_valid_spells()` como única fonte de compatibilidade; isso quebrou o fixture legacy `aimed_shot` e a capitalização histórica `Nevada`. A versão final corrigiu ambos sem reintroduzir `fast_clone()` ou duplicação de regras e terminou com as três gates verdes.

**Ainda aberto:** issue **#317** exige cobertura completa de todas as formas de execução intencionalmente aceites (`MOVE/ATTACK/STUN/SPAWN/SPELL`) e equivalência entre enumeração canónica e fixtures legacy. Enquanto essa matriz não estiver fechada, `execute_action()` não deve ser tratado como membership-only enforcement total.

Autoridade pretendida:

```text
input action
→ normalize canonical action
→ action-space resolution / membership where complete
→ transition-domain validation
→ only then mutate
```

`fast_clone()` continua fora de preflight e fora do hot path C++ da Ares.

### A.2 — native repetition/history contract

**Estado:** `CLOSED AS ARCHITECTURAL BOUNDARY`.

PR #338 foi merged como `21cef6afb5556d991d9a0f111ca2de42874ffc09`. A decisão canónica em `DECISIONS/2026-09-08-native-repetition-boundary.md` estabelece que `BoardState` não passa a possuir `state_history` mutável só para imitar a infraestrutura Python. A identidade/contagem de repetição pertence ao contexto de adjudicação que possui a sequência; `hash` representa a posição corrente e `twc` permanece distinto.

Isto fecha a necessidade de uma **decisão arquitetural**, mas **não** declara equivalência threefold Python↔C++.

## Estado 4 — A0.1 / A.1: EVIDÊNCIA REFORÇADA; BLOCKER #317 AINDA ABERTO

O baseline de Estado 4 começou em `21cef6afb5556d991d9a0f111ca2de42874ffc09` e terminou no `main` `c93a6c659451b86d9d32d73b5f5a1ba66a879f2f`.

- **PR #343** — contrato de rejeição de transições + segurança de não-mutação em erro. A cobertura verifica, entre outros casos, SPAWN em casa ocupada, SPELL bloqueado por silêncio de Inquisitor e SPELL desconhecido; os erros específicos do domínio são preservados e o estado RWEN não é alterado. Merged em `20b7022f88ae49deceaaeac5b0a94aee730e99ee` após as três gates verdes.
- **PR #344** — paridade representativa entre `engine.legal_actions(state)` e um oracle independente em `tools/analytics/legal_action_oracle.py`, cobrindo MOVE/ATTACK/SPELL/SPAWN em 11 heróis representativos e sem usar geradores de `Piece` como oracle. Merged em `c93a6c659451b86d9d32d73b5f5a1ba66a879f2f` após `RedWar AI Quality Gate #655`, `RedWar Test Suite #1791` e `RedWar CodeQL #615` verdes.

**Interpretação da evidência:** Estado 4 demonstra paridade representativa e preservação dos contratos de erro/mutação, mas **não fecha #317**. O oracle ainda é uma cobertura independente representativa, não uma enumeração provada de toda a superfície historicamente aceite; permanecem necessárias a matriz exaustiva de `MOVE/ATTACK/STUN/SPAWN/SPELL`, as variantes especiais/legacy e a reconciliação completa entre ações canónicas e fixtures aceites.

### Gate A0.1 atual

A0.1 permanece **OPEN apenas por A.1/#317**. A.2 continua **CLOSED AS ARCHITECTURAL BOUNDARY**.

**Próximo estado:** fechar a cobertura canónica/executável de A.1 sem duplicar regras, começando pela matriz completa de ações/variantes que `execute_action()` deve aceitar ou rejeitar explicitamente.

# B — Medição de força e calibração da Arena

**Estado:** `PARTIAL — infrastructure implemented; calibration not proven`.

Pré-requisito operacional: remover o blocker A.1 quando a alteração depender da semântica de execução. A infraestrutura de Arena e o audit emparelhado têm regressões de determinismo, mas isso não transforma dataset/run em prova de strength global.

# C — Ares: capability e eficiência de search

**Estado:** `BLOCKED by A0.1; then OPEN`.

Cada otimização exige regressão de correctness e benchmark controlado; qualquer alegação de strength exige Arena A/B independente. `fast_clone()` não pertence ao código C++ da Ares.

# D — NNUE

**Estado:** `INFRASTRUCTURE IMPLEMENTED; HOT-PATH INTEGRATION OPEN`.

`sync_board()` continua oracle até integração incremental demonstrar equivalência. O teste #331 protege a codificação por perspetiva, não prova benefício competitivo.

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
