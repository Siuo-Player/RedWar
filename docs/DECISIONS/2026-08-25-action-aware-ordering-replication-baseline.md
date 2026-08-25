# Discovery / Decision — Action-aware ordering replication baseline

**Date:** 2026-08-25  
**Related experiment:** action-aware history/killer ordering  
**Initial Arena:** 14–6 (+8) in 20 games at 10,000 nodes

## Discovery

The action-aware ordering change has since been merged into `main`. The long-run strength workflow originally used `origin/main` as its baseline.

That is unsafe for a historical replication: if the challenger branch still contains the action-aware ordering change and `main` already contains it, challenger and baseline become semantically identical.

## Decision

The long-run strength experiment must accept an explicit `baseline_ref` input and resolve it to an immutable commit SHA before building the baseline.

- `origin/main` remains the default for ordinary future experiments.
- Historical replications must pin the exact pre-change commit.
- The action-aware ordering replication baseline is `a58aad8`.

## Validation rule

A strength experiment is invalid when challenger and baseline resolve to the same commit SHA. The workflow should reject that configuration before starting games.

## Consequence

The next 100-game replication must compare:

- challenger: `feat/arena-action-aware-ordering-2026-08-25`
- baseline: `a58aad8`
- nodes: `10000`
- games: `100`

No implementation changes to Ares are allowed between the 20-game result and this replication.