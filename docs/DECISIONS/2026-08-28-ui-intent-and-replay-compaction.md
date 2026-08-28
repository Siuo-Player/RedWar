# UI intent and developer replay compaction

## Findings

Manual play exposed three interaction problems:

1. FrostMage could select Nevada with its own square as the center.
2. A board destination could correspond to more than one legal action, while the UI silently preferred movement, attack, stun, spawn or spell according to an implementation order.
3. Developer UI evidence included high-frequency hover/window state and could therefore grow far faster than the semantic decisions it was intended to preserve.

## Decisions

### Nevada self-center

The Nevada center set excludes the FrostMage's own square. The restriction is enforced in the Python rules layer and remains subject to Python/C++ differential coverage.

### Action intent

A destination with exactly one legal action executes directly. A destination with multiple legal actions must present the alternatives to the player and must not silently choose one.

Manual DEV sessions also support cancelling a selection by clicking the currently selected hero again, and clicking another allied hero changes the selection instead of executing an accidental action.

### Ally/self offensive targets

An offensive spell directed at an allied hero, including the spell caster itself, requires explicit confirmation before execution. Support spells such as `purify` and `swap` retain their normal friendly-target semantics.

### Replay evidence

Canonical game replays remain the primary executed-action evidence. Developer UI replay remains secondary evidence for what the player was actually shown.

Developer UI replay schema v2 stores:

- unique semantic UI states;
- unique action sets;
- ordered clicks referencing the exact visible state before the click;
- elapsed time rather than a timestamp on every event;
- no per-frame hover position or window-size duplication.

This preserves the key inference:

```text
click
  ↓
exact visible state
  ↓
complete legal action set exposed to player
```

without repeating the same state payload hundreds or thousands of times.

## Preservation rule

No decision-relevant information is deliberately discarded. Repetition is removed by interning equivalent states/action sets; canonical replays retain executed actions, and developer replay retains the UI choice context needed to distinguish "not chosen" from "not available".

## Scope

This is interaction/evidence infrastructure. It does not rebalance Ares, alter Strength methodology, or change holdout/promotion policy.
