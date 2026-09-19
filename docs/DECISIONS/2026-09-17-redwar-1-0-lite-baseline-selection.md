# Decision — 1.0-Lite controlled Ares baseline selection

## Status

**Selected and frozen: StockWar-Iniciante (100,000 nodes).**

The controlled experiment is complete and the 1.0-Lite operational Ares baseline is now frozen. This does not make a competitive-strength claim.

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

## Final decision record

GitHub Actions run `35415022596` executed the experiment from `main` at source SHA `bf9955c26db58cf08c39f939f96317ed4a7be7c1` with engine SHA-256 `8f5799e646af7f0917e6e29afc9a24d764f7498609668215ba8c0c46ef482bcc` and compiler `g++ (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0`.

All three fixed candidates completed the same 8-pair / 16-main-game schedule:

- **100,000 nodes:** 16/16 valid; all `game_over`; 282.75 s total.
- **500,000 nodes:** 16/16 valid; all `game_over`; 1,197.43 s total.
- **1,000,000 nodes:** 16/16 valid; all `game_over`; 1,983.84 s total.

There were no invalid actions, recorded failures, timeouts, or unresolved hangs. One deterministic replay check per candidate reproduced the action digest exactly.

The selected baseline is **StockWar-Iniciante — 100,000 nodes**. The reason is operational: it is the lowest-cost candidate that satisfied the full reliability/reproducibility boundary under the controlled schedule. The 500k and 1M profiles also passed that boundary, but were not selected because they consumed substantially more execution time for the same baseline role.

The selection deliberately does **not** use hero win rate, Arena rating, competitive strength, or balance conclusions. The selected profile is the frozen execution context for subsequent 1.0-Lite Balance Lab evidence.

Evidence artifact: `redwar-lite-ares-baseline-selection-35415022596` (artifact `10576413639`).

Only after this freeze may Balance Lab development samples be collected under this exact Ares policy/context.

## Post-freeze boundary

The baseline is now frozen. Subsequent 1.0-Lite Balance Lab evidence must use this exact Ares policy/context unless a new baseline-selection decision is explicitly recorded.
