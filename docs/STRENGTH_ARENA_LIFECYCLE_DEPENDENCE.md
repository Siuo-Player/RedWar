# RedWar — Arena lifecycle dependence audit

**Date:** 2026-08-30  
**Evidence class:** instrument diagnostic / methodological evidence

## Observation

The canonical Arena creates persistent `CppEngineBot` instances for the tournament. The bridge keeps the underlying C++ subprocess alive between games. The C++ search implementation has process-global search state, including a transposition table; history and killer structures are reset at search start, while the transposition table is not.

Therefore adjacent colour-reversed games in one pair are not guaranteed to be independent execution contexts.

## Why this matters

The protocol already treats the 100 games as 50 paired units. Pairing controls opening and challenger colour, but it does not by itself remove dependence caused by state retained by the engine process.

The A/A result showing a strong colour imbalance is therefore compatible with several nuisance mechanisms:

- genuine game first-player/colour asymmetry;
- opening or ordering effects;
- persistent engine search state between games;
- another protocol or result-normalisation effect.

The current evidence does **not** identify which mechanism is causal.

## Diagnostic instrument

`tools/analytics/arena_lifecycle_diagnostic.py` compares two execution lifecycles while holding the following fixed:

- engines;
- node budget;
- number and order of games;
- opening seeds;
- adjacent colour reversal;
- Arena match runner and validity rules.

Only the process lifecycle changes:

```text
persistent engine process across games
vs
fresh engine process for every game
```

The output is deliberately labelled observational. A difference between the two modes is evidence of lifecycle sensitivity, not proof that the transposition table is the sole cause.

## Decision

Do **not** change gameplay, search, balance, or the official A/A protocol solely because of this observation.

First use the diagnostic to determine whether the measured A/A imbalance changes materially when engine-process reuse is removed. If it does, the experimental design must explicitly account for lifecycle dependence before strength claims are trusted.

The protected holdout remains untouched.
