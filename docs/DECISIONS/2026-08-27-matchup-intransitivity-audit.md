# Decision — matchup/context intransitivity audit

**Date:** 2026-08-27

## Decision

Add a descriptive analyzer that combines valid Arena results across multiple A/B experiments and summarizes directional matchup/context performance.

The analyzer may report a descriptive three-way cycle such as:

```text
A > B
B > C
C > A
```

but it must not interpret the cycle as causal evidence, a calibrated uncertainty interval, or a promotion/rejection decision.

## Rationale

A single global Elo-compatible rating can hide context-dependent performance. RedWar already records challenger/baseline versions, opening, seed, color and population context in Arena experiments. These fields are sufficient to construct conditional matchup summaries without changing the production rating estimator.

The first implementation therefore remains deliberately descriptive. It is an explanatory diagnostic that can reveal when a global strength number may be masking matchup structure or intransitivity.

## Constraints

- Only valid declared-strength games are included.
- Matchup direction is preserved rather than collapsing A-vs-B and B-vs-A into one count.
- Context fields are explicit and configurable.
- Intransitivity requires a minimum number of games per directed edge.
- A score rate above 0.5 is treated only as a descriptive directional edge.
- No promotion gate or production strength estimator consumes this result yet.

## Next step

Collect several real Arena comparisons among more than two Ares/controller versions or relevant populations, then inspect whether the observed matchup graph contains stable context-dependent structure. Only after that empirical validation should an inferential model be considered.
