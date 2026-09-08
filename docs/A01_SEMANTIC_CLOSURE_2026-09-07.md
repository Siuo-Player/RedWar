# RedWar — A0.1 Semantic Closure

**Status:** OPEN  
**Current `main`:** `b1aadb8a26d8af0e80839e0149b693d6ca710f40`  
**Data de reconciliação:** 2026-09-08

Este documento continua a ser a auditoria/contrato de transição de A0.1. Não substitui `CURRENT_STATE.md` nem `ROADMAP.md`; estes apontam para a sequência operacional atual.

## Distinção de evidência

Os estados usados abaixo têm este significado:

```text
DOCUMENTED → IMPLEMENTED → TESTED → VALIDATED → PROVEN (claim-specific)
```

A0.1 não fecha por acumulação de testes isolados. Uma propriedade fechada é fechada apenas para o contrato que a evidência realmente cobre.

## Matriz reconciliada

| Fronteira | Estado atual | Evidência |
|---|---|---|
| Inquisitor silence/stun | TESTED / CLOSED | #292 compara C3 oracle, Python e native move generation |
| terminal semantics | TESTED / CLOSED | #310 observa o score do `alpha_beta()` nativo real |
| special-spell legality | TESTED / CLOSED | #303 cobre as special actions declaradas |
| canonical `GameAction` boundary | IMPLEMENTED / TESTED / CLOSED | #306 |
| `execute_action()` canonical normalization | IMPLEMENTED / TESTED / CLOSED | #308 |
| Python repetition observation | IMPLEMENTED / TESTED / CLOSED | #299 |
| FrostMage unreachable legacy block | IMPLEMENTED / TESTED / CLOSED | #300 + AST regression |
| fixed node-budget semantics | TESTED / CLOSED | cobertura dedicada do contrato |
| authoritative execute-time legal membership | DOCUMENTED / UNVERIFIED / OPEN | #309 e #315 estão fechadas sem merge |
| native repetition/history | DOCUMENTED / UNVERIFIED / OPEN | não existe contrato equivalente estabelecido no `BoardState` |

## Fechado

### Inquisitor silence/stun

O contrato foi explicitamente comparado entre o C3 oracle, Python e native move generation: um Inquisitor inimigo atordoado não fornece silêncio. PR #292 transformou essa descoberta em regressão explícita.

### Terminal semantics

PR #310 faz a regressão observar o score do `alpha_beta()` real, cobrindo as classes terminais definidas naquele contrato e o controlo TWC=49. O contrato externo de root terminal continua `bestmove 0000`.

### Special-spell legality

PR #303 estabeleceu uma comparação determinística das special actions entre geradores Python, oracle e native C++. FrostMage `NEVADA` permanece `SPELL`, não um segundo mecanismo escondido de `STUN`.

### Canonical action boundary

PR #291 consolidou a análise de MOVE/ATTACK/STUN/SPAWN/SPELL. PR #306 tornou `engine.legal_actions` a fronteira canónica e #308 passou `execute_action()` pela normalização canónica antes da transição existente.

### Repetition observation

PR #299 corrigiu a observação repetida do mesmo hash em Python para que chamadas idempotentes de `check_game_over()` não fabriquem ocorrências.

### Legacy code

PR #300 removeu o bloco FrostMage inalcançável depois de a implementação ativa ter regressões suficientes.

## Ainda aberto

### 1. Autoridade de execução

No `main` atual, `GameState.execute_action()` normaliza a entrada para `GameAction`, mas ainda não existe a verificação canónica de membership que impeça uma ação ilegal de chegar à mutação. Os PRs que tentaram fechar esse boundary (#309 e #315) não foram merged.

Regra alvo:

```text
input action
   ↓
canonical normalize
   ↓
canonical legal-action membership
   ↓
only then mutate
```

Não considerar este ponto fechado apenas porque existe normalização.

### 2. Repetition / threefold nativo

Python mantém `state_history`. A implementação mostrada no `main` também mantém essa informação no `GameState` Python, mas a análise não encontrou um equivalente de history no `BoardState` nativo. Isto continua uma **fronteira de arquitetura**, não uma autorização para uma implementação ad hoc.

Antes de implementar deve ser decidido:

- o que constitui identidade de repetição;
- se TWC faz parte da identidade;
- se history pertence à posição, ao search context ou a adjudicação externa;
- como `make/unmake`, RWEN e search interagem com history;
- como provar a equivalência escolhida.

## Regra de saída

A0.1 só fecha quando as duas fronteiras abertas forem resolvidas, ou quando forem transformadas explicitamente em contratos arquiteturais deliberados e testados que deixem de exigir a alegação de equivalência atualmente ausente.

A existência deste documento não autoriza search tuning, NNUE tuning, strength claims ou balance changes por si só.

Fonte operacional: [`ROADMAP.md`](ROADMAP.md). Estado resumido: [`CURRENT_STATE.md`](CURRENT_STATE.md). Raciocínio transversal: [`PROJECT_REASONING.md`](PROJECT_REASONING.md).
