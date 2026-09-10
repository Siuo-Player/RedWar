# Ares — Search-State Invariants Audit

**Governing issue:** #413  
**Parent:** #406 → #372  
**Baseline:** `main` @ `3e8bbe9417b584b5a4208d18852070f578bb8b77`

This audit records the state contract that the native Ares search path must preserve across `make_move()` / `unmake_move()`. It is a correctness baseline, not a performance or strength claim.

## Required invariant

For any legal search move `m` from state `S`:

```text
S
→ make_move(m)
→ search-visible state
→ unmake_move(m)
→ S'
```

must yield `S' == S` for every search-relevant field.

The current native reversibility regression compares the complete `BoardState`, including:

- side to move;
- TWC;
- Zobrist hash;
- material score;
- White/Black piece counts;
- every piece's occupancy, team, hero identity, stun timer, lifespan, spawn cooldown, cost and ID;
- every terrain effect's occupancy, team, type and timer.

## Existing executable evidence

`tests/cpp_reversibility_test.cpp` already exercises the production `generate_valid_moves()` → `make_move()` → `unmake_move()` path on representative cases for:

1. basic movement/capture;
2. stunned-piece state;
3. spawn/lifecycle state;
4. temporary lifespan plus terrain effect/timer state.

The test rejects any field-level difference and prints the affected move in the failure message. This means a missing restoration of a search-relevant timer/hash/count is a correctness failure rather than a benchmark regression.

The native NNUE regression independently verifies incremental/full-sync equivalence around real `make_move()` / `unmake_move()` operations.

## Native state model

`BoardState` is the native search position. Repetition history is intentionally kept outside the position object; a state hash identifies the position, while sequence/history logic remains an external concern.

`fast_clone()` is not part of this contract and must not be introduced into the C++ search path or legality preflight.

## Remaining audit boundary

The next correctness work should target any search-specific semantics not already exercised by the existing reversibility matrix, especially action-specific mutations such as complex spells, second-stun effects and spawn side effects. New cases should be added as deterministic regressions when a concrete transition is identified.

No search heuristic should be tuned on top of a failing invariant. Performance and Arena measurements only become meaningful after this correctness layer remains green.
