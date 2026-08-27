# RedWar — Strength dataset population and uncertainty decision

**Date:** 2026-08-27  
**Scope:** real Arena Strength calibration  
**Source reviewed:** PROJECT-STUDIES PR #3 and RedWar PR #134  
**Status:** active methodological guardrail

## Context

The first durable real Arena experiment contains 100 games arranged as 50 complete colour-inverted pairs. The purpose of this tranche is evidence retention and empirical calibration, not automatic promotion.

## Decisions

### Experimental unit

For colour-inverted comparisons, the primary paired unit is one complete pair. Therefore:

```text
100 games = 50 paired game units
```

This must not be described as 50 independent experimental conditions. Opening and seed combinations are partially reused, so some pairs are replications under related controlled conditions.

### Population interpretation

The current sample is evidence conditional on its manifest-defined population: rules, node budget, opening distribution, seeds, colour policy and versions. Increasing N under exactly the same constrained population is not equivalent to expanding population coverage.

Future experiments should deliberately combine controlled replication with explicit variation/stratification of openings, seeds and other relevant context.

### Uncertainty semantics

A paired bootstrap percentile interval is an empirical descriptive interval until the project establishes and validates the inferential assumptions needed for a calibrated confidence interval. Quantiles such as 2.5% and 97.5% must not automatically be labelled an `IC95%`.

### Draw evidence

The first real dataset contains no draws. Consequently, it does not validate draw-related behaviour of the strength model or future sequential testing. Draw handling remains an open validation requirement.

### Intransitivity

An observed cycle between strategies/matchups is diagnostic evidence only. Repeated cycles, context sensitivity, uncertainty and population stability must be established before interpreting a cycle as stable strategic intransitivity.

### Promotion gate

The real dataset does not change the promotion authority. SPRT/promotion remains disabled until the statistical model is calibrated against realistic Arena data, including draw behaviour, dependence structure, invalid-game policy and experimental-population assumptions.

## Consequence for implementation

No production AI change is implied by this decision. The current Strength/Evaluation implementation should preserve the richer provenance and paired-unit representation. Any future inference change must update the methodology, tests and promotion policy together.
