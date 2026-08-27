# RedWar — Strength replication and calibration protocol

**Date:** 2026-08-27  
**Source:** `Siuo-Player/Siuo-Player-PROJECT-STUDIES/REDWAR/RESEARCH_INBOX/2026-08-27-strength-replication-and-calibration-protocol.md`  
**Status:** active roadmap/methodology guardrail

## Decision

The next Strength block is **replication and calibration**, not search/NNUE optimisation and not replacement of the current rating model.

The first persistent control contains:

```text
100 games = 50 complete colour-inverted pairs
             ≠ 50 independent experimental conditions
```

Because opening/seed combinations are reused, the evidence is conditional on the manifest-defined experimental population.

## Frozen batch contract

Each calibration batch must have one shared `experiment_id` and freeze, before any results are inspected:

```text
engine/rules versions
compute budget
opening/scenario sampling rule
seed-generation rule
colour-pairing rule
validity/termination rules
primary outcome
primary statistic
planned diagnostics
hold-out policy
```

Run-specific `seed_policy` and `population_id` may vary intentionally to test replication and context variation. Changing a frozen field requires a new protocol version rather than silent reinterpretation of the same observations.

## Required experimental structure

Prefer several intentional runs rather than one homogeneous large run. At minimum, future batches should distinguish:

```text
controlled replication
+ new seeds
+ broader/stratified openings or scenarios
+ broader population coverage
```

The evidence hierarchy must remain explicit:

```text
raw game → paired unit → experiment run → population/stratum
```

Statistical resampling must respect the dependence structure at the level being claimed.

## Required evidence

A calibration batch must retain provenance sufficient to identify challenger, baseline and rules versions, run and experiment identifiers, pair, colour, opening/scenario, seed, compute budget, outcome, validity, termination reason and population identifier.

The raw Arena record remains the source of truth; derived datasets are analytical views.

Primary analyses should include paired effect, between-run stability, context effects and legitimate draw behaviour. A paired-bootstrap percentile interval remains descriptive until its inferential calibration is established; it must not automatically be labelled `IC95%`.

At least one later run, stratum or predeclared subset should remain available as hold-out evidence for model refinements.

## Current RedWar implementation

`tools/analytics/strength_calibration_protocol.py` implements `redwar-strength-calibration-protocol-v3` and validates the frozen batch structure, run identity, population/seed variation, planned diagnostics and hold-out ordering.

`tools/analytics/strength_calibration_report.py` consumes persisted run datasets and produces descriptive run-to-run summaries. It does not alter the production uncertainty proxy and has no promotion authority.

`data/arena/strength/plans/2026-08-27-replication-v3.json` is a predeclared, not-yet-executed plan. It contains placeholder engine/rules SHAs intentionally; real execution must freeze actual commits before data collection.

## Process correction

During PR development, a synthetic SPRT operating-characteristic harness was briefly opened as the next implementation step. Cross-document review against the current `PROJECT-STUDIES/REDWAR` protocol showed that this sequencing was premature: the active next block is first **real experimental replication and calibration**, while SPRT validation follows that evidence block.

The temporary SPRT harness and its regression tests were therefore withdrawn. No production SPRT, uncertainty proxy or promotion policy was changed. The correction is preserved here so the branch history remains understandable rather than silently erasing the deviation.

## Promotion implications

The current engineering uncertainty proxy remains unchanged until repeated-run evidence establishes whether it tracks observed variation across relevant contexts.

SPRT remains an isolated statistical library and must not become the promotion authority until operating characteristics are validated with null/positive controls, draws, invalid/incomplete games, repeated-condition dependence and stopping behaviour.

## Completion criterion

The calibration block is complete only when a reproducible report contains:

```text
dataset + provenance
→ exclusions / invalids
→ paired effect
→ run-to-run variation
→ context effects
→ draw analysis
→ uncertainty diagnostics
→ hold-out result
→ SPRT validation
→ explicit decision
```

The accepted decisions are:

```text
RETAIN BASELINE
REFINE MODEL
COLLECT MORE DATA
KEEP PROMOTION DISABLED
```

No production Ares change follows from this decision alone. Downstream search/evaluation/NNUE optimisation remains after the minimum Strength evidence gate.
