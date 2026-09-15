# Ares LMR experiment status

The first conservative single-ply LMR candidate is tracked in PR #500.

The candidate changes only `ai/cpp_engine/search.cpp` and reduces eligible late `MOVE` actions by one child ply at depth >= 4, with the first move, TT principal move, non-MOVE actions, and active STUN continuations excluded. A reduced bound improvement is re-searched at full depth.

PR #500 passed the repository CI suite, including build, tests, CodeQL, FrostMage regression, and the existing 100-game AI quality Arena.

The 100-game Arena result is diagnostic only. The authoritative promotion methodology now requires `promotion_arena.py` plus `promotion_gate.py` and sequential paired-bootstrap lower-bound evidence at the fixed stages 96, 192, 320, and 512 games. The legacy generic Arena margin result is not treated as a promotion decision.

No LMR merge is authorized until the candidate has passed the authoritative promotion evidence path under #372.

#503 is merged and provides that authoritative CI path for strength-sensitive changes.

#504 is also merged and adds a dedicated authoritative Ares workflow identity; this commit only refreshes the experiment status to trigger a fresh PR synchronization run.