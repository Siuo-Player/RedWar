# RedWar 1.0 Foundation Authority Matrix

Snapshot: **2026-09-10**  
Verified `main`: **`612221b88381cf740bab6d2ab9e31acfb98c6324`**  
Parent gate: **#370 Foundation**  
Audit issue: **#379**

## Purpose

This matrix records one declared authority, the important consumers, and the current evidence for critical engine/domain contracts. It is an audit artifact, not a second roadmap and not a strength/balance claim.

The machine-readable source is `data/analysis/foundation_authority_matrix_2026-09-10.json`.

## Matrix

| Contract | Authority | Status | Evidence / disposition |
|---|---|---|---|
| Action normalization | `engine.actions.normalize_action` | `CANONICAL_AND_TESTED` | A0.1 semantic-closure docs and legacy fixture matrix |
| Legal action enumeration | `engine.legal_actions.legal_actions` | `CANONICAL_AND_TESTED` | action-space parity and full action-analysis tests |
| Canonical action resolution | `engine.legal_actions.resolve_legal_action` | `CANONICAL_AND_TESTED` | A0.1 semantic-closure docs and legacy fixture matrix |
| Transition mutation/state progression | `GameState.make_action` | `CANONICAL_AND_TESTED` | core-contract docs and state-hash regression coverage |
| Hero design data | `heroes_config.json` / `HERO_DEFS` | `CANONICAL_AND_TESTED` | hero schema and canonical spell metadata tests |
| Spell capability identity | `_declared_spell_names()` → `HERO_DEFS[hero].spells` | `CANONICAL_AND_TESTED` | #380 implementation + regression coverage |
| Unique spell transition semantics | specialized `make_action` branches | `JUSTIFIED_SPECIALIZATION` | schema boundary intentionally keeps unique mechanics in code |
| State hash/repetition identity | GameState Zobrist helpers + `get_state_hash()` | `CANONICAL_AND_TESTED` | post-state-hash and cross-backend coverage |
| Native NNUE incremental mutation | native `Board::make_move/unmake_move` | `CANONICAL_AND_TESTED` | PR #356 and current NNUE documentation |
| NNUE full reconstruction oracle | native `sync_board()` | `CANONICAL_AND_TESTED` | explicit oracle/recovery boundary in #356 evidence |
| Python `fast_clone()` | `GameState.fast_clone` | `JUSTIFIED_SPECIALIZATION` | reference/fixture/replay tooling only; prohibited in native hot path |
| Terminal conditions | `GameState.check_game_over()` | `CANONICAL_AND_TESTED` | Arena no-move decision, terminal differential/AI tests, and foundation regression coverage |
| Effects/timers | `set_tile_effect`, `update_timers`, specialized effect branches | `CANONICAL_AND_TESTED` | incremental/hash regression scenarios |
| Current-state/NNUE documentation | `docs/CURRENT_STATE.md`, `docs/NNUE.md` | `CANONICAL_AND_TESTED` | PR #381 merged as `612221b...` |

## Corrective findings

The audit found two concrete issues rather than a broad rewrite requirement.

1. **Spell vocabulary duplication** is being corrected by #380: the transition validator now checks whether the acting hero declares the spell in canonical configuration. Python still owns the unique transition semantics that the current schema does not express as a generic DSL.
2. **Documentation drift** was corrected by #381: current-state and NNUE baseline/status now match verified `main` and merged native NNUE evidence.

## Remaining foundation debt

The authority matrix itself is now complete for the audited critical contracts. Any remaining #370 work should be driven by concrete uncovered transition/invariant evidence rather than another documentation inventory. The current active implementation blocker is #380 until its required CI gates pass.

This matrix intentionally does **not** infer gameplay balance, engine strength, or search superiority.
