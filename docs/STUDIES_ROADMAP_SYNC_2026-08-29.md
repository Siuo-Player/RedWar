# RedWar — PROJECT-STUDIES Roadmap Sync

Date: 2026-08-29
Source baseline: `PROJECT-STUDIES/REDWAR/ROADMAP_STUDY.md` at `50ff8b9ecc6fd9b3b50ce3b1f2c42d3c55d32e54`.

## Current model

The roadmap is not a single linear queue. It is three coordinated tracks sharing one evidence layer:

```text
                    SHARED EVIDENCE LAYER
          replay + provenance + telemetry + Arena + Actions
                              │
          ┌───────────────────┼───────────────────┐
          ↓                   ↓                   ↓
      PRODUCT / UX       ENGINE / CORRECTNESS  EMPIRICAL AI
          │                   │                   │
       Sidebar          Bridge hardening      Strength
          ↓                   ↓                   ↓
   responsive/capture  stateful/property     Balance
          ↓          metamorphic/fuzz/recovery    ↓
 replay inspection         replay base       Search
          ↓                                     ↓
    read-only Web                              NNUE
                                                 ↓
                                      Population/QD/PSRO
```

A correctness blocker may interrupt all tracks.

## RedWar status

Implemented/integrated before this sync:

- Battle Sidebar with persistent Selected Hero, Hovered Cell/Context and contextual Actions.
- Repeated hero selection in draft, including toggle to deselect.
- Ambiguous action choice in the sidebar instead of a fullscreen modal.
- Deterministic UI scene validation/capture harness (#185).
- Bridge lifecycle/failure hardening (#186, merged into `main` at `74693812d837928076337d2f1a47f5129e43c185`).

Stateful differential fuzzing remains **pending**. PR #188 was closed unmerged after its generated sequence exposed a real Python/C++ transition mismatch.

## Immediate execution order

```text
Battle Sidebar visual/responsive completion
        ↓
stateful correctness + property/metamorphic/fuzz/recovery
        ↓
Replay / telemetry foundation
        ↓
Continuous Evidence Factory
        ↓
Strength calibration
        ↓
contextual balance / pricing / matchup
        ↓
RPG-specific search / move ordering
        ↓
NNUE baseline + parity/generalisation validation
        ↓
population / QD / PSRO when justified
        ↓
read-only Web / Replay product
        ↓
authoritative multiplayer
        ↓
reconnect / integrity / telemetry
        ↓
MMR / spectator / ranked / tournaments
        ↓
player-local themes + broader visual identity
```

## Evidence Factory rules

The Evidence Factory is a cross-cutting capability, not a second Arena or Strength pipeline.

Campaign classes:

- CORE: temporal comparability.
- COVERAGE: rare mechanics and persistent states.
- EXPLORATION: bounded discovery.
- A/B: controlled comparison.
- HOLD-OUT: protected validation.
- REAL-PLAYER: product/player behaviour.

Every campaign should retain campaign id, rules version, engine/version, configuration hash, root seed, shard, scenario distribution, sampling policy, resource budget and schema version.

Keep regression, development, exploration, promotion, hold-out and real-player evidence explicitly separated.

Daily evidence is not automatically hold-out.

## Correctness blocker currently known

The stateful cross-backend campaign found:

```text
SPELL aimed_shot A6 A1
Python: twc = 8
C++:    twc = 0
```

The test fixture uses a temporary target (`lifespan < permanent`). Under the existing game-state rule, TWC only resets when a permanent piece is captured. The C++ special-attack spell path currently resets TWC unconditionally, so this must be resolved before the stateful fuzz block can be considered complete.

Do not hide this discrepancy by changing the Python side to match the C++ implementation.

## Strength and optimisation gates

Strength work follows:

```text
correctness
→ deterministic capability probes
→ independent hold-out
→ paired Arena
→ rating + uncertainty
→ sequential test calibration
→ contextual analysis
```

Balance changes require context stratification, a mechanism hypothesis, counterfactual reasoning, one-parameter intervention and an independent rerun.

Search/NNUE should follow:

```text
RPG-specific move ordering
→ selective search where justified
→ stable classical baseline
→ NNUE feature/provenance design
→ full-rescan vs incremental parity
→ training/generalisation validation
→ Arena strength evidence
```

NNUE is not presumed to improve strength automatically; strength and performance are separate gates.

## Source authority

`RedWar/docs/ROADMAP.md` remains the execution authority inside RedWar. This file records the synchronization decision so the implementation repository retains the relevant Studies interpretation and current blockers.
