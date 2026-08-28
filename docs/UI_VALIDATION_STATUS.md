# RedWar — UI Validation Status

## Scope

This document records the validation contract for the Battle Sidebar after PR #184.

## Current baseline

Implemented and merged:

- persistent Selected Hero section;
- Hovered Cell / Context section;
- contextual Actions section;
- ambiguous-destination action choice in the sidebar;
- keyboard action selection and cancellation;
- repeated hero selection in Draft with explicit toggle-off.

Not yet validated automatically:

- responsive resizing across representative desktop widths;
- focus-state presentation;
- illegal-target recovery presentation;
- visual regression through captured scenes.

## Validation matrix

| Scenario | Expected invariant |
|---|---|
| Idle | Sidebar remains legible without inventing contextual data |
| Hero selected | Hero information remains visible while hover changes |
| Hovered cell | Cell context changes without replacing Selected Hero |
| One legal action | No unnecessary action picker |
| Multiple legal actions | Complete legal set appears in Actions section |
| Illegal destination | Selection remains coherent; no silent action substitution |
| Keyboard focus | Focusable action remains visibly identifiable |
| Narrow window | Semantic sections remain distinguishable and usable |
| FrostMage / Nevada | Selection, hover, spell context and ambiguity remain readable |

## Capture strategy

Visual validation should eventually produce deterministic scene captures for at least:

1. idle battle;
2. selected hero + hovered cell;
3. ambiguous action choice;
4. illegal destination;
5. FrostMage/Nevada contextual state;
6. narrow-window layout.

The capture mechanism should be a test/diagnostic surface, not part of game rules or Ares.

## Acceptance

A UI validation package is complete only when the above scenarios can be reproduced deterministically and the captures can be inspected or compared without requiring a live opponent.
