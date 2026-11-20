# Arena #597 — deterministic recomputation from preserved raw JSONL

**Status:** reproduced from the original GitHub Actions artifact; descriptive evidence only  
**Governing issue:** [#597](https://github.com/Siuo-Player/RedWar/issues/597) under [#372](https://github.com/Siuo-Player/RedWar/issues/372)  
**Workflow run:** [37858487666](https://github.com/Siuo-Player/RedWar/actions/runs/37858487666)  
**Artifact:** [11584718698](https://github.com/Siuo-Player/RedWar/actions/runs/37858487666) — `redwar-arena-experiment-0eccfa8d0f68af488cce87b6191af26e3b0961a9`  
**Artifact ZIP SHA-256:** `164b0a332d1a5ad66303ff2053b8386bbbc70de6eedbc880c6d0b7bc0d5a5da8`  
**Raw JSONL SHA-256:** `249a5dc14e551c8cc24406d1ed712f54693b5e00f9d20fd4dc20b26ba53e0bc2`

## Frozen inputs

- Baseline: `48dd4df0f6809d072190291bceebb09ddfe52e5f`
- Challenger: `3826b3bfe5c63102677f4a097163aeda4a03f83d`
- Rules version: `48dd4df0f6809d072190291bceebb09ddfe52e5f`
- Budget: 10,000 nodes per move
- Raw records: 100 games, 100 valid, 0 invalid
- Declared authority: `promotion_authority=false`

## Independent recomputation

Re-reading every non-empty JSONL record and counting the raw `outcome` fields yields:

| Outcome | Games |
|---|---:|
| Challenger wins | 54 |
| Baseline wins | 46 |
| Draws | 0 |
| Invalid | 0 |
| **Total** | **100** |

The paired/color audit independently confirms 50 distinct pairs, each containing two games with the same opening index and seed and opposite challenger colours. There are no incomplete or structurally invalid pairs.

| Challenger colour | Challenger wins | Baseline wins | Games |
|---|---:|---:|---:|
| White | 30 | 20 | 50 |
| Black | 24 | 26 | 50 |

The 50 complete pairs aggregate to 10 pairs where the challenger wins both games, 34 split-result pairs, and 6 pairs where the challenger loses both games. The raw sequence cycles through 16 openings: the first two openings have 4 pairs each (8 games each), and the other 14 have 3 pairs each (6 games each). The contextual diagnostic flags this as opening-count imbalance; it is a property of distributing 50 pairs across 16 openings and should remain visible when interpreting the result.

## Why the rating signs differ

Replaying the legacy Elo-compatible update in the original JSONL order gives:

- Sequential Elo delta: **−16.9931**.
- Existing uncertainty value: **±755.0803**, an engineering proxy, **not** a calibrated confidence interval.
- Aggregate score: `54 / 100 = 0.54`.
- Descriptive Elo-equivalent derived only from aggregate score: `400 × log10(0.54 / 0.46) = +27.8544`.

These quantities answer different questions. The sequential delta depends on the order in which results update the current rating; the aggregate-score equivalent depends only on the final score and is order-invariant. The latter is only a descriptive transformation, not a calibrated matchup-strength estimate or promotion criterion. Neither replaces the predeclared paired analysis or colour/opening context.

## Promotion-authority defect

The original summary says `promoted=true` because `win_threshold=0`, despite the provenance explicitly setting `promotion_authority=false`. This is a reporting/contract defect, not evidence that the experiment was authoritative. PR #600 adds an explicit non-authoritative mode, preserves the legacy `promoted` field as false in that mode, and records `promotion_decision=not_authorized`.

The original artifact and raw JSONL were not modified. This note records recomputation only; it does not promote either engine revision and does not close #372 or #488.
