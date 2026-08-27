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

## Required experimental structure

Future calibration must preserve a frozen analysis contract covering engine/rules versions, compute budget, opening/scenario sampling, seed generation, colour pairing, validity/termination rules, outcome definition, primary statistic, diagnostics and hold-out policy.

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

A calibration batch must retain provenance sufficient to identify challenger, baseline and rules versions, run/experiment identifiers, pair, colour, opening/scenario, seed, compute budget, outcome, validity, termination reason and population identifier.

The raw Arena record remains the source of truth; derived datasets are analytical views.

Primary analyses should include paired effect, between-run stability, context effects and legitimate draw behaviour. A paired-bootstrap percentile interval remains descriptive until its inferential calibration is established; it must not automatically be labelled `IC95%`.

At least one later run, stratum or predeclared subset should remain available as hold-out evidence for model refinements.

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

No production Ares change follows from this decision alone. Downstream search/evaluation/NNUE optimisation remains after the minimum Strength evidence gate.