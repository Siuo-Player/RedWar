# RedWar — Developer UI Replay

## Purpose

The canonical game replay is intentionally compact. It records semantic actions that actually changed `GameState`; it does not record every rendered frame.

That is sufficient for deterministic reconstruction of a completed game, but it is **not sufficient for auditing a manual interaction**. In particular, the absence of an action from the canonical replay does not establish that the player consciously declined that action. The action may never have been presented by the UI.

For manual debugging, RedWar therefore has a temporary developer-mode replay layer.

## Three evidence layers

Manual-test evidence is interpreted as three distinct layers:

```text
1. canonical game replay
   what actually changed GameState

2. action-input diagnostics
   what action attempts reached the engine and whether they were accepted/rejected

3. developer UI replay
   what the UI exposed to the player and what the player clicked
```

The layers must not be silently conflated.

### Canonical replay

The canonical replay remains the source for deterministic game reconstruction. It stores the battle-start state plus semantic actions and result/provenance information.

It does **not** imply that an unavailable action was consciously skipped.

### Action-input diagnostics

Diagnostics describe inputs that reached the action executor. They are useful for answering questions such as:

```text
player attempted X
→ engine rejected X
→ rejection reason Y
```

They are diagnostic evidence, not part of the canonical move sequence.

### Developer UI replay

The developer replay answers the missing question:

```text
what did the player actually have available to choose at the UI decision point?
```

This is essential when UI code filters legal actions before an action reaches the engine.

## What is recorded

A developer replay records semantic events only.

### UI-state transition

A `ui_state` event is recorded when the observable decision UI changes. Examples include:

- game phase/screen changes;
- selected piece changes;
- selected square changes;
- available action set changes;
- available spell targets change;
- shop selection changes;
- relevant budget changes;
- game-over state changes;
- side to move changes.

The recorder hashes a normalized representation of the state and suppresses identical consecutive states. Therefore a 60 FPS render loop does **not** create 60 replay entries per second.

### Click event

A `click` event records the player's click location together with the UI context known immediately before the click. That context can contain the current selection and the actions visible/available at that decision point.

The click is retained even when it has no legal game effect.

## What is deliberately not recorded

The developer replay does not store:

- screen images;
- Pygame surfaces;
- rendered frames;
- mouse-movement events unless a future investigation explicitly requires them;
- search simulation states as player actions;
- hidden internal engine simulations as if they were user input.

The objective is semantic interaction evidence, not a video recording.

## Interpretation rule

The following inference is valid only when the corresponding UI evidence exists:

```text
"player chose not to do X"
```

It requires evidence that:

```text
X was presented as an available option
+
player had an opportunity to select it
+
player selected another option or advanced the interaction
```

Without that UI evidence, the safer statement is:

```text
"X does not appear in the canonical action sequence"
```

## Example

Suppose FrostMage is selected.

### Case A — option visible

```text
ui_state:
  selected_piece = FrostMage
  available_actions = [move, Nevada]

click:
  selected target = E4
  context.available_actions contains Nevada

click:
  action = Nevada
```

This establishes that Nevada was exposed and chosen.

### Case B — option not exposed

```text
ui_state:
  selected_piece = FrostMage
  available_actions = [move]

click:
  target = E4
```

This does **not** establish that the player declined Nevada. It establishes that Nevada was not exposed by that UI state.

### Case C — engine rejection

```text
ui_state:
  Nevada visible
click:
  Nevada
engine:
  rejected
```

Now the investigation should compare the UI contract, the action validator and the rejection reason.

## Temporary developer mode

The current implementation is intentionally an explicit developer entrypoint rather than part of the normal product startup path:

```text
python tools/replay/dev_main.py
```

This leaves `python main.py` unchanged.

The developer overlay identifies the session as `DEV REPLAY` so that a captured run is not mistaken for a normal production replay.

Generated developer replays live under:

```text
data/replays/dev_ui/
```

and are ignored by Git because local replay data is not repository content.

## Lifecycle

```text
start DEV session
      ↓
UI transition / click events
      ↓
deduplicate unchanged UI states
      ↓
finish session
      ↓
write one semantic JSON document
```

The developer replay is a manual-test instrument, not a permanent public API commitment.

## Removal criteria

This temporary mode should be removed or replaced when the normal product has a stable, explicit interaction-observability model. Before removal, any useful findings from developer sessions should be converted into:

```text
discovery
→ evidence
→ reproducible test
→ canonical documentation
```

rather than relying on the temporary replay files as permanent project memory.
