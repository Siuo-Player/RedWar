# RedWar — Roadmap Synchronization Note — 2026-08-29

This note records the synchronization with the latest `Siuo-Player-PROJECT-STUDIES/REDWAR` state.

## Study-layer order adopted

The current package order is:

1. Battle Sidebar implementation.
2. Responsive / visual validation with deterministic captures.
3. Replay / player telemetry evidence.
4. Strength / balance / Ares empirical sequence.
5. Search / move-ordering RPG optimization.
6. Incremental NNUE work.
7. Web / app / multiplayer presentation.

The first item is now implemented and merged in upstream RedWar. The second item is represented by the deterministic scene-validation harness in PR #185.

## Sidebar contract carried forward

The sidebar is treated as three semantic regions:

- Selected Hero: persistent selection state.
- Hovered Cell / Context: transient contextual state.
- Actions: contextual decision surface, shown when an explicit action choice is required.

The renderer must consume existing game semantics and must not own game-rule decisions.

## Validation scenes

The canonical visual-validation set is:

- `battle_idle`
- `selected_hero_hovered_cell`
- `ambiguous_action_choice`
- `illegal_destination`
- `frostmage_nevada`
- `narrow_window`

FrostMage/NEVADA remains the principal visual stress case because it combines selection, hover, spell preview, action ambiguity and persistent effects.

## Evidence boundary

Passing PNG-generation tests establishes deterministic capture capability. It does not establish that the visual design is subjectively optimal. Human inspection of generated captures remains part of the UI validation loop.

Balance changes remain deferred until empirical Arena/replay evidence is sufficient, consistent with the Study-layer strength methodology.
