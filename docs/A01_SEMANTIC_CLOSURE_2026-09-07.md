# RedWar — A0.1 Semantic Closure

**Status:** OPEN  
**Current `main`:** `e17afcd54ad57635e222f3b3c9a5bb9966df9394`  
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
| canonical action resolution seam | IMPLEMENTED / TESTED | #321 — `resolve_legal_action()` centraliza resolução exacta e compatibilidade legacy STUN |
| authoritative execute-time legal membership | DOCUMENTED / UNVERIFIED / OPEN | #317 aberta; #309/#315 não foram merged |
| native repetition/history | DOCUMENTED / UNVERIFIED / OPEN | não existe contrato equivalente estabelecido no `BoardState` |

## Ainda aberto

### 1. Autoridade de execução

A normalização e resolução canónica agora têm um seam explícito, mas a garantia forte desejada ainda não deve ser considerada fechada. A fronteira deve distinguir action-space de transition validity:

```text
input action
   ↓
canonical normalize / resolve
   ↓
action-space membership
   ↓
transition-domain validation
   ↓
only then mutate state
```

`resolve_legal_action()` não substitui as validações específicas de `GameState.make_action()`. Essas validações devem ocorrer antes de `gerar_notacao()`, `last_move` e demais mutações observáveis quando uma transição for rejeitada.

`fast_clone()` não é mecanismo de preflight nem autoridade de legalidade. Mantém-se apenas como ferramenta auxiliar em referência Python, replay, fixtures/property tests, tooling offline e comparação de estados; não entra no hot path C++ da Ares.

### 2. Repetition / threefold nativo

Python mantém `state_history`. O `BoardState` nativo não possui ainda um equivalente definido no mesmo nível de contrato. Antes de implementar deve ser decidido:

- o que constitui identidade de repetição;
- se TWC faz parte da identidade;
- se history pertence à posição, ao search context ou à adjudicação;
- como `make/unmake`, RWEN e search interagem com history;
- como provar a equivalência escolhida.

## Regra de saída

A0.1 só fecha quando as duas fronteiras abertas forem resolvidas, ou quando forem transformadas explicitamente em contratos arquiteturais deliberados e testados que deixem de exigir a alegação de equivalência atualmente ausente.

A existência deste documento não autoriza search tuning, NNUE tuning, strength claims ou balance changes por si só.

Fonte operacional: [`ROADMAP.md`](ROADMAP.md). Estado resumido: [`CURRENT_STATE.md`](CURRENT_STATE.md). Raciocínio transversal: [`PROJECT_REASONING.md`](PROJECT_REASONING.md).
