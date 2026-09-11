# Audit — FrostMage vs Inquisitor endgame

**Date:** 2026-09-11  
**Status:** Audited; exact manual position still required for a full reproduction

## Scope

Issue #444 reports a manual endgame with 16 FrostMages against one Inquisitor in which the player could not find a practical finish. The issue does not include a canonical replay, RWEN state, or exact board coordinates, so a claim that the reported position has been exactly reproduced would be unsupported.

## Findings against current `main`

1. `NEVADA` is a spell and its intended contract is an area spell whose center does not require an enemy. The existing FrostMage contract tests cover empty centers, ice-center exclusion, silence and repeated casts.
2. The runtime FrostMage rule installation also enforces the intended contract: an active opposing Inquisitor inside radius 2 blocks spells, while empty legal centers remain available outside that aura.
3. `GameState.check_game_over()` still evaluates no-legal-action positions after the 50-turn capture counter and repetition rules. The terminal condition is therefore not obviously missing from the current authoritative engine.
4. The new stress fixture uses the reported 16-vs-1 material composition and asserts that the position is not falsely classified as blocked while legal FrostMage actions exist. A second case verifies that Inquisitor silence is local: a FrostMage inside the aura loses NEVADA, while another outside it can still cast and can still move.

## Conclusion

The available evidence does **not** justify changing combat semantics or terminal rules yet.

The current classification is:

- **No confirmed terminal-rule defect.**
- **No exact reproduction of the manual deadlock yet**, because the canonical board state is missing.
- **Potential UX/strategy issue remains open.** The next decisive input is the exact replay/RWEN state (or equivalent move sequence) from the reported position.

Once the exact state is available, the audit should answer deterministically whether there is a forced win, a forced loss/tiebreak, or a genuine no-progress interaction. Any rule change should come only after that result.

## Regression coverage

`tests/test_frostmage_inquisitor_endgame_audit.py` deliberately keeps the fixture state-level and independent from UI behavior. This prevents the issue from being “fixed” by hiding an engine problem behind player feedback.
