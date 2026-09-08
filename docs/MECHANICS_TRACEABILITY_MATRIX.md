# RedWar — Mechanics Traceability Matrix

Esta matriz é o gate de integração de mecânicas. O significado operacional e a ordem de uso estão em [`PROJECT_REASONING.md`](PROJECT_REASONING.md); a fila de trabalho está em [`ROADMAP.md`](ROADMAP.md).

## Cadeia obrigatória

```text
configuration
→ Python rules
→ C++ rules
→ legal actions
→ state transition
→ RWEN
→ make
→ unmake
→ hash
→ differential
→ regression/property
→ tactical/semantic benchmark when applicable
```

## Interpretação dos estados

`✓` significa que existe caminho implementado e cobertura documentada. Não significa que qualquer combinação futura de estados esteja provada.

`targeted` significa que a mecânica necessita de fixtures dirigidos porque sequências aleatórias podem não atingir o caso raro.

## Current A0.1 emphasis

Os contratos já explicitamente reforçados incluem:

- special-spell legality (`#303`);
- canonical action boundary (`#291`, `#306`, `#308`);
- Inquisitor active-vs-stunned silence (`#292`);
- terminal semantics / native alpha-beta (`#310`);
- lifecycle/TWC/effects/spawn-cooldown/special transition coverage;
- explicit make/unmake root restoration.

Os pontos que não devem ser marcados como semanticamente fechados sem nova evidência são:

- execute-time authority contra ações ilegais antes da mutação;
- história/repetição nativa equivalente.

## Completion rule

Uma nova mecânica só é `complete` quando a cobertura relevante demonstra geração, transição, reversibilidade, representação e paridade de backend; quando a mecânica altera decisões da Ares, acrescenta-se capability benchmark.

Não usar esta matriz isoladamente para declarar força da engine.
