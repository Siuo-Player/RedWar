# Arena — terminal no-move contract

## Discovery

The AI Quality Gate reproduced a real headless Arena position in which the C++ engine returned `bestmove 0000` while the Python `GameState` still had `game_over == False`.

The observed state had White to move with all available White pieces unable to act. The Python game rules already define this as a blocked terminal position (`Oponente Bloqueado`).

## Evidence

CI run: `33185411196`

The failure occurred in `ai/bot.py` after eight completed games of the A/B Arena. The C++ engine returned `0000` for the recorded RWEN state instead of a legal action.

The same run also demonstrated that:

- challenger and baseline both compiled successfully;
- the generic engine benchmark produced the same stable best move on both builds;
- the FrostMage Nevada tactical regression passed at 100 and 1000 nodes;
- the failure was isolated to the terminal/no-move boundary in the Arena loop.

## Decision

`bestmove 0000` is accepted only when the authoritative Python `GameState` independently confirms `game_over` after evaluating terminal conditions.

Otherwise `0000` remains a hard engine/bridge failure and must not be converted into a draw, random move, or silently accepted result.

## Rationale

This preserves evidence integrity:

```text
C++ says no legal move
        ↓
Python independently validates terminality
        ↓
terminal → normal game completion
non-terminal → hard failure
```

The Arena must not reinterpret a malformed or inconsistent engine response as a valid strength observation.

## Regression coverage

`tests/test_ai_bot.py` covers both directions:

- terminal state + `0000` → terminal result accepted;
- non-terminal state + `0000` → `RuntimeError` remains required.

## Scope

This decision changes no evaluation, search, strength methodology, seed sets, holdout data, or promotion rules.

It is an integration/contract correction at the Python↔C++ boundary.
