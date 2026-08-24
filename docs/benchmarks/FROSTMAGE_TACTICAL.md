# FrostMage Tactical Benchmark

## Why this exists

`FrostMage` costs 5 points but can apply an area stun at range 3. Under the RedWar rule that a second stun while the target remains stunned becomes a death, a single FrostMage can create an extreme tactical sequence: stun a cluster now and, on the next available FrostMage turn, convert the same cluster into kills.

This makes FrostMage a deliberate adversarial benchmark for Ares. Ares must not evaluate the unit from material cost alone; it must recognise the tactical value of multi-target stun and the future conversion into deaths.

## Benchmark position

`tools/analytics/frostmage_benchmark.py` uses a fixed RWEN position with five enemy Bones clustered in one FrostMage three-range stun area.

The benchmark expects the engine to select a `STUN` action at several node budgets. It is diagnostic while Ares is still known to be weak; it should become a regression gate only after the engine reliably solves the position.

## Interpretation

A failure is evidence of a search/evaluation problem, not a balance problem. Possible causes include:

- the move generator not exposing the strongest multi-target stun;
- move ordering failing to search the stun early enough;
- the classical evaluation undervaluing simultaneous stun pressure;
- quiescence/search horizon effects hiding the second-stun conversion;
- NNUE features not representing the tactical structure strongly enough.

The next Ares work should isolate these causes with controlled positions rather than immediately changing FrostMage's cost.
