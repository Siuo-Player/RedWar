# GameState terminal-state regression

## Discovery

PR #180 removed the no-legal-action terminal block from `GameState.check_game_over()` while changing the Inquisitor silence semantics.

The missing block caused the Python GameState to report `game_over == False` for positions where the C++ engine correctly returned `bestmove 0000`.

## Evidence

The AI quality gate reproduced the boundary after 8 Arena games. The Python↔C++ bridge reported `bestmove 0000`; the Python state did not recognize the blocked position as terminal.

A deterministic regression board was added to `tests/test_ai_bot.py` and reproduces the same terminal condition independently of Arena randomness.

## Decision

The canonical `GameState.check_game_over()` terminal logic must remain intact, including the no-legal-action / blocked-position rule.

The Inquisitor change is limited to the intended semantic rule: a stunned opposing Inquisitor does not project silence.

## Validation

The deterministic regression must pass together with the existing RWEN, differential, Nevada, and replay tests before PR #180 can merge.

## Scope

No changes to evaluation, search, Strength methodology, seed sets, holdout data, or promotion authority.
