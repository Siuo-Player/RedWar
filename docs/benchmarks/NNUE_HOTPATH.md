# NNUE hot-path baseline

The current C++ evaluator uses the NNUE accumulator implementation, but the evaluation path explicitly synchronizes the board before every inference. The NNUE implementation also exposes incremental change hooks intended for normal search.

This document records the next optimization target: move normal search from full `sync_board()` scans to incremental accumulator maintenance while preserving a full-sync reference path for parsers/tests.

Validation requirements:

- Python regression suite unchanged.
- C++ smoke and numeric tests unchanged.
- NNUE feature/regression tests unchanged.
- Tactical benchmarks unchanged in best moves and thresholds unless the optimization improves them.
- Arena must not regress.
- Measure nodes/second before and after on the same engine build flags and positions.
