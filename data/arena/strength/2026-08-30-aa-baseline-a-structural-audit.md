# A/A baseline A — structural audit

Date: 2026-08-30

Run: `aa-baseline-a-v1`
Artifact: GitHub Actions artifact `9739205697`

## Observed result

- 100 valid games
- 50 complete pairs
- 0 invalid games
- Challenger: 41 wins
- Baseline: 59 wins
- Challenger white: 28 wins / 50
- Challenger black: 13 wins / 50

The aggregate 41–59 result is **not** interpreted as a strength estimate because challenger and baseline are identical by protocol.

## Pair structure

The 100 games form 50 colour-reversed pairs. The data confirm the intended pairing structure: the two games in a pair use the same opening and the challenger colour is inverted.

Within pairs, 28 pairs split one game each to challenger and baseline; 12 pairs were won by baseline in both games; 3 pairs were won by challenger in both games; and 7 pairs had the same winning colour across both games while challenger/baseline role reversed.

## Opening structure

The A/A result is strongly structured by opening rather than behaving like independent homogeneous games. In the observed run:

- openings 2, 9, 10 and 13 produced baseline wins in all six games;
- opening 15 produced challenger wins in all six games;
- openings 1 and 11 had all pairs won by the same board colour across the colour reversal, producing no challenger-vs-baseline paired advantage despite a systematic side winner.

These observations show that the opening/scenario component is capable of producing large deterministic-looking effects in a 100-game A/A sample.

## Evidence class

`empirical descriptive evidence`

This audit is diagnostic evidence about the measurement protocol and its nuisance structure. It is **not** evidence that Ares is weaker or stronger.

## What cannot be concluded

- The 41–59 aggregate cannot be treated as Ares strength evidence.
- The white-side imbalance cannot by itself be attributed to the engine or to gameplay.
- The observed opening effects do not establish causal responsibility for colour imbalance.
- The 50 pairs are not 100 independent experimental units.
- Percentile bootstrap output must not be labelled a formal 95% confidence interval without an inferential design that justifies that interpretation.

## Decision

Before changing gameplay, search, evaluation, or NNUE, replicate the experiment with `aa-baseline-b-v1` and analyse A and B separately.

The comparison should preserve the pair as the primary experimental structure and report colour, opening, seed, pair integrity, invalid/unfinished rate, node-budget conformance, and provenance.

A separate lifecycle-dependence diagnostic is also required because the Arena currently reuses persistent C++ engine processes across games, while the C++ transposition table is global. This creates a plausible source of within-pair dependence that must be measured rather than assumed away.
