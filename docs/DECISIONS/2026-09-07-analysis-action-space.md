# Python analysis action-space correction — 2026-09-07

## Finding

The previous `ai/search.py` analysis generator considered only MOVE and ATTACK actions. The engine already exposes canonical action types for MOVE, ATTACK, STUN, SPAWN and SPELL.

## Decision

Add `engine/legal_actions.py` as the engine-facing adapter that maps the existing piece-level legal generators to canonical `GameAction` values. The adapter does not duplicate hero rules and returns a deterministic ordering.

Update Python position analysis to consume this complete action space and remove random tie-breaking noise.

## Boundary

This change is analysis correctness and API consolidation only. It does not claim stronger play, does not run experiments, and does not alter game rules or C++ search.

## Follow-up

A future core refactor may expose `legal_actions()` and `is_legal()` directly on `GameState`. This tranche deliberately avoids reshaping `GameState.make_action()` until that refactor has dedicated transition-contract coverage.
