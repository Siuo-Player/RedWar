# RPG Move-Ordering Baseline

This benchmark isolates search-ordering changes from evaluation changes.

## Goal

Measure whether Ares finds the same tactically correct action with fewer nodes after move-ordering changes. The board position, rules, evaluation and node budgets remain fixed.

## Method

Use the existing deterministic tactical benchmark cases and run a denser node scan than the normal exponential scan. The first reference case is `frostmage-5-target`.

Suggested scan:

```text
10, 25, 50, 75, 100, 150, 200, 300, 500, 1000
```

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

## Baseline command

```text
python tools/analytics/move_ordering_baseline.py --case frostmage-5-target --trace
```

The baseline should be recorded before each ordering optimization so improvements are expressed as a lower node threshold rather than simply a different move.
