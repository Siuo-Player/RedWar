# Diagnostic — A/A-B frozen engine returns `bestmove 0000`

**Status:** investigation-only

A/A-B run `33413842213` on the declared `aa-baseline-b-v1` context failed during Arena execution at a non-terminal position. The Python bridge reported `bestmove 0000` after 250000 nodes.

The exact position was reproduced independently through the C++ move-generation bridge and has legal moves, so the failure is not currently attributed to root move generation.

The next diagnostic is to run the frozen native engine directly on that position and preserve its native `info string search error` output if search throws. No calibration result is valid until the failure is resolved.

The two additional A/A-B runs triggered while preparing the diagnostic branch are explicitly invalid experiment attempts and must not be used as evidence.
