# Ares — AI Engine

## Authority

Este documento é o contrato técnico atual da Ares. [`CURRENT_STATE.md`](CURRENT_STATE.md) identifica o baseline verificável; [`ROADMAP.md`](ROADMAP.md) define a ordem de evolução; [`PROJECT_REASONING.md`](PROJECT_REASONING.md) define a cadeia de evidência.

## Current baseline

**Baseline:** `main` @ `3e8bbe9417b584b5a4208d18852070f578bb8b77` (2026-09-10).

Ares usa C++ no hot path e mantém:

- alpha-beta/PVS;
- iterative deepening;
- transposition table;
- Zobrist hashing;
- move ordering;
- killer/history heuristics;
- quiescence/tactical search;
- node/time bounded search;
- optional NNUE.

Ares é um engine de RPG táctico, não uma implementação de xadrez. O estado relevante inclui peças, stun, lifespan, spawn cooldown, efeitos, TWC e lado a jogar.

## Semantic contract before search

A fronteira canónica consolidada é:

```text
input action
→ normalize / canonical resolution
→ action-space membership
→ transition-domain validation
→ only then mutate
```

A action-space canónico e a terminação sem ações usam `engine.legal_actions` como autoridade quando essa decisão depende da existência de ações de tabuleiro. `surrender` é uma ação terminal canónica não enumerada no action-space de tabuleiro.

A fronteira foi exercida por regressões Python e comparações com o backend nativo para os contratos abrangidos. Isto fecha uma autoridade específica; não afirma cobertura matemática de todos os estados possíveis.

`fast_clone()` não é componente do hot path C++ nem mecanismo aceite de preflight de legalidade. Continua limitado a tooling/reference Python.

## Search

A pesquisa permanece separada do evaluator. Move ordering e pruning devem explorar fenómenos reais de RedWar — capturas, stun/segundo-stun, spells forçantes, passivas, lifespan/cooldown, terreno e TWC — e cada alteração deve ser estudada como hipótese isolada.

Não copiar heurísticas de outras engines apenas por existirem. O critério é ganho demonstrável no fenómeno pretendido, sem regressão semântica e com o nível de evidência adequado ao claim.

## Evaluation

A avaliação clássica permanece o baseline experimental atual. A composição exata e as regras de comparação estão documentadas em [`ARES_CLASSICAL_EVALUATION_BASELINE.md`](ARES_CLASSICAL_EVALUATION_BASELINE.md).

Uma limitação conhecida do evaluator é uma hipótese de investigação, não prova de “balanceamento errado”.

## NNUE

NNUE é opcional. As features atuais representam peça+quadrado+equipa relativa, stun, lifespan, cooldown, efeitos, TWC e side-to-move.

A integração incremental nativa foi exercida contra `sync_board()` no caminho real de make/unmake pelo PR #356. `sync_board()` continua como oracle/recovery path.

O principal problema de performance a investigar no gate #372 é que `evaluate_board()` ainda chama `sync_board()` antes de cada inferência NNUE. A hipótese é medir o custo e, apenas mantendo paridade exata, permitir que o acumulador incremental seja usado diretamente no hot path.

```text
full-sync oracle
→ incremental accumulator
→ make/unmake parity
→ controlled cost benchmark
→ matched-budget search comparison
→ Arena
```

## Benchmarks

`tools/analytics/tactical_benchmark_suite.py` é um capability/regression harness.

O modo normal deve demonstrar pelo menos:

```text
bestmove exists
+ bestmove parses
+ bestmove belongs to canonical legal action-space
```

O modo `--strict-choice` é deliberadamente mais forte e deve ser tratado como evidência estilo-strength, não como requisito de capability genérica.

```text
benchmark result
≠
global strength proof
```

Uma melhoria num caso FrostMage ou noutro puzzle é evidência de capability específica. Generalização e strength exigem instrumentos próprios.

## Strength

A separação operacional é:

```text
correctness
→ capability
→ controlled performance
→ independent validation
→ strength
```

Um bestmove melhor, maior NPS, maior profundidade, maior dataset ou menor training loss não autoriza por si só uma alegação de aumento global de força.

## Current Ares gate

#372 é a gate ativa após o fecho de #371 Gameplay. O plano preparatório está em [`ARES_EXECUTION_PLAN.md`](ARES_EXECUTION_PLAN.md), governado por #406.

A promoção exige correctness/regressions, capability determinística, performance controlada e evidência Arena independente. NNUE só passa a default se houver benefício demonstrado de força/eficiência.

## Observability

No modo local documentado, `DRAFT` mantém informação do adversário oculta e `BATALHA` expõe o estado completo. Ares só pode usar a informação permitida pelo modo em questão.

Fonte: [`OBSERVABILITY_CONTRACT.md`](OBSERVABILITY_CONTRACT.md).
