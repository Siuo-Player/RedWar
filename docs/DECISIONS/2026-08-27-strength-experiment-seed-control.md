# Decision — explicit seed control for Strength replication

**Date:** 2026-08-27  
**Scope:** Strength/Arena experiment infrastructure  
**Status:** accepted

## Context

The active Strength replication protocol requires intentional variation between experiment runs, including new seed sets. The current Arena workflow invokes `arena_tournament.py` without a seed-generation input, while the tournament derives its opening state from the fixed opening-book seeds.

Therefore a branch run cannot currently satisfy the planned `replication-seed-set-b` condition merely by changing its branch or commit.

## Problem

Using the same opening/seed conditions across runs would create nominal replication without the intended experimental-condition variation. That would not provide the evidence the calibration protocol asks for.

## Decision

Add explicit, reproducible seed control to the Arena experiment path before executing the next calibration batch.

The seed rule must:

- be explicit in the experiment configuration;
- be deterministic from a declared base seed/generation rule;
- preserve paired colour inversion within each pair;
- allow distinct seed sets across runs;
- be retained in experiment provenance;
- not change the production game rules or Strength estimator.

The opening/scenario selection and seed generation remain separate controls. A new seed set must not silently redefine the opening population.

## Evidence

The current `arena_tournament.py` calls `run_headless_match(..., opening_index)` without supplying an alternate seed, causing `run_headless_match` to load the opening-book seed. The active replication protocol explicitly requires new seeds between runs.

## Consequences

Positive: the planned multi-run experiment becomes reproducible and capable of testing between-run variation intentionally.

Cost: the experiment CLI/workflow must carry and persist the seed policy, and regression tests are required.

## Validation

Before real calibration data are collected:

1. verify deterministic seed generation for a fixed configuration;
2. verify different declared seed sets produce different opening seeds;
3. verify the two members of each colour-inverted pair share the same opening seed;
4. verify experiment metadata records the seed-generation policy;
5. keep promotion disabled.

Only after these checks pass should the `replication-v3` Arena runs be executed.