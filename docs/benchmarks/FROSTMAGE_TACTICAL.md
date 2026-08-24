# FrostMage Tactical Benchmark

## Why this exists

`FrostMage` costs 5 points but can apply an area stun at range 3. Under the RedWar rule that a second stun while the target remains stunned becomes a death, a single FrostMage can create an extreme tactical sequence: stun a cluster now and, on the next available FrostMage turn, convert the same cluster into kills.

This makes FrostMage a deliberate adversarial benchmark for Ares. Ares must not evaluate the unit from material cost alone; it must recognise the tactical value of multi-target stun and the future conversion into deaths.

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

The first baseline therefore has a failure threshold between 100k and 500k nodes for this position.

## Interpretation

This is evidence of a tactical search weakness, not evidence that FrostMage should receive a lower cost. The unit is already at the minimum configured cost.

The current search already orders `STUN` moves above ordinary moves, but its quiescence `is_forcing_move()` logic only treats a stun as forcing when it sees an already-stunned target. A first multi-target stun against fresh targets can therefore fall outside the tactical continuation that quiescence searches.

Other candidate causes are:

- insufficient value given to simultaneous stun pressure;
- horizon effects hiding the second-stun conversion;
- move ordering that does not distinguish high-impact tactical actions deeply enough;
- lack of selective extensions after a strong tactical event;
- spells and passives being considered in static material rather than as future tactical potential;
- NNUE not yet representing the tactical structure strongly enough.

## Optimization methodology

For each search change, rerun this exact position at the same budgets. A successful optimization lowers the failure threshold or keeps it stable without materially increasing evaluation cost.

The broader benchmark suite follows the same principle: high-node reference first, progressively lower node budgets afterward, then compare the threshold before/after each isolated search change.

## Planned tests

1. Treat multi-target stun as a forcing tactical event in quiescence when appropriate.
2. Add selective search extension after high-impact multi-target stun.
3. Improve generic tactical scoring of spells and passives without hardcoding benchmark positions.
4. Add more adversarial positions for spells, passives, aura denial, lifespan, cooldown and chained effects.
5. Validate the winner in Arena after the micro-benchmark improves.
