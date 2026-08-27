# RedWar — Plan-backed Strength calibration runner

**Date:** 2026-08-27  
**Status:** accepted methodological correction  
**Scope:** Strength calibration execution only

## Discovery

The `replication-v3` protocol is validated as a design, but the existing Arena CLI accepts its frozen controls only as independent command-line arguments. It did not provide a single execution path that validated the declared `run_id` before launching the games and then built the scientific dataset with the declared `experiment_id` and `run_id`.

The Arena also still exposes a legacy promotion calculation. A calibration run using `--margem-vitorias 0` could therefore produce a summary with `promoted=true` even though the workflow has no promotion authority. That is ambiguous evidence and must be prevented at the calibration execution layer.

## Decision

Add `tools/analytics/strength_calibration_runner.py` as a thin orchestration layer.

The runner:

1. validates the complete calibration plan;
2. selects one explicit `run_id`;
3. requires the execution context (`games`, selection policy, controller population and skill context) explicitly;
4. requires the run's frozen node budget and seed set;
5. requires identical challenger/baseline revisions for calibration runs;
6. invokes the existing Arena without changing game semantics;
7. uses `games + 1` as an impossible legacy promotion threshold;
8. rejects any resulting summary that reports `promoted=true`;
9. invokes the existing scientific dataset builder with the declared `experiment_id` and `run_id`.

## Boundary

This does not recalibrate Strength, enable promotion, modify the search/evaluation implementation, or alter Arena rules. It only binds execution to the predeclared experimental design and makes the provenance chain explicit.

## Consequence

Run A and Run B now have a deterministic, plan-backed execution path that preserves raw Arena output and produces a derived dataset carrying the experiment/run identity. No result is considered evidence until the actual games execute successfully and the resulting artifacts pass validation.
