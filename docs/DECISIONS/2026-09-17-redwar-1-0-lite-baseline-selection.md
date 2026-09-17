# Decision — 1.0-Lite controlled Ares baseline selection

## Status

**Experiment implemented; selection not yet frozen.**

The repository now contains an explicit controlled experiment for selecting the 1.0-Lite Ares Balance Baseline. The experiment is an instrument-reliability/reproducibility study only.

## Fixed candidates

- StockWar-Iniciante — 100,000 nodes
- StockWar-Intermedio — 500,000 nodes
- StockWar-Avancado — 1,000,000 nodes

The 150,000-node benchmark and mixed training bots are excluded from baseline selection.

## Evidence model

Each candidate plays against itself from the same deterministic opening schedule. The two games in each pair invert candidate colour. Each game uses fresh engine processes, so a previous game's process-local state is not silently carried into the next observation.

Each game records candidate, node budget, seed, opening identity, colour, validity, termination, failure diagnostics and a digest of the complete action trace. Fixed-condition replay checks compare the action digest from repeated executions.

## Selection boundary

The selected baseline must be chosen from operational reliability and reproducibility evidence:

```text
valid completion
+ no unresolved hang/invalid-action pattern
+ deterministic replay evidence
+ complete provenance
```

The following are explicitly excluded from the selection criterion:

```text
hero win rate
competitive strength
Arena rating
Auto-Pricer output
```

Selecting a baseline does not certify the selected Ares as the strongest engine and does not certify the hero roster as balanced.

## Next decision

After the controlled artifact has been executed and reviewed, one exact profile/configuration can be frozen as the 1.0-Lite Balance Baseline. Only then may Balance Lab development samples be collected for hero/economy analysis.
