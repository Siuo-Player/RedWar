# Battle Sidebar — contextual Encyclopedia status

## Implemented
- **PR #279:** integrated the contextual hero Encyclopedia into the battle sidebar with bounded scrolling.
- **PR #280:** unified the standalone Encyclopedia with the canonical `HeroEncyclopediaContext` model.
- **PR #281:** exposed the canonical passive rule in the contextual panel.

## Validation
- PR #279: Test Suite #1433, AI Quality Gate #563, CodeQL #467 — success.
- PR #280: Test Suite #1440, AI Quality Gate #565, CodeQL #470 — success.
- PR #281: Test Suite #1444, AI Quality Gate #566, CodeQL #472 — success.

## Contract
The contextual panel is presentation-only. Hero rules are sourced from canonical `HERO_DEFS` through `HeroEncyclopediaContext`. The panel exposes description, movement, attack, passive, spells and special rules; selection changes reset panel state and scroll position; bounded scrolling prevents long rule text from overflowing the sidebar.

## Remaining validation work
Keyboard operation and deterministic screenshot/scene capture are not yet implemented. These should be treated as separate changes so input policy and visual-regression infrastructure remain independently testable.
