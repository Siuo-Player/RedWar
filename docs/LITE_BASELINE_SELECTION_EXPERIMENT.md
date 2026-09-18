# 1.0-Lite Ares Baseline Selection Experiment

## Purpose

Select one reproducible Ares execution profile for the 1.0-Lite Balance Baseline.

This experiment measures **instrument reliability and reproducibility**, not competitive strength, hero power, or global roster balance.

## Candidates

The experiment evaluates only the player-facing C++ Ares profiles currently exposed by `ai/bot.py`:

| Profile | Node budget |
|---|---:|
| StockWar-Iniciante | 100,000 |
| StockWar-Intermedio | 500,000 |
| StockWar-Avancado | 1,000,000 |

The 150,000-node benchmark and the mixed training bots are excluded because they serve different purposes.

## Experimental design

For each candidate:

1. use the same deterministic opening seeds;
2. use the same current rules/build;
3. run candidate-versus-itself;
4. invert candidate colour between the two games of each pair;
5. create fresh engine processes for every game;
6. record termination, invalid-action and execution-time diagnostics;
7. repeat one or more fixed conditions to verify identical action traces.

The experiment therefore does not compare candidate win rates against each other. Any winner information is a game-execution diagnostic only.

## Provenance

Every output records:

- source commit SHA;
- rules-document blob identity;
- candidate name and node budget;
- opening seed and index;
- colour/pair identity;
- process policy;
- termination reason;
- validity/failure information;
- action-trace digest for reproducibility checks.

## Selection rule

A candidate can become the Lite Balance Baseline only after the evidence shows that it is a sufficiently stable execution instrument for controlled Balance Lab experiments.

The decision must not use:

- aggregate hero win rate;
- `auto_pricer.py` output;
- competitive Arena rating;
- claims that one candidate is globally stronger.

The selected profile is a reproducibility choice for the Lite Balance Lab. Competitive Ares #372 remains independent.

## Execution

The canonical implementation is:

```text
tools/analytics/lite_baseline_selection.py
```

The manual GitHub Actions entry point is:

```text
.github/workflows/lite_baseline_selection.yml
```

The workflow uploads the raw JSON evidence. A human/design decision must inspect that artifact and record the selected baseline before hero/economy tuning begins.
