# RedWar — Current Roadmap Snapshot (2026-08-29)

Source of truth reconciled against `Siuo-Player/Siuo-Player-PROJECT-STUDIES` at:

- status reconciliation: `6b0ee86a073b0703764a2f38a25083b1942abb67`
- six-pass extension: `35a137ed194d7c3cb01dea9892f295b898cf005f`
- real-player evidence study: `cd94fafa28e33864160e4474930c82b9f3643315`

## Principle

The existing replay, correctness, provenance, EngineBridge, Arena, Strength infrastructure, Battle Sidebar and telemetry are operational foundations. Do not rebuild them without a falsifiable gap.

```text
foundations
  ↓
calibrate measurement
  ↓
make evidence-backed claims
  ↓
optimise
```

## Six-pass AI roadmap

### Pass 1 — Re-anchor

Treat existing correctness/replay/telemetry/Strength infrastructure as foundations, not new milestones.

### Pass 2 — Strength calibration

Required ladder:

```text
A/A
↓
A vs deliberately weaker A
↓
A vs independently justified stronger/improved A
↓
independent real A/B candidate
```

A/A must behave approximately neutrally before trusting directional strength claims.

### Pass 3 — Experimental units

Preserve grouping identifiers and analyse at the true experimental-unit level. Keep colour/opening/seed/pair structure explicit. Report valid, invalid and unfinished games separately.

### Pass 4 — Uncertainty + SPRT calibration

Validate empirical coverage and operating characteristics under A/A, known positive/negative effects, draw rates, colour/opening imbalance, dependence and invalid-game rates. Do not enable automatic promotion yet.

### Pass 5 — Contextual balance

Analyse strength by hero × opponent × roster × side × scenario/opening × budget × mechanic/state family. Treat balance changes as controlled interventions and preserve human evidence as a separate evidence class.

### Pass 6 — Search / NNUE

Only after strength measurement is calibrated:

```text
RPG move ordering
→ selective search
→ stable classical baseline
→ NNUE parity/data/strength
→ population/QD/PSRO only when diversity evidence justifies it
```

## Current RedWar status

```text
Battle Sidebar                     ✅
visual validation tooling          ✅ foundation / QA continues
Bridge hardening                   ✅
stateful differential correctness  ✅
replay + provenance                ✅
telemetry schema/store/runtime     ✅
manual-play telemetry              ✅
Strength baseline                  ✅
SPRT implementation                ✅ isolated only

NEXT AI GATE                      → Strength calibration
```

## Parallel product track

- Battle UI responsive/focus/golden-scene validation.
- Replay ↔ telemetry completeness and missingness audit.
- Replay inspection/export.
- Real-player evidence collection when enough sessions exist.
- Web/multiplayer may advance independently.

## Promotion rule

```text
benchmark success ≠ global strength gain
CI green ≠ scientific proof
synthetic games ≠ human behaviour
nominal uncertainty ≠ calibrated confidence
SPRT implementation ≠ validated promotion gate
```

A `CONTINUE` result is a valid outcome when evidence is insufficient.
