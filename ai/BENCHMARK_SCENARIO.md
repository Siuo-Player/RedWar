# Ares deterministic benchmark

This scenario is the fixed regression position used for search-performance work.

- Position: fixed RWEN below.
- Side to move: White.
- Node budget: 150,000.
- Samples: 5 after 1 warmup.
- Comparison metric: median wall-clock time and median NPS.
- Correctness guard: `bestmove` must remain stable.

```text
B:Sentry_0_N_0,.,.,.,B:Ranger_0_N_0,.,.,./.,B:Phantom_0_N_0,.,.,.,.,B:FrostMage_0_N_0,./.,.,.,B:Templar_0_N_0,.,.,.,./.,.,.,.,.,.,.,./.,.,.,.,.,.,.,./.,W:Templar_0_N_0,.,.,.,W:Phantom_0_N_0,./.,W:FrostMage_0_N_0,.,.,.,.,W:Ranger_0_N_0,./W:Sentry_0_N_0,.,.,.,W:Inquisitor_0_N_0,.,.,.,. W 0
```

The benchmark is intentionally a single short search rather than a tournament, so small but real regressions can be compared before spending time on 100/200-game workflows.
