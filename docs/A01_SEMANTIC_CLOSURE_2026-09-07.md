# RedWar — A0.1 Semantic Closure — 2026-09-07

## Purpose

A0 = PASS established a bounded correctness gate, but the adversarial architecture review identified semantic contracts that were not yet demonstrated as closed. A0.1 is the explicit follow-up gate before Strength calibration.

## Current verified findings

### Inquisitor silence

Three independently relevant layers agree on the intended contract:

- The C3 oracle ignores an enemy Inquisitor when `stun_timer != 0`.
- The Python runtime spell wrapper requires `source.can_act()` for the Inquisitor aura.
- The native C++ move generator ignores stunned enemy silence sources.

PR `#291` adds explicit engine-vs-oracle tests for both active and stunned Inquisitor sources so this contract is no longer only transitively covered.

### Repetition / threefold

Python `GameState` maintains `state_history` and terminates on the third occurrence of the current state hash. The native `BoardState` representation currently contains no equivalent game-history collection, and native search keys are derived from board state/TWC rather than a repetition-history context.

This is therefore an unresolved architecture boundary, not a presumed parity fact. A later change must decide how history enters the native/search contract before claiming full repetition parity.

### Terminal semantics

Python terminal resolution includes material/no-capture and no-legal-action handling. Native search has corresponding material/no-capture/no-move scoring paths, but the equivalence still needs dedicated differential tests covering the exact terminal classes and winner/value semantics.

## Open gate checklist

- [ ] repetition / threefold parity or an explicitly documented backend boundary
- [ ] terminal-state differential parity
- [x] silence/stun semantic contract explicitly tested against C3 oracle
- [ ] all special-spell legality parity under one canonical contract
- [x] engine-facing canonical action adapter introduced by PR #291
- [ ] authoritative execute path rejects illegal canonical actions by contract
- [ ] differential coverage of every closed transition contract
- [ ] confirmed dead rule code removed only after replacement behavior is covered

## Constraints

This gate does not run datasets, statistical analyses or strength experiments. It does not authorize search tuning, PST tuning, NNUE tuning or balance claims.
