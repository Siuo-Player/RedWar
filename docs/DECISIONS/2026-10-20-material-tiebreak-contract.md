# Decision — current material tie-break contract

**Date:** 2026-10-20  
**Governing issue:** #607  
**Related contracts:** `docs/GAME_RULES.md`, `engine/game_state.py::GameState.check_game_over()`, C++ `no_capture_terminal_score()`

## Context

The canonical README and GAME_RULES documents said that only permanent pieces count toward the material tie-break and described the winning colour as an adaptive balancing policy. The current Python terminal resolver summed the cost of every on-board piece. The C++ search used `board.material_score`, which is an evaluation score containing positional bonuses, temporary lifespan scaling and stun adjustments. These paths could disagree on the winner for the same position: Python awarded Black on equal raw costs, while C++ could award White when positional/effect terms made the evaluation score positive despite equal raw material.

Temporary summons such as Bone, Ghoul and StoneWall have non-zero costs. Their removal does not reset the no-capture counter, but they can affect the material score while present.

## Decision for the current ruleset

Align the implementations to the documented permanent-only material rule. This is a correctness fix for a cross-backend contract mismatch, not a strength optimization:

1. Material is the sum of configured costs of permanent pieces currently on the board.
2. Temporary summons do not contribute to terminal material.
3. Positional bonuses, stun adjustments and lifespan-scaled evaluation values do not contribute to terminal material.
4. If White's permanent material is strictly greater, White wins.
5. Otherwise Black wins, including exact equality.
6. The no-capture counter is a separate contract: only removal of a permanent piece resets it. A temporary piece's lifespan/removal does not reset the counter.
7. The Black-on-equality rule is a fixed deterministic rule. It is not evidence that Black is statistically disadvantaged and is not an adaptive colour-compensation algorithm.

## Consequences

- Canonical rules documentation must describe the behavior actually implemented in both engine paths.
- Tests protect temporary-piece exclusion and equal-material outcomes in Python and C++; the C++ smoke suite calls the same terminal-material helper used by search, and its equality case includes a stunned hero to prove that evaluation discounts do not alter terminal material.
- A future change to material policy or adaptive colour compensation requires a separate balance/rules decision with controlled evidence.
- A promotion decision is valid only when the authoritative Arena completes and emits `accept` or `reject`; shell/import failures are execution failures, not promotion evidence.
