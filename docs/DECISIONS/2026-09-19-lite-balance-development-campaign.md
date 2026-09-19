# Decision — 1.0-Lite Balance Lab development campaign

## Status

**Development campaign instrument defined; no balance intervention authorized.**

The 1.0-Lite Ares Balance Baseline is frozen at StockWar-Iniciante / 100,000 nodes by the completed #538 decision. This decision defines the first controlled development campaign used to collect contextual Balance Lab evidence.

## Development population

The campaign uses **48 unique deterministic opening conditions**, each played twice with the focus colour inverted, for **96 games total**.

The development opening seeds are generated as:

2001 + 17 × index, for indexes 0 through 47.

Each opening condition is therefore observed once with white as the focus colour and once with black as the focus colour. These are paired observations, not independent samples simply because they are two games.

## Protected hold-out reservation

A separate **48-opening hold-out bank** is reserved but is deliberately not exposed by the development runner.

Its seeds are:

2001 + 17 × index, for indexes 48 through 95.

No development analysis may treat this bank as training/calibration data. A future validation issue must explicitly decide when and how it is opened.

## Provenance contract

Every campaign record must preserve:

- source SHA;
- rules-version identity;
- engine binary SHA-256;
- compiler identity;
- hero-configuration SHA-256;
- fixed StockWar-Iniciante / 100,000-node policy;
- opening condition and seed;
- focus colour;
- initial/final RWEN;
- action trace and terminal reason;
- execution validity/failure diagnostics.

The raw game records are authoritative evidence. Derived summaries must not replace them.

## Methodological boundary

This campaign is **development evidence only**. It must not be used to claim:

- competitive Ares strength;
- global roster balance;
- intrinsic hero power independent of context;
- validity of an automatic price/mechanic change.

Any future balance intervention must preserve contextual dimensions such as hero, position, composition, matchup, initiative/colour, seed, policy and terminal context, and must use the protected hold-out separately where the intervention requires validation.

No hero price, mechanic, rules or Ares policy changes are part of this decision.
