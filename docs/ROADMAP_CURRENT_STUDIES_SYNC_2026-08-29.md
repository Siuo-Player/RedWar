# RedWar — Current Studies Roadmap Sync — 2026-08-29

This file is the current operational addendum to `docs/ROADMAP.md`. It records the latest `PROJECT-STUDIES` decision state without rewriting historical roadmap detail.

Source: `Siuo-Player/Siuo-Player-PROJECT-STUDIES` commit `265fe637cd27b77c50670bbbd9a9d9d4dc92e584`, especially `META/ROADMAP_MASTER.md`, plus the RedWar Strength Calibration v2 and current-state studies.

## Operating model

RedWar development is now explicitly **non-linear**. Shared foundations are continuous infrastructure; UI, evidence collection and AI evaluation can progress in parallel when their dependencies are satisfied.

```text
SHARED EVIDENCE / CORRECTNESS FOUNDATION
replay + provenance + telemetry + differential + Arena
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
 correctness/UX  empirical AI  product
        │           │           │
     UI + telemetry Strength   replay/Web
        ↓           ↓           ↓
 regression       balance      multiplayer
 corpus/context      ↓
                   search
                     ↓
                    NNUE
```

## Current RedWar gates

### NOW

```text
replay ↔ telemetry completeness / missingness validation
        ||
Battle UI responsive + visual regression validation
        ||
Continuous Evidence Factory activation on real source contracts
```

These streams can proceed concurrently.

### AI critical path

```text
stateful correctness closure
→ independent controlled evidence
→ Strength calibration
→ protected hold-out
→ contextual matchup / Balance Lab
→ RPG-specific search / move ordering
→ selective search improvements
→ stable classical evaluation baseline
→ NNUE correctness + training validation
→ Population/QD/PSRO only when diversity evidence justifies it
```

### Product path

```text
canonical replay
→ read-only Web viewer
→ authoritative multiplayer
→ reconnect / idempotency / integrity
→ MMR / matchmaking
→ spectator / ranked / tournaments
```

## Strength calibration rule

Strength infrastructure already exists; the remaining problem is **calibration**, not additional rating plumbing.

Required diagnostic ladder:

```text
Level 0: A = A
Level 1: A vs deliberately weakened A
Level 2: A vs independently demonstrated improved A
```

For every level, preserve:

```text
experimental unit
colour/scenario pairing
seed policy
rules/configuration provenance
valid / invalid / unfinished outcomes
termination reason
rating
uncertainty
```

Do not treat a single Elo/rating estimate as proof of global strength. The current uncertainty proxy remains a proxy until empirical coverage is demonstrated.

## Continuous observability rule

Canonical replay remains authoritative for accepted game actions and deterministic reconstruction.

Telemetry is derived evidence for interaction/presentation observations.

Therefore:

```text
missing telemetry != rejected action
missing telemetry != player intent
telemetry != replay repair
telemetry != causal evidence
telemetry != strength estimate
```

The replay↔telemetry audit must expose missingness explicitly rather than silently imputing absent events.

## Gate definitions

A new AI/search change must satisfy:

```text
correctness
→ capability/regression evidence
→ protected independent evidence
→ paired Arena
→ calibrated strength + uncertainty
→ contextual slices
→ performance
→ promotion decision
```

A balance change must satisfy:

```text
observed signal
→ context stratification
→ mechanism hypothesis
→ controlled intervention
→ independent rerun
→ human evidence when the claim is player-facing
```

A UX change must satisfy:

```text
semantic correctness
→ visual regression
→ task/usability evidence
```

## Anti-overengineering constraint

Do not add a large analytics platform, permanent self-mutating AI loop, PSRO, ranked system or free-form theme editor merely because the technology is available. Each requires a concrete problem and evidence threshold.

## Historical/source-of-truth rule

`PROJECT-STUDIES` records research decisions and evidence boundaries. `RedWar` remains the upstream implementation authority. This addendum is intentionally separate from historical roadmap detail.
