# Decision — 1.0-Lite Balance Lab development campaign

## Status

**Development campaign instrument defined; no balance intervention authorized.**

The 1.0-Lite Ares Balance Baseline is frozen at StockWar-Iniciante / 100,000 nodes by the completed #538 decision. This decision defines the first controlled development campaign used to collect contextual Balance Lab evidence.

## Development population

The development set contains **96 unique deterministic opening conditions and 96 games total: exactly one game per condition**.

Development seeds are generated as:

2000 + 7 × index, for indexes 0 through 95.

The runner deliberately does **not** execute a second relabelled self-play game for the same opening. With identical Ares policies on both sides, relabelling the same deterministic self-play condition would not create an independent observation.

The first-player condition is retained explicitly: the current campaign always starts with `white_to_move`. White/black winner side is recorded, but this campaign does not claim colour or first-player calibration.

## Protected hold-out reservation

A separate **96-opening protected hold-out bank** is reserved and deliberately not exposed by the development runner.

Its seeds are:

2000 + 7 × index, for indexes 96 through 191.

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
- first-player / winner-side context;
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
