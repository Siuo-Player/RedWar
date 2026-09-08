# RedWar — Architecture

## Current authority

A arquitetura do RedWar é uma arquitetura de pequeno projeto com complexidade sistémica: regras Python, Ares C++, validação diferencial, Arena/Strength, NNUE, UI/replay e futura camada online.

A ordem causal entre estas áreas está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md). Este documento define as fronteiras arquiteturais.

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

A duplicação Python/C++ é uma dívida controlada: enquanto existir, qualquer mudança semântica que atravesse ambos precisa de differential evidence.

## Invariantes

1. Mesma posição → mesmas ações legais.
2. `make → unmake` restaura posição e metadados relevantes.
3. Regras terminais são equivalentes nos backends quando o contrato exigir.
4. Timers, efeitos, stun, lifespan, cooldown e TWC mantêm a mesma semântica.
5. Serialização/RWEN permanece estável e sem ambiguidade.
6. NNUE recebe as mesmas features para a mesma posição observável.

## Estado A0.1

A0 foi fechado como gate histórico. A0.1 continua porque:

- o executor ainda precisa de uma autoridade explícita que rejeite ação ilegal antes da mutação;
- repetição/threefold ainda necessita de um contrato nativo de history, em vez de uma implementação ad hoc.

Não tratar estas pendências como “bugs já corrigidos”.

## Modularidade

Search, evaluator, NNUE, Arena e UI devem permanecer separados da autoridade das regras. Ferramentas experimentais não devem duplicar `GameState` nem inventar uma segunda linguagem de regras.

## Critério de mudança

Uma alteração arquitetural deve declarar:

```text
fronteira afetada
→ contrato
→ dependências
→ testes
→ efeito esperado
→ próximo gate
```

Consultar [`PROJECT_DEVELOPMENT_METHODOLOGY.md`](PROJECT_DEVELOPMENT_METHODOLOGY.md) para a decomposição e [`MECHANICS_TRACEABILITY_MATRIX.md`](MECHANICS_TRACEABILITY_MATRIX.md) para mudanças de mecânicas.
