# RedWar — Battle Sidebar

## Status

Implemented in PR #184. The current implementation is the first functional slice of the sidebar architecture defined by the `PROJECT-STUDIES` research package. Responsive/visual validation remains pending.

## Architecture

The battle sidebar is a persistent contextual surface divided by semantic responsibility:

```text
RIGHT SIDEBAR
├── Selected Hero
│   persistent identity, state and relevant rules
│
├── Hovered Cell / Context
│   transient cell, piece, effects and consequences
│
└── Actions
    contextual decision surface; only expanded when a destination has
    more than one legal action
```

The three states are intentionally distinct:

- **Selected Hero** persists while the player works with that unit.
- **Hovered Cell** changes with the cursor and never replaces the selected-hero state.
- **Actions** is a decision surface, not an information dump; it becomes relevant when the destination is ambiguous.

## Current interaction contract

- One legal action: execute directly.
- Multiple legal actions: expose the complete legal action set in the sidebar.
- Zero legal actions: keep the selection coherent and show the destination as invalid.
- `1..9`: choose an action when the action panel is active.
- `ESC`: cancel the pending action choice.
- The board remains visible during action disambiguation.
- The renderer does not decide legality; it consumes the existing interaction/game semantics.

## Draft interaction

Draft hero selection is persistent and toggleable:

1. click a shop hero to select it;
2. click board cells to place repeated copies while budget and placement rules allow it;
3. select another shop hero to replace the current selection;
4. click the selected shop hero again to deselect it.

This is a domain interaction rule, not merely a visual state.

## Visual design constraints

The immediate sidebar should already provide:

- semantic visual roles rather than arbitrary decoration;
- clear selected, hover and focus states;
- neutral-dominant surfaces;
- readable typography and useful target sizes;
- redundant signalling for important states so colour is not the only cue;
- restrained feedback and no fullscreen modal for normal action disambiguation;
- useful use of the available right-side space without filling it with low-value text.

The complete art/theme system is deliberately a later product layer.

## Validation still required

The next validation package should cover:

- desktop wide, medium and narrow window sizes;
- selected-hero persistence while hover changes;
- ambiguous actions (`MOVE` vs `ATTACK`, `MOVE` vs `NEVADA`, etc.);
- keyboard focus/action selection;
- illegal-target recovery;
- silence/stun/lifespan/cooldown visibility where relevant;
- FrostMage/Nevada as the visual stress scenario;
- automatic screenshots/scene captures for regression review.

## Source of truth

Operationally, tested game behaviour is authoritative. The sidebar is a presentation and interaction layer over those semantics. Research documents in `Siuo-Player-PROJECT-STUDIES/REDWAR` define the recommended UX architecture and visual constraints; they do not override implemented game rules.
