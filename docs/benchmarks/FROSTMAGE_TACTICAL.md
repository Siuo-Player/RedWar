# FrostMage Tactical Benchmark

## Why this exists

`FrostMage` costs 5 points but can apply an area stun at range 3. Under the RedWar rule that a second stun while the target remains stunned becomes a death, a single FrostMage can create an extreme tactical sequence: stun a cluster now and, on the next available FrostMage turn, convert the same cluster into kills.

This makes FrostMage a deliberate adversarial benchmark for Ares. Ares must not replace the configured hero costs with hidden material constants; the costs in `heroes_config.json` remain the base values used by evaluation and search heuristics.

## Benchmark position

`tools/analytics/frostmage_benchmark.py` uses a fixed RWEN position with five enemy Bones clustered in one FrostMage three-range stun area.

The benchmark is intentionally outside the engine's decision logic: no engine code knows that this position exists or that FrostMage is the expected answer.

## Current baseline

Measured on the current Ares build:

```text
10,000 nodes   -> MOVE A5 C3   FAIL
100,000 nodes  -> MOVE A5 C3   FAIL
500,000 nodes  -> STUN A5 D5   PASS
```

A denser threshold scan should normally be used around the transition, for example every 25k nodes between the last failing and first passing budget.

## Search trace

The benchmark supports `--trace`. When enabled, each node budget gets a separate file under `logs/benchmarks/frostmage/`.

The trace is deliberately bounded and records:

- root move ordering and ordering scores;
- first few internal move orders;
- move attempts at shallow plies;
- best-move changes;
- transposition-table hits and cutoffs;
- alpha-beta/quiescence cutoffs;
- STUN selective extensions;
- best move at each completed iterative-deepening depth;
- final node count and aggregate counters.

This is a decision/pruning summary, not a complete node dump. The objective is to compare a failing threshold (for example 325k) against a passing one (350k) and identify where the search tree diverges.

## Interpretation

This is evidence of a tactical search weakness, not evidence that FrostMage should receive a lower cost. The unit is already at the minimum configured cost.

The current search treats any `STUN` that hits at least one enemy as a forcing action and gives that branch a selective +1 ply extension. This is intended to expose the immediate `STUN -> opponent reply -> second STUN` conversion without increasing search depth for unrelated moves.

Other candidate causes, if the extension is insufficient, are:

- move ordering that does not distinguish tactical actions deeply enough;
- horizon effects beyond the single extension;
- transposition-table/pruning interactions;
- spells and passives needing better tactical-potential signals;
- NNUE not yet representing the tactical structure strongly enough.

## Optimization methodology

For each search change, rerun the same position at the same node budgets. A successful optimization lowers the failure threshold or keeps it stable without materially increasing evaluation cost.

Recommended workflow:

```text
high-node reference
      ↓
find failure threshold
      ↓
make one isolated search change
      ↓
rerun the same budgets
      ↓
compare threshold + NPS/cost
      ↓
confirm with Arena
```

The benchmark must remain generic: it must exercise real RedWar rules and engine logic, never hardcode the answer for this position.

## Planned tests

1. Validate the current STUN extension with dense threshold scans and traces.
2. Add more adversarial positions for chained stuns and defensive replies.
3. Add spells/passives/aura positions where tactical potential matters without changing base hero costs.
4. Measure move ordering and pruning changes against the same reference suite.
5. Validate the winner in Arena after the micro-benchmarks improve.
