# RedWar — Persistent Arena Strength Dataset

## Purpose

The Arena already produces the raw JSONL needed for Strength analysis, but GitHub Actions artifacts are temporary. This document defines the persistent bridge from a real Arena artifact to a reproducible scientific dataset.

The canonical flow is:

```text
real Arena JSONL
    ↓
raw SHA-256 + workflow/artifact provenance
    ↓
current Arena validation
    ↓
explicit Strength population context
    ↓
complete colour-inverted pairs
    ↓
persistent dataset
    ↓
existing empirical paired uncertainty audit
```

The dataset is evidence storage and analysis input. It is not a promotion gate.

## Dataset contract

`data/arena/strength/*.json` uses schema `redwar-strength-dataset-v1` and contains:

- `manifest.evidence_class = real_arena`;
- source workflow run, artifact ID, source commit and raw JSONL SHA-256;
- challenger/baseline/rules versions;
- node budget and opening count;
- selection policy, controller population and skill context;
- explicit game validity and termination provenance;
- colour, opening and seed for every game;
- one `independent_units` entry per complete colour-inverted pair;
- a canonical SHA-256 over the dataset contents before the digest itself.

Here, `independent_units` means the **pair-level unit used by the current paired resampling procedure**. It does not mean that every pair is an independent draw from the full Arena environment distribution.

The stored game records deliberately contain only the scientific fields required for Strength analysis. Search traces and full action sequences remain in the original Arena artifact rather than being duplicated into the long-lived dataset.

## Experimental-condition independence

A complete colour-inverted pair is the correct unit for preserving the dependency created by the two games sharing an opening/experimental condition and reversing challenger colour. That paired structure is different from independence of the underlying conditions.

The first real control experiment contains 50 complete pairs but only a finite opening/seed schedule. The same opening/seed combinations are reused across pairs. Therefore:

```text
50 paired resampling units
≠
50 independent environment-condition draws
```

Repeated conditions may be legitimate deliberate replicates, but they reduce the amount of independent information available for claims about the wider game-state population. Future calibration must therefore retain condition identity and report how conditions are repeated, stratified or varied across experiments.

The current dataset format preserves `opening_index` and `seed` for every game, so this distinction can be audited without changing the production estimator.

## Immutable evidence lineage

A committed dataset is a durable derived evidence record, not a replacement for the raw Arena result. Its provenance must remain content-addressed through both:

```text
raw Arena JSONL SHA-256
        ↓
derived dataset canonical SHA-256
```

The repository must never silently replace an evidence dataset in place while preserving its original identity. A materially new Arena experiment gets a new dated dataset path (or a new explicit dataset version) and its own provenance record.

## Existing real control experiment

`2026-08-27-control-100.json` is derived from GitHub Actions run `33027350530`, artifact `9628952365`, whose raw Arena output has SHA-256:

```text
19738166542806738c72468e2b10ba87f1dd8762603caa28638f4aa5ea0d98bf
```

The experiment contains 100 valid games and 50 complete colour-inverted pairs. The challenger won 50 games and the baseline won 50; there were no draws or invalid games. The challenger was White in 50 games and Black in 50 games.

The challenger revision is `f6a1ee4beb160ee4e23e7e044fba0f78aa5961ac`, a control revision containing no gameplay change relative to the baseline commit `37b94d51b810b7ef698139f896afd30eee50fa5a`. This therefore acts as a real Arena null/control observation rather than a synthetic fixture.

The Arena summary happened to mark the run as `promoted` because that experimental workflow was invoked with a zero win-margin threshold. That flag is not copied into the scientific dataset and must not be interpreted as a production promotion result.

## Empirical uncertainty audit

The persistent dataset is consumed by the existing `empirical_paired_uncertainty_audit`, with the pair—not the individual games—as the resampling unit. The derived audit is stored next to the dataset in `2026-08-27-control-100.audit.json`.

For this control experiment, 20,000 paired bootstrap resamples produced:

- aggregate implied Elo delta: `0.0`;
- empirical 2.5th percentile: approximately `-41.48` Elo;
- empirical 97.5th percentile: approximately `+41.48` Elo;
- empirical half-width: approximately `41.48` Elo;
- current engineering uncertainty proxy half-width: approximately `755.08` Elo.

These numbers are an **empirical descriptive audit**, not a calibrated confidence interval. The single control experiment is not sufficient to replace the proxy, authorize a promotion policy change, or establish general strength across the broader Arena population.

The use of 2.5th and 97.5th percentiles is descriptive nomenclature only; it must not be presented elsewhere as a calibrated 95% confidence interval.

## Matchup / intransitivity interpretation

The contextual matchup analyzer is also descriptive. A detected cycle such as:

```text
A > B
B > C
C > A
```

is a signal that context-dependent performance may be present. It is **not by itself evidence of persistent strategic intransitivity**. Finite-sample variation, repeated conditions, population composition and heterogeneous strengths can all create an observed cycle.

Future interpretation should require repeated evidence across controlled experiments and explicit uncertainty/context accounting before promoting a cycle from diagnostic observation to a scientific claim.

## Reproducibility

Build a persistent dataset from a raw Arena JSONL with:

```bash
python tools/analytics/strength_dataset.py build RESULTS.jsonl \
  --population-id ares-dev-population-v1 \
  --selection-policy paired-fixed-openings \
  --controller-population Ares-v1-vs-baseline-v1 \
  --skill-context fixed-node-budget \
  --workflow-run-id RUN_ID \
  --artifact-id ARTIFACT_ID \
  --head-sha HEAD_SHA \
  --output DATASET.json
```

Audit a stored dataset with:

```bash
python tools/analytics/strength_dataset.py audit DATASET.json --bootstrap-samples 20000 --seed 0
```

The audit remains descriptive until calibration has been repeated across independent real Arena experiments and the sequential test has been empirically validated.

## Relationship to existing contracts

The persistent dataset builds on:

- `tools/analytics/arena_experiment_validation.py` for raw Arena structural validation;
- `tools/analytics/arena_strength_audit.py` for pair construction and empirical audit integration;
- `tools/analytics/strength_population.py` for population/selection context;
- `tools/analytics/strength_empirical_audit.py` for paired resampling;
- `tools/analytics/real_arena_strength_report.py` for broader descriptive reporting.

No production Strength estimator or promotion policy is changed by this dataset layer.