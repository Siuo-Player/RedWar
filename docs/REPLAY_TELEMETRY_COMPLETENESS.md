# Replay ↔ Telemetry Completeness Audit

The canonical replay is authoritative for accepted game actions. Manual telemetry is derived evidence about the interaction surface.

`tools/analytics/replay_telemetry_completeness.py` compares the two streams by `game_id` and reports:

- expected human-player actions from the canonical replay;
- observed `action_selected` telemetry;
- exact action matches;
- action mismatches;
- missing telemetry actions;
- extra/unattributed telemetry;
- games with no telemetry at all;
- malformed selected-action events without a `game_id`.

## Interpretation rules

A missing telemetry event means only that the derived observation is incomplete. It does **not** mean that the player cancelled, rejected, ignored or preferred another action.

Likewise, telemetry does not establish legal action sets or game-state truth. Those remain properties of the canonical replay and authoritative rules engine.

The audit therefore returns `status = audit_only_no_intent_inference` and keeps missingness as a separately measured quantity.

## Player action extraction

The current local replay format declares `metadata.player_side`. Since local turns alternate by ply, the audit selects the corresponding plies as the human player's canonical action sequence. Unsupported or missing side metadata causes the audit to fail rather than silently infer a population.

## Evidence boundary

This audit is observational. It does not repair replay data, mutate telemetry, infer player intent, or provide causal evidence about UX or balance.
