# Decision — Replay retention and local storage priority

**Date:** 2026-08-28  
**Status:** Implemented locally, subject to PR validation

## Discovery

The current game stored `GameState.move_log` only in memory. That made post-game navigation possible during the session, but closing the application lost the replay. The project-study research explicitly changes the requirement from “keep ten games” to “retain all completed games, with ten as the hot cache”.

Manual play also reproduced a legality mismatch: a spell could be exposed by the Python action-generation path while `GameState.make_action()` correctly rejected it because an enemy Inquisitor silenced the caster.

## Evidence

- `main.py` uses a single `peca_loja` selection state and stores battle actions in `GameState.move_log`.
- `GameState.make_action()` is the authoritative transition validator and rejects silenced spells.
- The study requirement calls for semantic/action replays, a ten-game hot layer, retained cold history, measured compression, and a future server-authoritative archive.

## Decision

Implement the smallest local architecture that satisfies the current product contract:

```text
completed match
    ↓
immutable semantic replay
    ↓
chunked local archive
    ├─ hot index: 10 most recent IDs
    └─ older records retained
```

The canonical representation stores the battle-start state, semantic action stream, result, provenance identifiers and a final state hash. A complete board snapshot is not stored for every ply.

Full chunks are gzip-compressed JSONL. The archive index points to `game_id → chunk + line + SHA-256`. This avoids one-file-per-game scaling problems while keeping the representation portable and inspectable.

The first fixture benchmark confirms strong compression for repetitive action streams. Compact JSON was 938/3301/10222 bytes for 12/80/320 plies; gzip JSON was 396/635/683 bytes. The benchmark harness is `tools/replay/benchmark_representations.py`. These are engineering fixture measurements, not yet a real-player corpus measurement.

## Legality decision

The engine remains the final authority. Spell generators must not advertise actions blocked by the Inquisitor silence rule. Direct malformed calls remain rejected by `GameState` rather than being silently ignored.

## Product policy boundary

The implementation does not invent server retention, account deletion, training-use consent, access-control or anonymisation policy. Those remain product decisions before backend deployment.

## Not changed

- hero prices;
- Ares evaluation/search algorithms;
- Arena thresholds;
- Strength calibration methodology;
- protected hold-out data;
- future P2P as a correctness boundary.
