# Ares LMR experiment status

The first conservative single-ply LMR candidate is tracked in PR #500.

The candidate changes only `ai/cpp_engine/search.cpp` and reduces eligible late `MOVE` actions by one child ply at depth >= 4, with the first move, TT principal move, non-MOVE actions, and active STUN continuations excluded. A reduced bound improvement is re-searched at full depth.

PR #500 passed the repository CI suite, including build, tests, CodeQL, FrostMage regression, and the existing 100-game AI quality Arena.

The 100-game Arena result is diagnostic only. The current `ai_quality_gate.yml` still invokes the generic `arena_tournament.py --jogos 100 --margem-vitorias 10`, while the authoritative promotion methodology requires `promotion_arena.py` plus `promotion_gate.py` and sequential paired-bootstrap lower-bound evidence at the fixed stages 96, 192, 320, and 512 games. Therefore the CI string `promoted` is not treated as an authoritative promotion decision for LMR.

No LMR merge is authorized until the candidate has passed the authoritative promotion evidence path under #372.
