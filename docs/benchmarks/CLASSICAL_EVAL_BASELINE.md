# Ares — Classical Evaluation Baseline

**Governing issue:** #411  
**Parent:** #406 → #372  
**Baseline branch:** `main`  
**Evaluator source:** `ai/cpp_engine/evaluate.cpp`  
**Source blob:** `5fbad5fd9ae97f683628411febcffa477409261b`

This document freezes the current classical evaluator as the comparison baseline for future Ares experiments. It is an engineering baseline, not a strength claim.

## Evaluation pipeline

```text
piece value
+ positional bonus
+ FrostMage pressure
+ TWC directional adjustment
→ classical score
```

The terminal values are handled before the non-terminal score:

- no White pieces → `-INFINITO + 100`;
- no Black pieces → `INFINITO - 100`.

## Term inventory

### 1. Piece cost

`safe_piece_cost()` obtains the configured piece cost when the native identifier is valid, otherwise falls back to the piece's embedded cost and finally to `50`. The result is clamped to a safe maximum.

### 2. Lifespan

Temporary pieces (`lifespan != 999`) scale their base value by `lifespan / 5`, with the lifespan bounded to a safe interval before multiplication.

### 3. Positional tables

The current evaluator contains explicit PSTs for:

- Ghoul;
- Sentry;
- FrostMage;
- Lich (sharing the FrostMage table);
- BoneLord;
- Phantom.

Other heroes currently receive no additional PST term.

### 4. Stun state

A stunned piece has its value and positional bonus reduced to 40%. A threat term derived from half the configured piece cost then changes the signed contribution. This is part of the current baseline and must not be silently changed during unrelated search experiments.

### 5. FrostMage pressure

An active FrostMage receives pressure from enemy pieces within Manhattan distance 4. A currently stunned target contributes 50% of its cost; an unstunned target contributes 10%, with the aggregate pressure capped per mage at 40. The total pressure is then signed by team.

### 6. TWC

For non-terminal positions, `board.twc` is subtracted from a positive score or added to a negative score. This preserves the current directional pressure toward the 50-turn no-capture boundary.

## NNUE boundary

`evaluate_board()` first checks the optional native NNUE path. When NNUE is available it performs a full `sync_board()` and returns the NNUE result; otherwise it returns `evaluate_classical_board()`.

Therefore this file is specifically the **classical evaluator baseline**, independent of any claim that the optional NNUE path is stronger.

## Experimental rule

Future evaluator experiments must isolate one hypothesis/term at a time and compare against this exact implementation under matched search budgets. A scalar evaluation difference, lower training loss, or improved tactical puzzle result is not sufficient evidence for a global strength claim.

The source blob above identifies the implementation frozen by this baseline. When a candidate changes evaluator code, update the experimental record with the new commit/source hash rather than silently redefining this baseline.
