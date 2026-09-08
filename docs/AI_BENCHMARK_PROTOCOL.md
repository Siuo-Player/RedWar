# RedWar — AI Benchmark Protocol

Este documento define o que um benchmark pode provar e o que não pode provar. A regra operacional completa está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md) e [`ROADMAP.md`](ROADMAP.md).

## Classes de evidência

```text
regression
→ known failure não regressa

capability
→ a Ares encontra/evita um comportamento específico

performance
→ custo, NPS, nodes ou profundidade mudam sob condições controladas

generalisation
→ capacidade não depende apenas das posições usadas no tuning

strength
→ comportamento competitivo melhora contra baseline sob Arena controlada
```

Estas classes não são equivalentes.

## Estrutura de um benchmark

Cada cenário deve conter:

- posição RWEN canónica;
- objetivo táctico/semântico explícito;
- solução de referência obtida com orçamento suficientemente alto;
- budgets de teste;
- failure threshold;
- trace opcional para diagnóstico;
- versão das regras e da engine.

## Anti-overfitting

Uma suite pequena e fixa pode ser extremamente útil como regression/capability probe, mas não deve ser usada como prova única de força. Expandir a cobertura por mecânicas e, quando possível, usar posições independentes ou derivadas de jogos reais.

## Gate

Uma alteração de search que melhora apenas este benchmark fica classificada como `capability improved` até existir evidência de generalização e, para uma afirmação de força, Arena A/B.

## Relação com o roadmap

- Fase A usa benchmarks apenas para fechar comportamento/correctness.
- Fase C usa benchmarks para search capability/performance.
- Fase B e a parte final de C usam Arena para força.
- Fase D usa benchmarks para custo/paridade NNUE e Arena para strength.
