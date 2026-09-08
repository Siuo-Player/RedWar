# RedWar — A0.1 Semantic Closure — 2026-09-07

## Purpose

A0 = PASS established a bounded correctness gate, but the adversarial architecture review identified semantic contracts that were not yet demonstrated as closed. A0.1 is the explicit follow-up gate before Strength calibration.

## Current verified findings

### Inquisitor silence

Three independently relevant layers agree on the intended contract:

- The C3 oracle ignores an enemy Inquisitor when `stun_timer != 0`.
- The Python runtime spell wrapper requires `source.can_act()` for the Inquisitor aura.
- The native C++ move generator ignores stunned enemy silence sources.

PR `#292` adds explicit engine-vs-oracle tests for both active and stunned Inquisitor sources so this contract is no longer only transitively covered.

### Repetition / threefold

Python `GameState` maintains `state_history` and terminates on the third occurrence of the current state hash. The native `BoardState` representation currently contains no equivalent game-history collection, and native search keys are derived from board state/TWC rather than a repetition-history context.

This is therefore an unresolved architecture boundary, not a presumed parity fact. A later change must decide how history enters the native/search contract before claiming full repetition parity.

### Terminal semantics

The deterministic terminal matrix is now closed by PR `#310`. The regression compares the same RWEN fixtures across Python and the native backend for mutual annihilation, one-side annihilation, blocked side, TWC=50 and the TWC=49 non-terminal boundary. Native terminal scores for terminal classes are obtained from the actual `alpha_beta()` implementation rather than a duplicated test-side formula; the external root representation remains `bestmove 0000` for terminal positions.

### Special-spell legality

PR `#303` closed the discovered inherited-spell legality gap in the Python silence guard and established explicit special-spell legality coverage. The canonical action adapter and the C3/native comparisons therefore have a single documented action-space boundary for MOVE/ATTACK/STUN/SPAWN/SPELL.

### Canonical action boundary

PR `#306` made `engine.legal_actions` an explicit engine-facing canonical action boundary, with explicit legacy conversion for compatibility consumers. PR `#308` then made `GameState.execute_action()` normalize accepted inputs through `normalize_action()` before crossing the existing `make_action()` transition seam.

## Open gate checklist

- [ ] repetition / threefold parity or an explicitly documented backend boundary
- [x] terminal-state differential parity
- [x] silence/stun semantic contract explicitly tested against C3 oracle
- [x] all special-spell legality parity under one canonical contract
- [x] engine-facing canonical action adapter consolidated by PR #306
- [ ] authoritative execute path rejects illegal canonical actions by contract (`#309` / follow-up `#311`)
- [ ] differential coverage of every closed transition contract
- [x] confirmed dead rule code removed only after replacement behavior is covered (PR `#300`)

## Constraints

This gate does not run datasets, statistical analyses or strength experiments. It does not authorize search tuning, PST tuning, NNUE tuning or balance claims.
