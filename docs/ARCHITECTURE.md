# RedWar — Architecture

## Current authority

A arquitetura atual é uma arquitetura de pequeno projeto com complexidade sistémica: regras Python, Ares C++, validação diferencial, Arena/Strength, NNUE, UI/replay e futura camada online.

[`CURRENT_STATE.md`](CURRENT_STATE.md) identifica o baseline atual; [`ROADMAP.md`](ROADMAP.md) define a sequência; este documento define as fronteiras arquiteturais.

## Núcleo

```text
rules / state
      ↓
canonical actions
      ↓
Python reference ───── differential ───── C++ Ares
      ↓                                      ↓
product semantics                         search/eval
      ↓                                      ↓
replay / telemetry                    Arena / strength
```

A duplicação Python/C++ é dívida controlada. Enquanto ambos forem usados para regras/engine, mudanças que atravessem essa fronteira exigem evidence diferencial apropriada.

## Invariantes alvo

1. Mesma posição → mesmas ações legais.
2. `make → unmake` restaura posição e metadados relevantes.
3. Regras terminais são equivalentes nos backends quando o contrato exigir.
4. Timers, efeitos, stun, lifespan, cooldown e TWC mantêm a mesma semântica.
5. Serialização/RWEN permanece estável e sem ambiguidade.
6. NNUE recebe as mesmas features para a mesma posição observável.

## Estado A0.1

**Verificado no `main` atual:**

- a fronteira canónica `GameAction` está implementada e a entrada de `execute_action()` é normalizada (#306/#308);
- terminal, special-spell legality, Inquisitor silence/stun e vários outros contratos têm regressões explícitas (#292/#303/#310);
- repetição Python tem observação idempotente (#299).

**Ainda não provado/implementado no `main`:**

- `execute_action()` rejeitar canonical legal actions fora do conjunto legal **antes da mutação**; #309 e #315 não foram merged;
- um contrato nativo de repetition/history equivalente à história Python.

Não promover a intenção arquitetural a facto implementado apenas porque existe um PR ou um decision record.

## Implemented vs proven

```text
IMPLEMENTED
= comportamento presente no código alvo

TESTED
= existe regressão executável para a propriedade

VALIDATED
= a propriedade foi exercida pelo método de validação adequado

PROVEN
= a evidência é suficiente para a alegação específica feita
```

O desenho arquitetural pode ser um **intended invariant** antes de ser um invariant plenamente provado em todo o espaço de estados.

## Modularidade

Search, evaluator, NNUE, Arena e UI permanecem separados da autoridade das regras. Ferramentas experimentais não devem duplicar `GameState` nem inventar uma segunda linguagem de regras.

## Critério de mudança

Uma alteração arquitetural deve declarar:

```text
fronteira afetada
→ contrato
→ evidência atual
→ dependências
→ testes
→ efeito esperado
→ critério de saída
→ próximo gate
```

Consultar [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md) para mudanças que atravessam regras, estado ou backends.
