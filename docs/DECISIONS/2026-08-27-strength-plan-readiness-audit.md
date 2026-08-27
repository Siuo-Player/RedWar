# Decision — Strength plan readiness audit

**Date:** 2026-08-27  
**Scope:** Strength replication/calibration experiment plan  
**Status:** accepted

## Discovery

After PR #142, Arena can receive an explicit ordered set of exactly 16 unique non-negative opening seeds and persists that set in experiment provenance.

The replication plan nevertheless had two separate readiness problems:

1. `ares-broader-population-v1` is named by the plan but no executable population/sampling artifact was found in the repository.
2. `ARES_HOLDOUT_V1.json` is a protected manifest of 8 explicit `(seed, opening_index)` cases, while the current Arena interface only accepts a homogeneous 16-seed opening set. Treating the 8 cases as though they were a 16-opening seed set would change the declared holdout population.

## Decision

Freeze only what is actually executable and leave non-executable runs explicitly blocked.

The current frozen calibration baseline is RedWar `main` at:

```text
81d018d3dd9d509e6ed1e4ba801adfab0d6fe5ef
```

For calibration runs A and B, challenger and baseline are intentionally the same frozen engine revision. These are measurement/calibration controls, not strength-improvement experiments.

The following seed sets are frozen:

- Run A `control-seed-set-a`: `101,211,307,401,503,601,709,809,907,1009,1103,1201,1301,1409,1501,1601`
- Run B `replication-seed-set-b`: `10091,10211,10307,10401,10503,10601,10709,10809,10907,11009,11103,11201,11301,11409,11501,11601`

Runs C and holdout remain blocked until their actual population contracts can be represented without approximation.

## Holdout preservation

The existing `data/validation/ARES_HOLDOUT_V1.json` remains authoritative for the protected holdout. Its cases must not be expanded, reordered, duplicated or padded merely to satisfy the current 16-opening Arena API.

Dedicated holdout execution support is therefore required before holdout data collection.

## Consequence

The next executable experiment is Run A, followed by Run B, using the same frozen engine/rules revision and only the predeclared seed variation.

No Strength promotion, uncertainty-model replacement, SPRT activation or search/NNUE optimization follows automatically from these runs.
