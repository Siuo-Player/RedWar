# Decision: first-divergence differential diagnostics

## Status
Accepted for differential-testing tooling.

## Decision
When Python/C++ differential execution fails, diagnostics should identify the first divergent transition and preserve the original valid action order. Shrinking should initially operate on valid prefixes rather than deleting arbitrary actions.

## Rationale
Deleting arbitrary actions can invalidate subsequent RPG actions because legality depends on the evolving board state, timers, effects, and side to move. A shortest reproducing prefix is therefore a safe first reduction step.

## Scope
This decision applies to diagnostic tooling only. It does not alter engine semantics, search, move ordering, or promotion criteria.

## Future extension
If needed, add state-aware delta debugging that proposes alternative legal traces while preserving a reproducible divergence.