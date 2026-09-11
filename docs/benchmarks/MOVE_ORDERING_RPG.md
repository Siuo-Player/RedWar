# RPG Move-Ordering Baseline

This benchmark isolates search-ordering changes from evaluation changes.

## Goal

Measure whether Ares finds the same tactically correct action with fewer nodes after move-ordering changes. The board position, rules, evaluation and node budgets remain fixed.

## Method

Use the existing deterministic tactical benchmark cases and run a denser node scan than the normal exponential scan.

Default scan:

```text
10, 25, 50, 75, 100, 150, 200, 300, 500, 1000
```

The baseline runner can measure one case or the complete tactical corpus. Capability mode validates that the engine returns a non-null legal action at each budget; it does not promote that action to a strength claim.

Examples:

```text
python tools/analytics/move_ordering_baseline.py --case frostmage-5-target --trace
python tools/analytics/move_ordering_baseline.py --all-cases --output logs/benchmarks/move-ordering-baseline.json
```

The JSON artifact uses schema version `1` and records the cases, node budgets, per-budget bestmove, canonical legality, elapsed time, return code, and the captured suite output. This makes repeated baselines comparable without scraping console output manually.

For every change to move ordering, compare:

- expected tactical action;
- minimum budget at which the action is found;
- best move at each budget;
- search trace when the threshold changes;
- full tests and Arena result.

## What is allowed to change

Move ordering may use state information already available to search, such as:

- number of affected enemy pieces;
- value of affected pieces;
- whether a target is already stunned and therefore close to the two-stun kill rule;
- immediate spell impact;
- history/TT information.

These are ordering heuristics only. They must not directly change the static evaluation score.

## What is not allowed

Do not encode the coordinates, board layout, hero name, or benchmark-specific solution into the ordering code.

A tactical benchmark is evidence, not a special case.

The baseline runner itself must remain measurement-only: it must not patch engine state, alter search parameters, or inject benchmark-specific moves.
