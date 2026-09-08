# Ares — AI Engine

## Authority

Este documento é o contrato técnico atual da Ares. [`CURRENT_STATE.md`](CURRENT_STATE.md) identifica o baseline verificável; [`ROADMAP.md`](ROADMAP.md) define a ordem de evolução; [`PROJECT_REASONING.md`](PROJECT_REASONING.md) define a cadeia de evidência.

## Current baseline

**Baseline:** `main` @ `b1aadb8a26d8af0e80839e0149b693d6ca710f40`.

Ares usa C++ no hot path e mantém:

- alpha-beta/PVS;
- iterative deepening;
- transposition table;
- Zobrist hashing;
- move ordering;
- killer/history heuristics;
- quiescence/tactical search;
- node/time bounded search.

Ares é um engine de RPG táctico, não uma implementação de xadrez. O estado observável inclui peças, stun, lifespan, spawn cooldown, efeitos, TWC e lado a jogar.

## Semantic contract before search

A invariância alvo é:

```text
mesma posição → mesmas ações legais
make → unmake → mesma posição/metadados relevantes
mesmas condições terminais
mesma semântica de timers/efeitos/TWC
```

No `main` atual, a fronteira `GameAction`/normalização está implementada e testada (#306/#308). Isto **não** prova ainda que o executor rejeite todas as ações ilegais antes da mutação: #309 e #315 não foram merged.

Terminal, special-spell legality e Inquisitor silence/stun têm regressões explícitas (#292/#303/#310). Estas são propriedades específicas TESTED/VALIDATED; não equivalem a “semantic closure completa”.

## Search

A pesquisa permanece separada do evaluator. Move ordering e pruning devem explorar fenómenos reais de RedWar — capturas, stun, spells forçantes, passivas, lifespan/cooldown e TWC — e cada alteração deve ser estudada como hipótese isolada.

Não copiar heurísticas de outras engines apenas por existirem. O critério é ganho demonstrável no fenómeno pretendido, sem regressão semântica e com o nível de evidência adequado ao claim.

## Evaluation

A avaliação clássica permanece baseline de compatibilidade/correção. Contém material, PST, stun, lifespan, TWC e termos específicos de RedWar.

Uma limitação conhecida do evaluator é uma **hipótese de investigação**, não prova de “balanceamento errado”.

## NNUE

NNUE é opcional. As features atuais representam peça+quadrado+equipa relativa, stun, lifespan, cooldown, efeitos, TWC e side-to-move.

O caminho de integração continua:

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

Os hooks incrementais existem, mas a integração não é considerada concluída até a igualdade com `sync_board()` ser testada no caminho real de mutação.

## Benchmarks

`tools/analytics/tactical_benchmark_suite.py` é um capability/regression harness.

```text
benchmark result
≠
global strength proof
```

Uma melhoria num caso FrostMage ou noutro puzzle é evidência de capability específica. Generalização e strength exigem os seus próprios instrumentos.

## Strength

A separação operacional é:

```text
correctness
→ capability
→ performance
→ independent validation
→ strength
```

Um bestmove melhor, maior NPS ou menor training loss não autoriza por si só uma alegação de aumento global de força.

## Observabilidade

No modo local documentado, `DRAFT` mantém informação do adversário oculta e `BATALHA` expõe o estado completo. Ares só pode usar a informação permitida pelo modo em questão.

Fonte: [`OBSERVABILITY_CONTRACT.md`](OBSERVABILITY_CONTRACT.md).
