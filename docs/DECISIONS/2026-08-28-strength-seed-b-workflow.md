# Strength Run B — dedicated execution workflow

**Date:** 2026-08-28  
**Status:** accepted

## Discovery

The generic Strength experiment workflow is intentionally configurable and is not sufficient to execute the frozen `replication-v3` Run B because its default push behaviour compares a branch head against `origin/main`. The calibration protocol instead requires a same-engine control with a predeclared run identity and seed-set B.

## Decision

Add a dedicated `strength_calibration_seed_b.yml` workflow triggered only by the exact `experiment/strength/replication-seed-b-2026-08-28` branch.

The workflow hard-codes only the execution controls already frozen in `data/arena/strength/plans/2026-08-27-replication-v3.json`:

- run: `strength-calibration-2026-08-27-seed-replication`;
- 100 paired games;
- 10,000 nodes;
- `stratified-opening-scenarios-v1` selection policy;
- `Ares-v1-vs-baseline-v1` controller population;
- `fixed-node-budget` skill context;
- identical challenger/baseline frozen SHA;
- `replication-seed-set-b` validated from the plan.

The existing generic workflow remains available for explicit/manual experiments. No production engine, Arena semantics, rating model, uncertainty model or promotion authority is changed.

## Evidence boundary

Run B is a new calibration run because its seed context differs from Run A. It must not be started until Run A's raw evidence is retained and inspected. The branch contains no model-tuning change and no promotion decision.
