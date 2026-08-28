# Decision — Strength calibration execution provenance sidecar

**Date:** 2026-08-28  
**Scope:** Strength calibration execution provenance  
**Status:** accepted methodological correction

## Discovery

The calibration runner already preserved the raw Arena JSONL and built a derived scientific dataset with `experiment_id` and `run_id`. However, the execution did not emit one compact artifact tying together the exact plan, harness revision, engine/rules revisions, execution parameters and cryptographic hashes of the resulting artifacts.

The raw JSONL remains the source of truth and must not be rewritten after collection merely to inject metadata that was absent during execution.

## Decision

The calibration runner now emits a sidecar `*.run-provenance.json` after a successful Arena run and dataset build.

The sidecar records:

- experiment/run identity;
- plan SHA-256;
- execution harness Git commit and relevant script blob SHAs;
- challenger, baseline and rules revisions;
- games, node budget, opening seeds and seed policy;
- selection policy, controller population and skill context;
- explicit `promotion_authority=false`;
- SHA-256 hashes of raw JSONL, Arena summary and derived dataset;
- dataset canonical SHA-256.

## Boundary

This is provenance only. It does not alter Arena semantics, the production uncertainty proxy, statistical inference or promotion policy.

A later experiment may use the sidecar to prove exactly which execution path produced an artifact. No statistical conclusion follows from provenance alone.
