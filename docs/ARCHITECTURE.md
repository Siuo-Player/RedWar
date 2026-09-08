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

**Verificado no `main` atual (`e17afcd54ad57635e222f3b3c9a5bb9966df9394`):**

- a fronteira canónica `GameAction` está implementada e a entrada de `execute_action()` é normalizada (#306/#308);
- `resolve_legal_action()` foi introduzido e testado no #321 para centralizar resolução exacta e compatibilidade legacy STUN;
- terminal, special-spell legality, Inquisitor silence/stun e vários outros contratos têm regressões explícitas (#292/#303/#310);
- repetição Python tem observação idempotente (#299).

**Ainda não provado/implementado no `main`:**

- `execute_action()` rejeitar canonical legal actions fora do action-space e manter separadas as validações específicas da transição antes da mutação;
- ausência de mutação observável para todos os caminhos de rejeição relevantes;
- um contrato nativo de repetition/history equivalente à história Python.

O boundary de A.1 é explicitamente:

```text
input
  ↓
canonical normalization / resolution
  ↓
action-space membership
  ↓
transition-domain validation
  ↓
mutation
```

`legal_actions()` continua responsável pelo action-space derivado das primitivas de peças; `GameState.make_action()` continua autoridade de transição. Não transformar nenhum dos dois numa cópia do outro.

`fast_clone()` não é parte dessa autoridade. É permitido como ferramenta auxiliar fora do execution/search boundary; em particular, não é preflight de `execute_action()` nem componente do hot path C++ Ares.

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
