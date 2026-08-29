# RedWar — Player Telemetry

## Purpose

Player telemetry is a **derived analytical evidence stream**. It is not the canonical replay and must never replace, mutate, or infer missing events in the replay.

The canonical replay remains the source of accepted semantic game actions. Telemetry records observations about the application/player interaction that are useful for UX, balance and product analysis.

## Event contract

Each event contains:

```text
schema_version
sequence
event_type
session_id
occurred_at_ms
provenance
payload
```

`sequence` is strictly increasing inside a telemetry stream. Malformed, unsupported or non-monotonic records are corruption and are rejected rather than silently repaired.

## Current event vocabulary

```text
session_started
battle_started
selection_changed
action_choices_exposed
action_selected
action_rejected
battle_finished
session_finished
```

The distinction between `action_choices_exposed` and `action_selected` is deliberate. Absence of an `action_selected` event must **not** be interpreted as the player rejecting an option or preferring another action.

## Provenance boundary

Telemetry should identify the software/rules context needed to reproduce or stratify observations, for example:

```text
rules_version
engine_version
ui_schema_version
build_commit
```

Player identity/account information is intentionally outside this initial contract. Privacy, retention, consent, export and server-side authorization remain product decisions before remote collection.

## Storage

The initial implementation is append-only UTF-8 JSONL. It is suitable for local development evidence and deterministic tests.

It is intentionally not the same store as `ReplayStore`:

```text
GameState actions → canonical replay
UI/player observations → telemetry
```

A future Evidence Factory can ingest both streams and join them by stable identifiers such as `game_id`, `session_id` and provenance without changing either source format.

## Promotion boundary

Telemetry can support hypotheses such as:

- action exposure frequency;
- cancellation/reselection frequency;
- illegal-input recovery frequency;
- time spent before choosing among exposed actions;
- UX regressions by UI schema/build;
- player/Ares matchup strata.

Telemetry alone is not strength evidence, hold-out evidence, or causal evidence. Any balance/strength conclusion must use its established independent experimental protocol.
