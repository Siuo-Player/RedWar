# Battle Sidebar — contextual Encyclopedia integration

## State
Implemented in PRs #279, #280 and #281. The contextual Encyclopedia is integrated into the battle sidebar, shares the canonical hero context with the standalone Encyclopedia, and exposes the passive rule in the contextual view.

## Contract
- Selected hero remains the persistent anchor in the battle sidebar.
- The player can open the selected hero's rules without leaving the battle board.
- The contextual panel sources its content from the canonical `HERO_DEFS` path through `HeroEncyclopediaContext`.
- The contextual panel is presentation-only: it does not determine legality or execute actions.
- The contextual panel supports bounded vertical navigation so long rule summaries do not overflow the sidebar.
- The contextual view exposes description, movement, attack, passive, spells and special rules from the canonical context.
- Selecting another hero resets the contextual panel state and scroll position.
- Closing the contextual panel restores the hover/context view.
- Existing action-choice and confirmation surfaces remain in the same sidebar and continue to use the established interaction policy.

## Validation
PR #279 — Test Suite #1433, AI Quality Gate #563, CodeQL #467: success.
PR #280 — Test Suite #1440, AI Quality Gate #565, CodeQL #470: success.
PR #281 — Test Suite #1444, AI Quality Gate #566, CodeQL #472: success.

## Remaining follow-up
- Add keyboard shortcuts for opening/closing and scrolling the contextual Encyclopedia.
- Capture deterministic UI validation scenes at the supported viewport classes before broader visual polish.

The standalone Encyclopedia now consumes the same canonical presentation model as the contextual panel, so movement, attack and special-rule formatting no longer has two independent renderer implementations.
