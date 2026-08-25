# Discovery / Decision — action-aware ordering Arena result

**Date:** 2026-08-25  
**Experiment:** `feat/arena-action-aware-ordering-2026-08-25` vs `main` baseline  
**Node budget:** 10,000  
**Games:** 20  
**Result:** Challenger 14 — Baseline 6 — Draws 0  
**Margin:** +8 wins for challenger  

## Fact observed

The action-aware history/killer ordering change won 14 of 20 experimental games against the baseline, with no draws.

The measured challenger score rate is therefore 70%.

## Interpretation

This is **positive experimental evidence**, but not yet sufficient evidence to describe the change as a statistically established general strength improvement.

A 20-game sample is small. A point estimate of 70% has substantial uncertainty, and the result does not by itself establish the effect over many openings, seeds, colors, or future opponents.

The experiment is nevertheless useful because it is an independent A/B test rather than a hand-selected tactical benchmark. The action-aware ordering branch was evaluated against the previous engine baseline under the Arena protocol.

## Decision

1. Keep the action-aware ordering change in `main`; the observed result is sufficiently promising that reverting it solely because of uncertainty would discard useful evidence.
2. Do **not** classify the result as statistically proven promotion evidence yet.
3. Repeat the same comparison with a substantially larger number of games before using it to calibrate or validate the sequential promotion machinery.
4. Preserve the exact challenger/baseline commits, node budget, openings, seeds, color pairing and pentanomial information for the larger experiment.

## Statistical context

For 14 wins and 6 losses, the logistic Elo-equivalent point estimate against a binary baseline is approximately **+147 Elo**. This is descriptive only; it is not a calibrated strength rating and does not account for paired-game dependence or broader uncertainty.

The project should prefer paired/pentanomial aggregation and sequential testing inspired by Fishtest/Stockfish rather than replacing the evidence with a single 20-game win percentage. Fishtest explicitly tracks W/D/L together with pentanomial counts and uses statistical analyses such as SPRT/Elo to determine whether engine changes improve strength. See:

- https://github.com/official-stockfish/fishtest
- https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html

## Next experiment

Run the same challenger against the same baseline with a larger sample, without changing the implementation in between. The purpose is to estimate whether the +8 margin persists outside the initial 20 games.

The result of this experiment must not be used to select or modify tactical benchmark positions retroactively.
