# Decision — AI quality gate change-scope classification

**Date:** 2026-08-28  
**Scope:** `.github/workflows/ai_quality_gate.yml` change detection  
**Status:** proposed via dedicated PR

## Discovery

The public-release/licensing PR changed `ai/LICENSE`. The `ai-quality-gate` classified that file as an Ares engine change because its detection pattern treated every path under `ai/` as AI code.

That classification triggered the 100-game promotion Arena even though the PR changed no Ares implementation, search, evaluation, NNUE or benchmark logic. The run completed 50–50 and therefore failed the promotion margin, but that result is not evidence against the licensing change.

## Decision

The workflow should classify AI changes by actual source/tooling paths rather than the entire `ai/` directory:

```text
ai/*.{py,pyx,pyi,cpp,hpp,h,c,cc,cxx}
tools/nnue/**
```

Documentation, license notices and other non-executable metadata under `ai/` do not trigger the promotion Arena.

Real Ares source changes continue to trigger the existing quality pipeline and promotion Arena. No benchmark threshold, node budget, seed, promotion rule or test assertion is changed by this decision.

## Validation

A regression test extracts the engine-change pattern from the workflow itself and checks representative source paths are detected while `ai/LICENSE`, Ares documentation, repository documentation and UI assets are not.

## Interpretation

The prior failed promotion Arena run is retained as CI evidence of the classifier bug. It must not be interpreted as a strength result for the licensing PR.
