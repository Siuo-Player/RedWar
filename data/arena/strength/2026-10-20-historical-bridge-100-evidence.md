# Historical Arena bridge evidence — 2026-10-20

**Governing issue:** [#488](https://github.com/Siuo-Player/RedWar/issues/488)  
**Related diagnostic:** [#597](https://github.com/Siuo-Player/RedWar/issues/597)  
**Predeclared plan:** `data/arena/strength/plans/2026-10-06-historical-bridge-v1.json`  
**Workflow run:** [37858487666](https://github.com/Siuo-Player/RedWar/actions/runs/37858487666)  
**Artifact:** `11584718698` — `redwar-arena-experiment-0eccfa8d0f68af488cce87b6191af26e3b0961a9`

## Frozen provenance

- Artifact ZIP SHA-256: `164b0a332d1a5ad66303ff2053b8386bbbc70de6eedbc880c6d0b7bc0d5a5da8`
- Raw game JSONL SHA-256: `249a5dc14e551c8cc24406d1ed712f54693b5e00f9d20fd4dc20b26ba53e0bc2`
- Validation JSON SHA-256: `8db78b68fd71e7402fb94570944c391639c02890530cb234e6b8c9d1d2ce120e`
- Provenance JSON SHA-256: `fa49a0caea2a0c7559a31998b1296c4d55cfd9d2e9ee43d50135fcd53157c1a9`
- Summary JSON SHA-256: `21a66ea09581448af73cb7863072c52a34bd9cf0b7ec8c44c925fc62f545cdd0`
- Baseline: `48dd4df0f6809d072190291bceebb09ddfe52e5f`
- Challenger: `3826b3bfe5c63102677f4a097163aeda4a03f83d`
- Rules version: `48dd4df0f6809d072190291bceebb09ddfe52e5f`
- Node budget: 10,000 nodes per move
- Promotion authority: **false**; result is descriptive only.

The artifact ZIP and raw JSONL hashes were recomputed from the downloaded original artifact. The JSONL contains exactly 100 contiguous game indices and 50 complete pairs; every pair has two members, a shared seed/opening and opposite challenger colours.

## Recomputed outcomes

| Measure | Result |
| --- | ---: |
| Valid games | 100 |
| Invalid games | 0 |
| Challenger wins | 54 |
| Baseline wins | 46 |
| Draws | 0 |
| Complete colour-inverted pairs | 50 |
| Challenger as White | 30 wins / 20 losses |
| Challenger as Black | 24 wins / 26 losses |
| Pair bins | WW=10, split=34, LL=6 |

The fixed seed set contains 16 openings. Openings 0 and 1 each occur in four pairs (eight games); openings 2–15 each occur in three pairs (six games). This imbalance is a known limitation of distributing 50 pairs over 16 fixed openings and remains part of the interpretation.

## What the edge represents

Commit comparison from baseline to challenger shows:
- The C++ search/evaluation delta removes a full NNUE board resynchronisation from the per-node evaluation hot path, relying on the incremental accumulator maintained by board mutation hooks.
- The Python `GameState` delta adds only `replay_metadata`; it does not change transition rules.
- The declared rules version therefore remains the baseline commit.

The aggregate score is 54%, corresponding to a purely descriptive `+27.8544` Elo-equivalent transformation. The legacy sequential rating delta is `-16.9931` and depends on raw result order. These are different descriptive quantities; neither is a calibrated strength estimate or promotion criterion.

## Compatibility caveats

This comparison is registered as a provenance-addressed edge for **descriptive graph connectivity only**. It is not a promotion decision and is not lifecycle-neutral.

1. `arena_tournament.py` creates one challenger and one baseline `CppEngineBot` for the whole 100-game run. Their engine subprocesses persist across games, so process-global transposition-table state can carry between games.
2. The existing 512-game promotion edge creates fresh bots for each stage and uses 256 fresh opening pairs. This bridge instead repeats 16 canonical openings across 50 pairs.
3. The lifecycle diagnostic has shown that process persistence can change outcomes under the tested protocol. The different process lifecycle and opening population must therefore remain visible and must not be silently treated as identical sampling conditions.
4. The historical ledger's graph-connectivity criterion is now met, but this does **not** establish a calibrated global Elo scale. Future calibration must standardise or model lifecycle/opening context and be repeated across real Arena experiments.

The run's legacy `promoted=true` summary field was caused by `win_threshold=0`; provenance explicitly says `promotion_authority=false`. PR #600 corrects the reporting contract. This artifact does not promote or reject Ares and does not alter the authoritative #372 gate.

## Follow-up methodology
Issue [#617](https://github.com/Siuo-Player/RedWar/issues/617) tracks the unresolved calibration problem: the connected graph is descriptive, while opening-population, pair dependence and process-lifecycle differences must be modeled or standardized before publishing a calibrated global rating.
