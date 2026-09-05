# Battle Sidebar — contextual Encyclopedia integration

## State
Implemented in PR #279 and validated by the full repository CI suite.

## Contract
- Selected hero remains the persistent anchor in the battle sidebar.
- The player can open the selected hero's rules without leaving the battle board.
- The contextual panel sources its content from the canonical `HERO_DEFS` path through `HeroEncyclopediaContext`.
- The contextual panel is presentation-only: it does not determine legality or execute actions.
- The contextual panel supports bounded vertical navigation so long rule summaries do not overflow the sidebar.
- Selecting another hero resets the contextual panel state and scroll position.
- Closing the contextual panel restores the hover/context view.
- Existing action-choice and confirmation surfaces remain in the same sidebar and continue to use the established interaction policy.

## Validation
PR #279 CI:
- RedWar Test Suite #1431 — success (401 tests)
- RedWar AI Quality Gate #562 — success
- RedWar CodeQL #466 — success

## Follow-up candidates
- Add keyboard shortcuts for opening/closing and scrolling the contextual Encyclopedia.
- Reuse the same model directly in the standalone Encyclopedia renderer to remove remaining presentation duplication.
- Capture deterministic UI validation scenes at the supported viewport classes before broader visual polish.
