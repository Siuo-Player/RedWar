# Decision — UI evidence model for manual-game replay

**Date:** 2026-08-28  
**Status:** Implemented as temporary developer tooling

## Context

A normal game replay is a record of actions that actually changed the authoritative game state. This is the correct representation for deterministic reconstruction and scientific provenance, but it is not a complete record of the player's interaction with the graphical interface.

The distinction matters because the UI may prevent an action from ever reaching `GameState`. A missing action in the canonical replay can therefore have several explanations:

```text
player did not choose the action
player could not see the action
UI did not generate the action
UI generated it but the player clicked somewhere else
UI rejected the input before engine execution
engine rejected the action
```

Conflating these cases would create false conclusions about both player behaviour and game-rule correctness.

## Decision

Manual-test evidence is modelled as three related but independent layers:

```text
canonical replay
    = accepted state-changing game actions

input diagnostics
    = action attempts that reached the action executor

developer UI replay
    = observable UI state changes + player clicks
```

No layer is treated as a replacement for another.

## Canonical replay invariant

A canonical replay must remain suitable for deterministic reconstruction.

Therefore it records the initial game state, semantic accepted actions and result/provenance metadata. Search/simulation actions must not appear as player actions.

The canonical replay is not a video and does not attempt to preserve the exact rendered appearance of every frame.

## Input diagnostic invariant

Rejected input must not mutate the game state.

A diagnostic event may record:

- input category;
- source coordinate when applicable;
- destination coordinate when applicable;
- requested spell/spawn when known;
- accepted/rejected result;
- rejection reason;
- simulation flag when relevant.

These events are evidence about the interaction with the rules and validator, not canonical moves.

## UI replay invariant

The developer UI replay records enough information to reconstruct the decision context without storing screenshots or frame data.

A `ui_state` event records a semantic snapshot only when its normalized signature differs from the immediately preceding snapshot.

A `click` event records the mouse click plus the semantic UI context immediately before it.

The intended representation is therefore:

```text
60 rendered frames
        ↓
possibly 0 UI-state events

selection changed
        ↓
1 UI-state event

available action set changed
        ↓
1 UI-state event

player clicked
        ↓
1 click event
```

## Why UI transitions rather than frames

Frames are redundant for rule debugging and make replay storage large without improving semantic inference.

For the questions currently being investigated, we care about discrete transitions:

```text
which screen?
which piece selected?
which target selected?
which actions exposed?
which spell targets exposed?
which controls enabled?
what was clicked?
what did the UI become afterward?
```

These can be represented as structured state and input events.

## Available-action evidence

When a piece is selected during `BATALHA`, the developer recorder derives the action set from the same game-state legality methods used by the UI path:

```text
move targets
attack targets
stun targets
spawn targets
spell targets
```

The snapshot is diagnostic evidence of what the instrumented UI could expose at that point. It is not an alternative rules engine.

If a future UI introduces explicit action buttons or modes, their visibility must also be recorded directly rather than inferred from engine legality alone.

## Inference rules

The following hierarchy is mandatory for analysis.

### Claim: "the player did not choose X"

Allowed only when the UI replay demonstrates that X was exposed and the player had a meaningful opportunity to choose another action.

### Claim: "the UI did not expose X"

Allowed when the recorded UI state contains an explicit action set in which X is absent.

### Claim: "the engine rejected X"

Allowed when an input diagnostic records the attempted action and the executor reports rejection.

### Claim: "X was illegal"

Requires the authoritative legality rules/validator as well as the diagnostic context. A missing UI option alone does not prove the underlying rule is correct.

### Claim: "the player made a strategic mistake"

Requires a separate strategic analysis of the legal options and resulting game state. UI replay is evidence about opportunity and interaction, not proof of optimal play.

## FrostMage example

Consider a FrostMage position with a legal Nevada center and a legal movement target on the same destination square.

If the UI shows:

```text
move
Nevada
```

and the player selects move, it is meaningful evidence that Nevada was offered and not chosen.

If the UI shows only:

```text
move
```

then the replay must not say that the player declined Nevada. The UI did not expose it.

If Nevada is visible and an explicit Nevada attempt reaches the engine but is rejected, the investigation moves to the validator and rule implementation.

## Stun example

If an enemy is visibly stunned and later moves, the investigation should compare:

```text
UI state before the attempted move
canonical preceding actions
input diagnostic for the move
state snapshot / replay reconstruction
stun timer transitions
engine legality decision
```

A final replay alone may identify an apparent contradiction; the three-layer evidence model can identify where the contradiction entered the system.

## Scope of the temporary DEV mode

The developer mode is deliberately not part of the normal startup path. It is a local engineering instrument:

```text
python tools/replay/dev_main.py
```

The normal product remains:

```text
python main.py
```

Generated developer replay documents are stored outside the Git repository's tracked content under `data/replays/dev_ui/`.

## Privacy / repository hygiene

Manual developer replays may contain information about a human player's behaviour. They therefore remain local and ignored by Git by default.

They should not be committed to the public repository unless a later explicit evidence-retention decision defines what player data may be published.

## Removal / graduation

This tooling is temporary.

Before removing it, any important finding must be converted into a permanent engineering artefact:

```text
developer observation
    ↓
reproducible bug or rule test
    ↓
canonical documentation
    ↓
implementation fix if required
```

The temporary replay format is not a public compatibility contract.

## Validation requirements

Changes to this model must test at least:

```text
identical UI states are deduplicated
clicks remain distinct from UI-state events
available actions are preserved in a snapshot
normal game operation is unchanged
simulation/search activity is not recorded as player clicks
```

A future richer UI recorder should preserve these invariants rather than replacing them with frame capture.
