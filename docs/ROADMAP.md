# RedWar — Roadmap Operacional

**Baseline operacional:** `main` @ `010b14b6251ce131409e660df95c6d920c76af58`  
**Data:** 2026-09-09

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

**Estado histórico:** `PARTIAL` no início da tranche; **agora CLOSED**.

PR #336 eliminou o bypass de SPELL estruturalmente válido mas não declarado pelo herói. PR #350 fechou os bypasses equivalentes de STUN/SPAWN e consolidou a regra de que ações especiais não enumeradas pelo action-space não atravessam a resolução canónica para execução. PR #351 fez a cobertura de action-space sobre todos os heróis configurados em variantes de estado determinísticas: as ações produzidas diretamente pelos geradores das peças têm de aparecer no `legal_actions()`, ser reproduzíveis pela normalização legacy e executar através de `execute_action()` num clone isolado de teste. PR #352 fechou o contrato de erros de domínio e a garantia de não-mutação em rejeição.

**Estado final:** `IMPLEMENTED / TESTED / VALIDATED / CLOSED` para a fronteira `execute_action()` + action-space canónico e os contratos legacy cobertos. A geração continua na implementação das peças; não foi criada uma segunda fonte de regras no resolver.

Autoridade consolidada:

```text
input action
→ normalize canonical action
→ canonical resolution / membership
→ transition-domain validation
→ only then mutate
```

`fast_clone()` não é mecanismo de preflight nem autoridade de legalidade e continua fora do hot path C++ da Ares.

### A.2 — native repetition/history contract

**Estado:** `CLOSED AS ARCHITECTURAL BOUNDARY`.

PR #338 foi merged como `21cef6afb5556d991d9a0f111ca2de42874ffc09`. `BoardState` permanece a representação da posição/search state; a sequência necessária para repetição pertence ao contexto que realmente possui a história. Isto não constitui uma alegação de equivalência threefold Python↔C++.

## Estado 4 — A0.1 / A.1: EVIDÊNCIA REFORÇADA

PR #343 consolidou os erros específicos de transição e a segurança de não-mutação. PR #344 adicionou paridade representativa entre `engine.legal_actions()` e um oracle independente em 11 heróis.

Estas eram evidências parciais quando #317 ainda estava aberto. Foram posteriormente complementadas por #351 e #352, pelo que os seus limites já não constituem o estado operacional atual de A0.1.

## Estado 7 — A0.1 / A.1: ACTION-SPACE CLOSURE — FECHADO

**PR #351**, branch `state7/A01-actionspace-completeness-2026-09-09`, foi merged em `385a5bdcb53adb93a0477ef98f82ebd7596c6879` após `RedWar AI Quality Gate #668`, `RedWar CodeQL #637` e `RedWar Test Suite #1835` verdes.

A evidência cobre:

- catálogo completo de heróis configurados;
- estados empty/enemy-pressure/ally-pressure/mixed-pressure;
- geradores de MOVE/ATTACK/STUN/SPAWN/SPELL como fonte independente do teste;
- projeção desses resultados para o action-space canónico;
- resolução legacy equivalente;
- execução pela fronteira autoritativa `execute_action()`;
- STUN legacy sem AOE explícita;
- projeção apenas do herói sob teste quando existem outras peças com ações legítimas no tabuleiro.

## Estado 8 — A0.1 / A.1: DOMAIN ERROR CONTRACT — FECHADO

**PR #352**, branch `state8/A01-legacy-error-contract-2026-09-09`, foi merged em `010b14b6251ce131409e660df95c6d920c76af58` após `RedWar AI Quality Gate #669`, `RedWar CodeQL #639` e `RedWar Test Suite #1838` verdes.

A matriz de rejeição cobre SPAWN ocupado, SPELL desconhecida, silêncio de Inquisitor, ação não enumerada e origem sem peça, assegurando os erros específicos do domínio e a não-mutação observável.

### Gate A0.1 atual

**A0.1 — CLOSED.**

A fundação semântica necessária para prosseguir para B está agora fechada nos contratos deliberados acima. Isto não prova correctness matemático de cada estado possível nem strength competitivo; significa que o blocker estrutural que impedia trabalho dependente foi encerrado com evidência executável e merged em `main`.

# B — Medição de força e calibração da Arena

**Estado:** `PARTIAL — infrastructure implemented; calibration not proven`.

É o próximo bloco operacional autorizado. A infraestrutura de Arena e os audits existentes permanecem sujeitos aos respetivos protocolos de população, provenance, incerteza e hold-out.

# C — Ares: capability e eficiência de search

**Estado:** `OPEN after A0.1; correctness first`. Cada otimização exige regressão de correctness e benchmark controlado; qualquer alegação de strength exige Arena A/B independente. `fast_clone()` não pertence ao código C++ da Ares.

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
A0.1 Semantic Closure  [CLOSED]
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
