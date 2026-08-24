# Ares Tactical Benchmark Suite

Ares is validated with deterministic RPG positions rather than only aggregate Arena results.

## Method

Each case contains only:

- a canonical 8x8 RWEN position;
- the tactical action class expected from a stable high-budget reference;
- a node-budget scan.

The same position is executed at progressively smaller budgets. The useful metric is the **failure threshold**: the first budget at which Ares stops selecting the reference tactical action.

This deliberately avoids hard-coding a special search path for one position. The engine sees only the RWEN and node budget.

## Current cases

### `frostmage-5-target`

Five enemies are clustered inside one FrostMage stun area. The expected tactical class is the immediate `STUN`. This is the current sanity benchmark for the two-stun lethal rule.

Run it with:

```text
python tools/analytics/tactical_benchmark_suite.py --case frostmage-5-target --nodes 10 --nodes 100 --nodes 1000 --nodes 10000 --trace
```

## Cases to add next

The next positions should be independently constructed and validated at a high node budget before becoming regression references:

1. single-target lethal second stun;
2. multi-stun with fewer targets;
3. stun that misses all enemies, proving the selective extension is not triggered;
4. same first stun target area versus a different stun area;
5. high-value spell versus material gain;
6. passive/aura tactical threat without an immediate material swing;
7. lifespan/cooldown trade-off;
8. defensive position where the strongest move is not the highest material move.

A position is not promoted to a hard regression until its reference move is stable across repeated high-budget runs.
