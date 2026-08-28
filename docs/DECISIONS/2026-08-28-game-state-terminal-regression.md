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

The full Test Suite passed 255 tests, including the new terminal regression and Nevada contract tests. CodeQL also passed.

The AI Quality Gate executed its mandatory benchmark and 100-game A/B Arena. It produced 45 challenger wins, 55 baseline wins, 0 draws and 0 invalid games. This is a Strength/promotion result, not a correctness failure; the measured uncertainty proxy was ±755.1. The PR is a semantic rule-correction rather than a claim of improved Ares strength, so this result is not evidence that the Nevada contract is incorrect.

## Scope

No changes to evaluation, search, Strength methodology, seed sets, holdout data, or promotion authority.
