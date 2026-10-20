# Decision — current material tie-break contract

**Date:** 2026-10-20  
**Governing issue:** #607  
**Related contracts:** `docs/GAME_RULES.md`, `engine/game_state.py::GameState.check_game_over()`, C++ `no_capture_terminal_score()`

## Context

The canonical README and GAME_RULES documents said that only permanent pieces count toward the material tie-break and described the winning colour as an adaptive balancing policy. The current Python terminal resolver instead sums the cost of every on-board piece and awards Black the result when White does not have strictly more material. The C++ search uses the board's total material score, which includes temporary pieces and has the same equal-material preference.

Temporary summons such as Bone, Ghoul and StoneWall have non-zero costs. Their removal does not reset the no-capture counter, but they can affect the material score while present.

## Decision for the current ruleset

Preserve the existing Python/C++ behavior in this corrective slice, because changing terminal outcomes without controlled balance evidence would be a gameplay change:

1. Material is the sum of configured costs of all pieces currently on the board, including temporary summons while they remain.
2. If White's material is strictly greater, White wins.
3. Otherwise Black wins, including exact equality.
4. The no-capture counter is a separate contract: only removal of a permanent piece resets it. A temporary piece's lifespan/removal does not reset the counter.
5. The Black-on-equality rule is a fixed deterministic rule. It is not evidence that Black is statistically disadvantaged and is not an adaptive colour-compensation algorithm.

## Consequences

- Canonical rules documentation must describe the behavior actually implemented in both engine paths.
- Tests protect temporary-piece material and equal-material outcomes.
- A future change to permanent-only material, or to adaptive colour compensation, requires a separate balance/rules decision with controlled evidence; it must not be smuggled into a documentation or correctness patch.
