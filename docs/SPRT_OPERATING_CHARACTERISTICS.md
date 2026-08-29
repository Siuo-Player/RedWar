# SPRT Operating Characteristics

`tools/analytics/sprt_operating_characteristics.py` provides a deterministic Monte Carlo diagnostic for the existing RedWar SPRT implementation.

It generates synthetic win/loss/draw sequences from a known Elo delta and draw rate, evaluates them with the production `SPRTConfig`/`evaluate_sequence` functions, and summarizes:

- H1 acceptance rate;
- H1 rejection rate;
- inconclusive rate at the simulation cap;
- mean games to decision;
- 95th-percentile games to decision.

## Required calibration regimes

Use at least:

```text
true Δ = 0
true Δ = configured positive alternative
true Δ = small positive effect
```

and vary the draw rate enough to expose assumptions about draws.

The `true Δ = 0` regime estimates empirical false-positive behaviour. The configured alternative estimates detection/power. A smaller effect is a low-power diagnostic, not an implementation failure by itself.

## Interpretation boundary

This is **synthetic operating-characteristic evidence**, not an Arena result. It validates statistical behaviour under the SPRT model's own assumptions. It does not establish that Arena game outcomes satisfy independence, draw-rate, pairing or other model assumptions.

The simulation is deterministic when `seed`, `trials`, `true_elo_delta`, `draw_rate` and `max_games` are fixed. No promotion authority is granted by this tool.
