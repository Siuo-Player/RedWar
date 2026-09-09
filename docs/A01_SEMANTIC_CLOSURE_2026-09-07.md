# RedWar — A0.1 Semantic Closure

**Status:** CLOSED  
**Current `main`:** `010b14b6251ce131409e660df95c6d920c76af58`  
**Data de reconciliação:** 2026-09-09

Este documento continua a ser a auditoria/contrato de transição de A0.1. Não substitui `CURRENT_STATE.md` nem `ROADMAP.md`; estes apontam para a sequência operacional atual.

## Distinção de evidência

Os estados usados abaixo têm este significado:

```text
DOCUMENTED → IMPLEMENTED → TESTED → VALIDATED → PROVEN (claim-specific)
```

A0.1 fecha apenas para os contratos que a evidência realmente cobre. Não constitui alegação de correctness total de todos os estados possíveis nem de strength competitiva.

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
| canonical action resolution seam | IMPLEMENTED / TESTED / CLOSED | #321 + #351 |
| generator → canonical action-space closure | TESTED / VALIDATED / CLOSED | #351 cobre o catálogo configurado e variantes de estado determinísticas |
| canonical ↔ legacy execution compatibility | TESTED / VALIDATED / CLOSED | #348 + #349 + #351 |
| domain-specific rejection/error contract | TESTED / VALIDATED / CLOSED | #350 + #352 |
| authoritative execute-time legality | IMPLEMENTED / TESTED / VALIDATED / CLOSED | #336 + #350 + #351 + #352 |
| native repetition/history | ARCHITECTURAL DECISION / TESTED BOUNDARY / CLOSED | #338 define `BoardState` como posição/search state e não como owner da sequência |

## 1. Autoridade de execução — FECHADA

A fronteira consolidada é:

```text
input action
   ↓
canonical normalize / resolve
   ↓
action-space membership / canonical compatibility
   ↓
transition-domain validation
   ↓
only then mutate
```

`legal_actions()` continua a derivar as ações dos geradores das peças; não existe uma segunda implementação das regras de herói no resolver. `resolve_legal_action()` trata a representação canónica/legacy e só aceita formas especiais não-exatas quando existe uma resolução canónica inequívoca. A validação de transição permanece em `GameState` e preserva erros específicos do domínio.

PR #336 removeu o bypass de SPELL não declarada. PR #350 fechou os bypasses equivalentes de STUN/SPAWN e consolidou o fail-closed action-space boundary. PR #351 verificou, para todos os heróis configurados e quatro variantes determinísticas de estado, que as ações geradas diretamente aparecem no action-space, atravessam normalização legacy e executam pela fronteira autoritativa. PR #352 fixa o contrato de rejeição e a não-mutação observável.

### Compatibilidade legacy

A compatibilidade não significa aceitar ações arbitrárias. O contrato atual é:

- representação legacy e `GameAction` são normalizadas para a mesma forma canónica;
- STUN legacy sem AOE explícita só é expandido quando existe exatamente uma ação canónica compatível;
- SPAWN/SPELL mantêm os seus payloads canónicos (`spawn_name` / `spell_name`);
- ações não pertencentes ao action-space não são executáveis por `execute_action()`;
- condições como alvo ocupado, silêncio e spell desconhecida mantêm os erros específicos já estabelecidos;
- uma rejeição não pode alterar RWEN, hash, histórico observável, turn, timers ou estado terminal.

### `fast_clone()`

`fast_clone()` não é mecanismo de preflight nem autoridade de legalidade. Mantém-se apenas em referência Python, replay, fixtures/property tests, tooling offline e comparação de estados; não entra no hot path C++ da Ares.

## 2. Repetition / threefold nativo — FECHADO COMO FRONTEIRA ARQUITETURAL

PR #338 estabeleceu que `BoardState` não deve possuir `state_history` mutável apenas para imitar a infraestrutura Python. A posição corrente é identificada por `hash`; `twc` permanece um componente distinto da semântica da posição. A sequência necessária para repetição pertence ao contexto de adjudicação/search que efetivamente possui a história.

A decisão fecha a obrigação arquitetural sem alegar equivalência threefold Python↔C++ que não foi demonstrada.

## Regra de saída

A0.1 está **CLOSED** porque as fronteiras que impediam prosseguir — action-space canónico, execução autoritativa, compatibilidade legacy, erros de domínio e limite arquitetural de repetition/history — têm agora contratos deliberados e evidência testável no `main` atual.

O próximo trabalho autorizado é B, segundo [`ROADMAP.md`](ROADMAP.md). Nenhuma alegação de strength, balance ou melhoria de Ares resulta apenas do fecho de A0.1.

Fonte operacional: [`ROADMAP.md`](ROADMAP.md). Estado resumido: [`CURRENT_STATE.md`](CURRENT_STATE.md). Raciocínio transversal: [`PROJECT_REASONING.md`](PROJECT_REASONING.md).
