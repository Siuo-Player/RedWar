# Ares — AI Engine

## Authority

Este documento é o contrato técnico atual da Ares. A ordem de evolução está em [`ROADMAP.md`](ROADMAP.md); o raciocínio transversal está em [`PROJECT_REASONING.md`](PROJECT_REASONING.md).

## Current baseline

Ares usa C++ no hot path e mantém:

- alpha-beta/PVS;
- iterative deepening;
- transposition table;
- Zobrist hashing;
- move ordering;
- killer/history heuristics;
- quiescence/tactical search;
- node/time bounded search.

Ares é um engine de RPG táctico, não uma implementação de xadrez. O estado inclui peças, stun, lifespan, spawn cooldown, efeitos, TWC e lado a jogar.

## Semantic contract before search

Ares depende destes invariantes:

```text
mesma posição → mesmas ações legais
make → unmake → mesma posição
mesmas condições terminais
mesma semântica dos timers/efeitos/TWC
```

A fronteira canónica Python foi consolidada por #291/#306/#308. A0.1 ainda mantém dois pontos abertos: autoridade de legalidade no próprio executor antes de mutar o estado e contrato nativo de repetição/history.

A cobertura especial de Inquisitor, special spells e terminal score foi explicitamente reforçada por #292/#303/#310.

## Search

A pesquisa continua independente do evaluator. O move ordering deve explorar fenómenos reais de RedWar — capturas, stun, spells forçantes, passivas, lifespan/cooldown e TWC — e cada mudança deve ser estudada como hipótese isolada.

Não copiar heurísticas de outras engines apenas por existirem. O critério é ganho demonstrável no fenómeno pretendido sem regressão semântica.

## Evaluation

A avaliação clássica permanece baseline de compatibilidade/correção. Contém material, PST, stun, lifespan, TWC e termos específicos de RedWar.

A avaliação não deve fingir representar exatamente o valor táctico total de todas as mecânicas. Uma limitação conhecida do evaluator não é uma prova de “balanceamento errado”; é uma hipótese para investigação posterior.

## NNUE

NNUE é opcional. As features atuais representam peça+quadrado+equipa relativa, stun, lifespan, cooldown, efeitos, TWC e side-to-move.

O caminho correto é:

```text
full resync
   ↓
incremental accumulator
   ↓
paridade make/unmake
   ↓
benchmark de custo/NPS
   ↓
Arena
```

Os hooks incrementais existem, mas a integração não deve ser considerada concluída até que a igualdade com `sync_board()` seja testada no caminho real de mutação.

## Benchmarks

`tools/analytics/tactical_benchmark_suite.py` é um capability/regression harness. FrostMage é um caso de referência, não uma medida da força global.

Os benchmarks devem ser distribuídos pela taxonomia de mecânicas e incluir estados independentes/derivados de jogos reais quando possível.

## Strength

A Arena mede força global sob condições controladas. A separação é:

```text
correctness
→ capability
→ performance
→ independent validation
→ strength
```

Um melhor bestmove num benchmark, maior NPS ou menor training loss não autoriza uma afirmação de aumento global de força.

## Observabilidade

No modo local documentado, `DRAFT` mantém informação do adversário oculta e `BATALHA` expõe o estado completo. Ares só pode usar a informação permitida pelo modo em questão.

Fonte: [`OBSERVABILITY_CONTRACT.md`](OBSERVABILITY_CONTRACT.md).
