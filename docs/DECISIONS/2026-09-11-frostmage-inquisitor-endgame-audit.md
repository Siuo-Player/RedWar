# Audit — FrostMage vs Inquisitor endgame

**Date:** 2026-09-11  
**Status:** Audited; exact manual position still required for a full reproduction

## Scope

Issue #444 reports a manual endgame with 16 FrostMages against one Inquisitor in which the player could not find a practical finish. The issue does not include a canonical replay, RWEN state, or exact board coordinates, so a claim that the reported position has been exactly reproduced would be unsupported.

The important strategic interpretation is also narrower than “can the FrostMages kill the Inquisitor?”: the Inquisitor can silence FrostMage spells, so direct elimination may be impossible in a given state. RedWar is nevertheless not intended to end in a draw. A position that cannot be won by elimination may still be won through an allowed terminal tie-break, provided the active balance policy awards that terminal to the FrostMage side.

## Findings against current `main`

1. `NEVADA` is a spell and its intended contract is an area spell whose center does not require an enemy. The existing FrostMage contract tests cover empty centers, ice-center exclusion, silence and repeated casts.
2. The runtime FrostMage rule installation also enforces the intended contract: an active opposing Inquisitor inside radius 2 blocks spells, while empty legal centers remain available outside that aura.
3. `GameState.check_game_over()` still evaluates no-legal-action positions after the 50-turn capture counter and repetition rules. The terminal condition is therefore not obviously missing from the current authoritative engine.
4. The new stress fixture uses the reported 16-vs-1 material composition and asserts that the position is not falsely classified as blocked while legal FrostMage actions exist. A second case verifies that Inquisitor silence is local: a FrostMage inside the aura loses NEVADA, while another outside it can still cast and can still move.
5. The rules do not treat the 50-turn/repetition mechanisms as a final draw. They exist to prevent infinite games and must resolve the game in favor of one side through the active balance/tie-break policy. Therefore “the FrostMages cannot eliminate the Inquisitor” is not by itself evidence of a FrostMage loss.

## Terminal interpretation

For Ares and for endgame testing, terminal results must be normalized as:

```text
WIN / LOSS
```

with the winning mechanism retained as metadata, for example:

```text
ELIMINATION
BLOCKADE
SURRENDER
TWC_TIEBREAK
REPETITION_TIEBREAK
```

A tie-break terminal is therefore a real win/loss result, not a third game-theoretic outcome called “draw”.

The side that receives a tie-break is a balance/rules policy question. It must not be inferred from hero identity, color, or the existence of the Inquisitor alone. The active policy can also be part of broader color balancing, including compensation elsewhere in the draft.

## Conclusion

The available evidence does **not** justify changing combat semantics or terminal rules yet.

The current classification is:

- **No confirmed terminal-rule defect.**
- **No exact reproduction of the manual position yet**, because the canonical board state is missing.
- **No basis for declaring the 16×FrostMage side unable to win merely because the Inquisitor suppresses NEVADA.** A tie-break victory remains a legitimate terminal path if the active balance policy awards it to that side.
- **Potential UX/strategy issue remains open.** The next decisive input is the exact replay/RWEN state (or equivalent move sequence) from the reported position.

Once the exact state is available, the audit should answer deterministically whether there is a forced elimination win, a forced blockade, a forced tie-break win/loss, or a genuinely unresolved state under the active rules. Any rule change should come only after that result.

## Regression coverage

`tests/test_frostmage_inquisitor_endgame_audit.py` deliberately keeps the fixture state-level and independent from UI behavior. This prevents the issue from being “fixed” by hiding an engine problem behind player feedback.

## Ares implication

This case is also a concrete reminder for victory-directed search: Ares must enumerate **all winning terminal classes** before concluding that a position is lost. A strategic route to a favorable tie-break must not be pruned merely because it does not contain an elimination of the last opposing piece.
