# FrostMage vs Inquisitor: Rule Audit and Evidence Limits

**Issue:** #444  
**Initial audit:** 2026-11-20  
**Follow-up:** PR #675 review  
**Status:** Local rule interactions covered; original strategic position not yet reproduced.

## 1. Scope

The tests in this file construct synthetic board states. They are useful for checking individual rule interactions, but they are not a replay of the manual 16-FrostMage-versus-1-Inquisitor game described in Issue #444.

The original issue did not provide a complete initial RWEN position and action sequence. Therefore, the tests cannot establish a forced result for every possible 16-vs-1 position.

## 2. Blocked-player terminal rule and backend parity

When a side has no legal actions, Python's `check_game_over()` declares the game terminal. The C++ search engine independently treats an empty legal-move list as a loss for the side to move:

- White to move and blocked: C++ terminal score is negative; Black wins.
- Black to move and blocked: C++ terminal score is positive; White wins.

The Python winner mapping must therefore name the **opposing** side:
```python
adversario_vencedor = "Pretas" if self.white_to_move else "Brancas"
```

The previous Python mapping named the blocked side and disagreed with C++. The parity regression now checks both colours against the native terminal evaluator. The unusual game rule is not being changed; Python is being aligned with the existing native interpretation.

## 3. FrostMage stun against a lone Inquisitor

In the synthetic fixture, a FrostMage can legally cast `NEVADA` so its cross-shaped effect reaches the lone Inquisitor. Black then has no legal action. Under the native terminal rule, the blocked side loses, so White wins this constructed position.

This finding corrects the previous PR #675 conclusion, which incorrectly treated the Python winner string as authoritative without checking the native evaluator.

It remains a fixture-level result. It does not prove that the original manual position had the same geometry, available actions, or tactical sequence.

## 4. Ice and indirect splash

The interaction tests now execute actions through the canonical sequence `legal_actions()` → `GameState.execute_action()`. They no longer use `make_action()` to force transitions that are not present in the legal action space.

The tests cover these narrower claims:

- Directly focusing `NEVADA` on the Inquisitor's square creates ice there.
- An ice-covered square is excluded from direct spell focus and from the cross-shaped splash.
- Focusing `NEVADA` on an adjacent square can stun the Inquisitor without icing its square.
- If a Black auxiliary piece can legally move, a second FrostMage can legally focus the still-stunned Inquisitor and capture it.

These tests demonstrate the local action sequence only. They do not prove a universal winning strategy for either side.

## 5. Material tiebreak

The material fixture places the no-capture counter at its terminal threshold and checks the resolver's comparison: 128 points for the Inquisitor against 80 points for sixteen FrostMages.

This verifies the tiebreak calculation **at the threshold**. It does not prove that avoiding `NEVADA` necessarily forces the game to reach that threshold, nor that the Inquisitor can systematically eliminate all FrostMages.

The counter increments per action/ply, not per complete two-player turn. Describing 50 increments as 50 full turns was inaccurate.

## 6. What remains to close Issue #444

To answer the original strategic question rather than only test isolated mechanics, the issue needs the original replay or the initial RWEN plus the full action sequence. Then the audit can:

1. Reproduce the exact position on the corrected engine.
2. Verify the legal actions, aura distances, spell ranges, and ice effects at each ply.
3. Compare both players' continuations using the same terminal contract as the native engine.
4. Only then classify the original position as forced win, forced loss, draw, or interaction deadlock.

No combat or terminal semantics are changed beyond correcting the Python/C++ winner mismatch.
