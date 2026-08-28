# RedWar — Replay Storage

## Status

**Implemented locally; server archive remains future work.**

The canonical product goal is to retain every completed game. The current ten-game requirement is only a hot-cache policy, not a global retention limit.

```text
completed game
    ↓
canonical semantic replay
    ↓
local chunked archive
    ├─ hot index: newest 10 IDs
    └─ cold history: older games retained
```

## Canonical representation

A replay is an immutable, versioned record containing:

- `schema_version`;
- `game_id` and creation timestamp;
- rules/engine/hero-configuration provenance hashes or commit where available;
- the battle-start state;
- an ordered semantic action stream;
- termination/result metadata;
- final state hash.

The action record is compact:

```text
type, start-row, start-col, end-row, end-col, spell, spawn
```

The implementation intentionally does **not** store a full board snapshot for every ply. Reconstruction starts from the initial state and replays the semantic actions through `GameState`.

The canonical replay is separate from analytical/derived data. Aggregates may be regenerated and must not silently replace the source replay.

## Local storage layers

### Hot cache

`HOT_CACHE_SIZE = 10`.

The cache is an ordered list of replay IDs in `data/replays/index.json`. It is deliberately only an access index; it is not a deletion queue.

### Cold archive

Games are appended to `data/replays/archive/` as JSONL records. Open chunks contain up to 256 games. A full chunk is sealed as deterministic gzip-compressed JSONL.

This avoids creating one filesystem object per match while preserving simple append semantics.

The index stores:

```text
game_id → chunk + line + replay SHA-256
```

and also stores important-game markers separately.

### Important games

`ReplayStore.mark_important()` promotes a game into an explicit permanent evidence category. Current reasons are intentionally free-form so the product can distinguish cases such as:

```text
bug reproduction
balance anomaly
rare edge case
calibration evidence
important research sample
```

The local archive currently has no automatic deletion policy beyond the hot-cache rotation, which is intentional. A future product deletion/retention policy must be documented separately rather than inferred from this implementation.

## Integrity and versioning

Each record carries `record_sha256`, calculated over canonical JSON without the hash field itself. The archive index stores the same digest. Loading validates both the schema version and the content digest.

A schema mismatch or malformed archive is reported as `ReplayCorruptionError`; corrupted data is not silently converted into another game result.

## Reconstruction

`tools.replay.storage.reconstruct()` restores the battle-start state and executes each semantic action with `is_simulation=True`. This means replay reconstruction reuses the same game-state transition semantics instead of maintaining a second rules engine.

The final state hash stored in the replay provides a deterministic round-trip check.

## Representation trade-off

The repository includes `tools/replay/benchmark_representations.py` to compare:

1. readable JSON;
2. canonical compact JSON;
3. gzip-compressed canonical JSON;
4. MessagePack as an optional binary candidate.

The benchmark records:

```text
bytes/game
bytes/ply
compression ratio
serialization CPU
compression/decompression CPU
binary pack/unpack CPU when MessagePack is available
```

### Initial repeatable fixture measurement

The first benchmark was run on deterministic short/medium/long fixture records containing the same state dimensions used by the replay schema. It is an engineering baseline, **not a measurement of gameplay strength and not yet a corpus of real player games**.

| Fixture | Plies | Compact JSON | gzip JSON | gzip B/ply | gzip ratio | MessagePack |
|---|---:|---:|---:|---:|---:|---:|
| short | 12 | 938 B | 396 B | 33.00 | 2.37× | 654 B |
| medium | 80 | 3,301 B | 635 B | 7.94 | 5.20× | 1,919 B |
| long | 320 | 10,222 B | 683 B | 2.13 | 14.97× | 5,401 B |

Representative median CPU timings on the benchmark environment were:

```text
                    JSON dump    gzip compress    gzip decompress
12 plies              10.73 µs       13.18 µs          5.43 µs
80 plies              39.47 µs       19.68 µs          7.10 µs
320 plies            118.82 µs       34.73 µs          9.45 µs
```

MessagePack was smaller than uncompressed JSON but remained substantially larger than gzip JSON for these highly repetitive action streams. It also requires an additional runtime dependency. Therefore the current production choice remains **compact JSON + chunked gzip**: the representation is compact, portable, inspectable, deterministic enough for archival use and uses only the standard library at runtime.

The measurement is intentionally marked provisional: after real local games accumulate, rerun the same benchmark against the real corpus and reconsider codec/chunk sizing only if the data shows a meaningful benefit.

## Performance model

The principal random-access trade-off is intentional: loading a replay from a sealed chunk may decompress that chunk. The current chunk size of 256 games favours storage simplicity and bounded decompression work over a second, more complex block index. If measurements show that replay inspection becomes a bottleneck, a future version can add smaller compressed blocks or checkpoints without changing the canonical replay schema.

Scaling is therefore approximately:

```text
N games
→ N / 256 archive chunks + one index
```

rather than N files.

## Future server model

When a backend exists, the preferred architecture becomes:

```text
client
  → compact replay payload
  → server authoritative archive

client
  ← recent games / requested replay
```

The same canonical representation should be uploadable directly or via a transport wrapper. The server is the future durability boundary; the client archive remains a cache/offline layer.

Peer-assisted distribution is deliberately **not** part of the correctness boundary. It can only become an optimisation after availability, integrity, authentication, privacy, deletion, replication and malicious-peer handling are specified.

## Derived analytics

The archive is canonical source data. A future materialized analytical layer may derive:

- hero usage and result rates;
- hero × opponent and hero × color matrices;
- composition frequency;
- game-length distributions;
- action/termination histograms;
- player-vs-Ares summaries;
- version drift.

Those results are caches and research outputs. A sequence-level question must fall back to the canonical replay.

## Privacy and product-policy boundary

The current implementation intentionally avoids inventing a full account/retention policy. The following remain product decisions to document before server deployment:

- who can view a replay;
- who may delete it;
- how long the server retains it;
- whether player games may be used for AI training;
- export/portability rules;
- anonymisation/pseudonymisation requirements;
- authentication and authorisation for server access.

Local replay files are treated as player-owned client data in the engineering model, but no stronger legal/product claim is made here.

## Relationship to Arena/Strength evidence

Real player games and Arena/hold-out experiments are different evidence classes. Local replays may generate hypotheses and debugging evidence, but they must not silently become protected promotion or hold-out evidence.

Arena evidence retains its existing provenance/statistical methodology and does not depend on the local replay cache.
