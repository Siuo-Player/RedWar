# RedWar — Manual Runtime Telemetry

The developer entrypoint `tools/replay/dev_main.py` now installs a best-effort `TelemetryRecorder` around the existing manual-play instrumentation.

The runtime adapter observes semantic interaction boundaries only:

- `session_started` once per developer session;
- `battle_started` when the controller enters `BATALHA`;
- `selection_changed` only when the selected square actually changes;
- `action_choices_exposed` when the manual action picker is shown;
- `action_selected` only after `GameState.execute_action()` accepts the action;
- `action_rejected` when the player cancels a displayed choice.

A session receives its own telemetry JSONL stream under `data/replays/telemetry/`, so sequence numbers are local to that stream and remain strictly increasing.

Telemetry is derived evidence. It does not replace the canonical semantic replay, determine legal actions, or infer player intent from missing records. Storage errors are reported to the telemetry layer and do not block gameplay.

The local developer session records build/rules/engine provenance using the current build commit and `battle-sidebar-v1` UI schema identifier.
