# RedWar — Hero Data-Driven Audit — 2026-09-09

## Scope

This audit addresses Issue #318 using the existing hero, mechanics, balance-feature and engineering methodology contracts. It is a **design/data architecture audit**, not a balance verdict and not a strength evaluation.

The audit is anchored to:

- `engine/heroes_config.json` — canonical hero data source;
- `engine/HEROES_SCHEMA.md` — configuration vocabulary and data-vs-logic boundary;
- `engine/pieces.py` — Python consumer/compiler and specialized hero algorithms;
- `ai/cpp_engine/movegen.cpp` — C++ configuration consumer;
- `docs/HERO_SYSTEM.md` and `docs/MECHANICS_TRACEABILITY_MATRIX.md` — integration and evidence contracts;
- `docs/BALANCE_FEATURE_SCHEMA.md` — design/gameplay vector contract.

## Baseline identities

| Source | Identity |
|---|---|
| `engine/heroes_config.json` | `5c0b42d9661afc0493b76a4709845c91435063f2` |
| `engine/pieces.py` | `77656f607ba57399fa82fe0c6e1f1c18f5b12c78` |
| `main` | `7b6b9ae60e74a67e18851dfc3c94888829f0012f` |

## Architecture finding

The intended architecture is already substantially data-driven for **common geometry and metadata**. `DataPiece` loads canonical cost/acronym/description/passive/draftability/lifespan/cooldown and compiles movement/attack behavior from the configuration. The same configuration is also consumed by the C++ engine and analysis/model tooling.

The remaining hybrid boundary is concentrated around mechanics whose **state transition semantics** are not expressible by the current schema. Examples are area spell resolution, purification of a stunned ally, swapping, barricade creation, jump semantics, aura disablement, spawn validation and event-triggered passives.

This is not, by itself, an architectural defect: the schema explicitly permits specialized logic for mechanics that are unique or not sufficiently represented by the DSL.

## Hero inventory

### `DATA_DRIVEN_OK`

`Bone`, `Ghoul`, `Obelisk`, `Phantom`, `Sentry`, `Ranger`, `Nightshade`, `StoneWall`.

These heroes use the generic `DataPiece` path for their represented movement/attack behavior, with applicable common parameters coming from configuration. No hero-specific Python override was observed for their active geometry path.

### `SPECIALIZED_ALGORITHM_JUSTIFIED`

`Lich`, `BoneLord`, `Templar`, `Berserker`, `Inquisitor`.

Their distinctive mechanics are event/state dependent. The configuration already declares the relevant design data, while executable resolution remains specialized. Examples include lifecycle-aware spawning, on-kill creation, redirect/reflection, area damage and aura semantics.

### `HARDCODED_DESIGN_PARAMETER` + specialized algorithm

`FrostMage`, `Pyromancer`, `Dragoon`, `Cleric`, `Trickster`, `Geomancer`.

These are the clearest data-driven debt candidates because `engine/pieces.py` contains specialized implementations that also hardcode design-level details that could plausibly be represented by an extended schema:

| Hero | Duplicated / hardcoded detail | Why not refactor immediately |
|---|---|---|
| FrostMage | Nevada range/shape and spell name | Needs a generic area-spell vocabulary that preserves selectable focus and center effect semantics. |
| Pyromancer | Ignite scan radius and spell name | Needs a generic effect-footprint/range contract tied to actual spell resolution. |
| Dragoon | Direction set and jump midpoint semantics | Jump is a movement+state rule, not just a numeric parameter. |
| Cleric | Purify radius and spell name | Requires state-conditioned ally targeting semantics. |
| Trickster | Swap radius and spell name | Requires target relation and state-transition semantics. |
| Geomancer | Eight-neighbour barricade geometry and spell name | Requires declarative board-alteration semantics, not only target geometry. |

These should become refactoring targets only after the common vocabulary is proven and regression coverage exists.

## Consumer map

| Layer | Consumer | Role |
|---|---|---|
| Configuration | `engine/heroes_config.json` | canonical design data |
| Python rules | `engine/pieces.py` | validation + behavior compilation + specialized semantics |
| C++ rules | `ai/cpp_engine/movegen.cpp` | native configuration-driven move generation |
| UI | `ui/hero_encyclopedia_panel.py`, `tools/replay/interaction.py` | selected-hero information/encyclopedia context |
| Analysis | `tools/balance/auto_pricer.py` | cost/roster diagnostics |
| NNUE tooling | `tools/nnue/features.py`, `tools/nnue/bootstrap_model.py` | stable hero identity/cost features |

The audit did **not** find evidence that ordinary hero identity/cost/geometry should be duplicated independently for each consumer. The more important current issue is that some specialized Python mechanics repeat design parameters that exist only partially in configuration.

## Classification rules applied

- `DATA_DRIVEN_OK`: represented by canonical configuration and consumed through the generic behavior path, with no unjustified hero-specific design duplication observed.
- `SPECIALIZED_ALGORITHM_JUSTIFIED`: configuration carries design metadata, but unique state-transition semantics remain procedural and should not be forced into JSON merely for uniformity.
- `HARDCODED_DESIGN_PARAMETER`: a specialized implementation contains a design parameter that is plausibly reusable/configurable and is duplicated outside the canonical data source.
- `ANALYSIS_GAP`: evidence needed for the next analysis layer does not yet exist in this audit, rather than being treated as zero capability.

## What is proven vs not proven

### Established by this audit

- `engine/heroes_config.json` is the canonical source for hero data.
- Common movement/attack geometry is compiled through `DataPiece`.
- The architecture deliberately permits specialized algorithms for unsupported unique mechanics.
- There are concrete duplicated design parameters in six specialized hero implementations.
- The repository already has a compatible design-vector schema and provenance contract.

### Not established

- Universal semantic equivalence of Python and C++ for every hero/state.
- Complete gameplay-vector measurements for every draftable hero.
- Balance, strength, fairness or draft-cost correctness.
- That every identified hardcoded parameter should be moved to JSON.

## Next implementation boundary

The safest next engineering increment is **not** a mass rewrite. It is one generic, repeated vocabulary extension at a time, chosen from the duplicated parameters above, with:

1. schema update;
2. Python consumer update;
3. C++ parity check where the field affects native behavior;
4. targeted regression tests;
5. traceability update;
6. only then reuse by additional heroes.

A separate gameplay-vector artifact should be produced only when a valid, versioned state-sampling protocol is available. The current JSON inventory therefore remains deliberately limited to design architecture evidence.

## Machine-readable companion

See [`data/analysis/hero_data_driven_audit_2026-09-09.json`](../data/analysis/hero_data_driven_audit_2026-09-09.json).
