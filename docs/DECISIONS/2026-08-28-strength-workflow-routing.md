# Strength workflow routing for dedicated calibration runs

**Date:** 2026-08-28  
**Status:** accepted

## Discovery

A push to the dedicated Run B branch `experiment/strength/replication-seed-b-2026-08-28` triggered both the dedicated Seed B calibration workflow and the generic `RedWar Ares Strength Experiment` workflow.

The generic workflow matched the broad `experiment/strength/**` pattern. Its push defaults intentionally compare the branch head against `origin/main` using the canonical development seed set. That is a different experimental contract from the frozen Run B same-engine calibration.

The accidental generic run was technically valid as a separate Arena experiment, but it is not Run B evidence and must not be combined with the calibration analysis.

## Decision

Keep the generic workflow available for ordinary Ares experiment branches, but explicitly exclude the dedicated calibration branch family `experiment/strength/replication-seed-b-*` from its automatic push trigger.

Dedicated calibration workflows remain responsible for their own exact predeclared run identities, seeds, engine/rules revisions and provenance.

## Evidence boundary

The accidental generic experiment is retained as historical execution evidence but is excluded from calibration conclusions. In particular, its 50/50 result and raw rating output are not treated as evidence for Run B.

This routing fix changes only workflow selection. It does not change Arena semantics, rating calculations, statistical thresholds, seed values, or promotion criteria.
