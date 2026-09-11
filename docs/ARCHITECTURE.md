# RedWar — Architecture

## Papel

Este documento define fronteiras e invariantes arquiteturais. O estado implementado é autoridade do código e dos testes; [`ROADMAP.md`](ROADMAP.md) define a sequência de evolução.

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

Python e C++ podem coexistir como backends de referência e produção, mas uma mudança que atravesse a fronteira deve preservar a semântica comum e usar evidência diferencial quando aplicável.

## Invariantes

1. Mesma posição → mesmas ações legais.
2. `make → unmake` restaura posição e metadados relevantes.
3. Regras terminais mantêm a semântica definida pelo ruleset.
4. Timers, efeitos, stun, lifespan, cooldown e TWC têm semântica consistente.
5. Serialização/RWEN é estável e sem ambiguidade.
6. NNUE recebe as mesmas features para a mesma posição observável.

## Limites importantes

A fronteira de execução é:

```text
input
→ canonical normalization / resolution
→ action-space membership
→ transition validation
→ mutation
```

`legal_actions()` descreve o action-space; a execução valida a transição concreta antes de mutar. `fast_clone()` é ferramenta auxiliar e não autoridade de legalidade, preflight ou hot path C++.

## Estados de evidência

```text
IMPLEMENTED
TESTED
VALIDATED
PROVEN
```

Uma propriedade documentada não se torna automaticamente uma propriedade provada.

## Regra de mudança

Qualquer mudança arquitetural deve declarar a fronteira afetada, o contrato, as dependências, a validação e o critério de saída. Detalhes transitórios de PR/commit pertencem ao Git e aos Issues, não a este documento.
