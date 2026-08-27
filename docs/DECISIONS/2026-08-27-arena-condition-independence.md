# Decision — distinguish paired resampling units from experimental-condition independence

**Date:** 2026-08-27  
**Status:** accepted

## Context

The first persistent real Arena Strength dataset contains 100 valid games grouped into 50 complete colour-inverted A/B pairs. The pair structure is appropriate for preserving within-condition dependence during paired resampling.

The adversarial review identified a separate issue: the experiment reuses a finite opening/seed schedule across pairs. Therefore the number of pair-level resampling units must not be presented as the number of independent draws from the wider Arena environment distribution.

## Decision

Use the following terminology:

- **paired resampling unit** — one complete colour-inverted A/B pair used as the resampling unit by the current paired empirical audit;
- **experimental condition** — the controlled combination of relevant opening, seed, rules, budget and population context;
- **independent experiment** — a separately executed real Arena experiment with its own provenance and controlled population/design.

For the current control:

```text
50 paired resampling units
≠
50 independent experimental conditions
```

The existing pair-level audit remains valid for its stated paired-resampling purpose. General calibration claims require multiple real experiments and explicit accounting for repeated or shared conditions.

## Consequences

Future dataset manifests and reports must preserve condition identity and should describe repeated conditions explicitly. Increasing the raw game count under the same finite schedule is not, by itself, equivalent to increasing independent experimental coverage.

The production Elo-compatible estimator, engineering uncertainty proxy and promotion policy remain unchanged by this decision.

## Statistical boundary

Bootstrap percentiles remain **descriptive empirical percentiles**. They are not calibrated confidence intervals merely because the reported quantiles are 2.5th and 97.5th percentiles.

Similarly, a detected A>B>C>A matchup cycle is a descriptive diagnostic and not evidence of persistent strategic intransitivity without repeated controlled evidence.
