# RedWar — Strength control self-play baseline

**Date:** 2026-08-27  
**Status:** accepted methodological correction  
**Scope:** `ai_strength_experiment.yml` / replication-v3 Run A

## Context

The active calibration plan defines Run A as a controlled replication with the same Ares revision on both sides. Its purpose is to measure Arena noise/variation under the fixed experimental conditions before interpreting changes between different engine revisions.

The Strength workflow previously rejected any experiment where the challenger and baseline resolved to the same commit. That made the declared Run A impossible to execute.

## Decision

The workflow now resolves two explicit engine references:

```text
baseline_ref
challenger_ref
```

and derives their concrete commit SHAs before building either engine.

Identical SHAs are allowed when explicitly requested. This is a **control/self-play experiment**, not evidence that a new revision is stronger.

The existing default remains unchanged for normal experiments:

```text
challenger = workflow commit
baseline   = origin/main
```

## Rationale

The same-engine control is required to estimate experimental variation under the same search/evaluation semantics. Rejecting identical revisions conflated:

```text
same engine / control condition
```

with:

```text
invalid A/B comparison
```

They are methodologically different cases.

## Validation boundary

The workflow records the resolved challenger and baseline SHAs in the Arena provenance. No production Ares/search/evaluation code is changed.

Run A remains non-promotional. Its result can calibrate variation and validate the experimental pipeline, but cannot by itself support a strength-improvement claim.
