# Decision — pre-match setup and effect timing contract

**Date:** 2026-09-10  
**Status:** Accepted for current 1.0 ruleset

## Pre-match draft and placement

The pre-match phase is a setup phase, not combat execution.

- Each team has the configured draft budget (`ORCAMENTO_BRANCAS` / `ORCAMENTO_PRETAS`; currently 200).
- A draft-selected piece must be marked `draftable` by the canonical hero configuration.
- Duplicate instances of a draftable hero are allowed when each instance is within the shared team budget.
- White pre-match pieces occupy the two home rows at the bottom of the board; black pieces occupy the two home rows at the top.
- The engine-level setup validator is the authority for these constraints. UI and training helpers may construct the board, but they must not redefine the rules.
- Runtime-created non-draftable units (for example temporary spawn units) are not retroactively subject to the draft validator after the match has started.

The budget is a maximum, not an implicit requirement to spend exactly all points.

## Fire/ice effect timing

Effect timers use the same side-owned turn convention as piece timers.

- Creating an effect does not immediately decrement its timer.
- After an action, the side to move becomes active and only timers owned by that active side are advanced.
- Therefore a white-owned fire/ice effect with timer 3 remains at 3 while black is active, then becomes 2 when white becomes active, and so on until expiry.
- Fire applies its destination interaction after the action transition; an eligible piece on fire is stunned unless the transition is the STUN action itself or the spell creating the fire (`ignite`).
- Ice blocks movement onto and through the affected tile and also excludes the tile as a Nevada center.
- Python and native C++ must preserve the same timer ownership and expiry order.

This document records the current 1.0 semantics; it does not introduce a new balance duration.
