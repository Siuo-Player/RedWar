# FrostMage Tactical Benchmark

## Why this exists

`FrostMage` costs 5 points but can apply an area stun at range 3. Under the RedWar rule that a second stun while the target remains stunned becomes a death, a single FrostMage can create an extreme tactical sequence: stun a cluster now and, on the next available FrostMage turn, convert the same cluster into kills.

This makes FrostMage a deliberate adversarial benchmark for Ares. Ares must not evaluate the unit from material cost alone; it must recognise the tactical value of multi-target stun and the future conversion into deaths.

## Benchmark position

`tools/analytics/frostmage_benchmark.py` uses a fixed 8x8 RWEN position with exactly five enemy Bones on the FrostMage stun cross: C5, D4, D5, D6 and E5. The FrostMage at A5 can stun the center D5, which affects all five occupied squares in the cross. Because all five targets are stunned by the first action, the next FrostMage stun can kill all five under the two-stun rule.

The benchmark is intentionally outside the engine's decision logic: no engine code knows that this position exists or that FrostMage is the expected answer.

## Methodology

First establish a high-node reference, then scan progressively lower node budgets. The useful metric is the lowest budget at which Ares still selects the tactical `STUN`.

For each search optimization, repeat the same node budgets and compare the failure threshold. A successful optimization lowers that threshold without materially worsening evaluation cost or other benchmark results.

Optional search traces record only bounded decision/pruning information: move ordering, root attempts, selective extensions, best moves, cutoffs and summary counters. They are diagnostic artifacts and should not be treated as source-of-truth test fixtures.

## Previous invalid baseline

An earlier version of this benchmark described five clustered Bones but placed one of them at D7, outside the D5 stun cross. That position only had four actual stun targets. Its trace results were therefore discarded and must not be used as evidence for Ares strength.

## Planned tests

1. Treat a stun that hits at least one enemy as a forcing tactical event.
2. Add selective search extension after the stun event.
3. Improve generic tactical scoring of spells and passives without hardcoding benchmark positions.
4. Add more adversarial positions for spells, passives, aura denial, lifespan, cooldown and chained effects.
5. Validate the winner in Arena after the micro-benchmark improves.
