# Decision — Persist the first real Arena Strength control dataset

**Date:** 2026-08-27  
**Status:** accepted

## Context

The Strength infrastructure can validate Arena JSONL and perform a paired empirical uncertainty audit, but GitHub Actions artifacts are temporary. A scientific result therefore needs a durable, content-addressed representation before it can be reused for later calibration work.

A dedicated 100-game control experiment produced a complete current-schema Arena dataset: 100 valid games, 50 complete colour-inverted pairs, no draws, no invalid games, and balanced challenger colour assignment. The experiment was generated on a control revision against `main`, so it is appropriate as a real null/control observation.

## Decision

Persist a reduced scientific dataset under `data/arena/strength/` rather than committing the full one-megabyte Arena JSONL. Preserve the raw artifact identity through:

- GitHub Actions workflow run ID;
- artifact ID;
- challenger/control head SHA;
- SHA-256 of the original raw JSONL;
- complete experiment metadata;
- all per-game fields required by the Strength validation contract;
- explicit Strength population context;
- explicit complete A/B pair units.

The existing `strength_empirical_audit` consumes those stored pair units directly.

## Why this boundary

Full engine traces and action logs are useful for forensic debugging but are not necessary for the Strength estimator or paired uncertainty calculation. Keeping the scientific dataset small makes it practical to version permanently while retaining a cryptographic reference to the original Arena artifact.

## Statistical boundary

The resulting paired bootstrap is an empirical descriptive audit only. For the first 50-pair control experiment, the aggregate implied Elo delta is `0.0`, while the empirical resampling half-width is approximately `41.48` Elo. The production engineering uncertainty proxy is approximately `±755.08` Elo for the same run.

This observation is useful for calibration work, but one real control experiment is not sufficient to replace the uncertainty proxy, validate the SPRT, or change the promotion gate.

## Consequence

Future real Arena experiments can use the same `redwar-strength-dataset-v1` schema. Calibration should proceed by accumulating independent real experiments and auditing stability across runs, contexts and populations rather than treating a single experiment as definitive.
