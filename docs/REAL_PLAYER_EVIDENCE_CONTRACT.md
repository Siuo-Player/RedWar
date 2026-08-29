# RedWar — Real-Player Evidence Contract

This document operationalizes the current PROJECT-STUDIES decision that human-player evidence is a distinct evidence class from synthetic Arena data.

## Minimum future-compatible context

When available, derived telemetry should preserve:

- `game_id`;
- build/rules/engine provenance;
- `mode`;
- pseudonymous `session_id`;
- event sequence and timestamp;
- `turn`;
- action/selection context;
- result;
- termination reason.

The existing telemetry schema remains version 1 because these fields are carried as event payload context rather than mandatory top-level fields. Older records remain readable.

## Evidence boundary

Telemetry is derived evidence. Canonical replay remains the authoritative accepted-action record. Missing telemetry must never be interpreted as player intent.

Synthetic evidence and human evidence must remain separate analytical populations:

```text
synthetic Arena → strength / regression / search evidence
human telemetry → behaviour / UX / player-facing evidence
```

## Analysis discipline

Human data must be checked for missingness, truncated sessions, reconnects, duplicates, version drift and timestamp/order inconsistencies before aggregation.

Claims about confusion, frustration or perceived fairness require validated human-study measures; they are not telemetry fields by default.
