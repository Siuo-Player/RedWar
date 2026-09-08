# Canonical legal-action boundary — 2026-09-08

## Decision

`engine.legal_actions` is the canonical engine-facing action-space adapter. Piece-level generators remain the rule primitives, while integration code crosses to legacy dictionaries explicitly through `to_legacy_dict` / `to_legacy_dicts`.

The Python analysis path now consumes that explicit boundary instead of performing an inline conversion itself.

## Scope

This tranche is intentionally limited to representation and API authority. It does not change hero legality rules or action execution semantics.

The remaining runtime consumers that still query piece generators directly are tracked separately; migrating them will be done incrementally so any semantic divergence is isolated as a correctness finding rather than silently changed.
