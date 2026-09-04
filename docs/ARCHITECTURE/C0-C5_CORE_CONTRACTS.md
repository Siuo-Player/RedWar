# RedWar Core Contracts — C0–C5

**Status:** architectural baseline for implementation work  
**Date:** 2026-09-05  
**Scope:** Python core, independent oracle, native Ares move generation/transition, bridge and serialized state

This document defines what each correctness layer is responsible for, which implementation is authoritative today, and which boundaries must become explicit before large product/search expansion.

It is intentionally a contract document, not a rewrite plan. Existing behaviour remains authoritative unless a later decision explicitly changes it.

## 1. Layer model

```text
C0 State identity
    ↓
C1 Action representation
    ↓
C2 Action validation + execution
    ↓
C3 Legal-action specification
    ↓
C4 State transition equivalence
    ↓
C5 Engine/bridge protocol
```

The dependency direction is one-way in principle. Higher layers may consume lower-layer contracts; lower layers must not depend on UI, Arena, strength tooling, or statistical conclusions.

## 2. C0 — canonical state

### Authoritative implementation today

`engine.game_state.GameState` currently owns the complete Python game state used by the product and most tooling:

- board and pieces;
- tile effects;
- side to move;
- terminal state and winner;
- turn-without-capture counter (TWC);
- move log and last move;
- clocks;
- derived hash and hash validity;
- current evaluation score.

`engine/heroes_config.json` is the canonical hero-definition input. `engine/pieces.py` compiles the declarative movement/attack portion into Python behaviour.

### Identity rule

The current state identity must include every field that can change legal future behaviour or serialized/search identity. The Zobrist implementation currently includes:

- piece position, team and name;
- stun timer;
- lifespan;
- spawn cooldown;
- tile effect type/team/timer;
- side to move;
- TWC.

The current hash is therefore a derived identity, not an independent source of truth.

### Contract

A C0 state is valid only when its board/effect objects, lifecycle fields, turn information and derived hash describe the same logical position. Any state mutation must either maintain the hash incrementally or invalidate it so it can be recomputed safely.

### Known architectural debt

`to_rwen()` compatibility is installed dynamically from `engine/__init__.py`. This preserves the existing protocol but hides an important serialization contract behind import-time mutation. Future work should make the state serializer explicit and versioned without changing current RWEN semantics first.

## 3. C1 — canonical action

### Current representation

`engine.actions.GameAction` is the canonical typed action representation for the core. It captures the action type, origin/destination coordinates and action-specific payloads (`area`, `spawn_name`, `spell_name`).

Legacy dictionaries remain supported at compatibility boundaries, for example:

```python
{
    "type": "move",
    "start": (6, 0),
    "end": (5, 0),
}
```

`engine.actions.normalize_action()` converts a legacy mapping to `GameAction` and leaves an existing `GameAction` unchanged. This allows producers to migrate independently without changing gameplay semantics.

### Boundary status

`GameState.execute_action()` accepts both canonical `GameAction` values and legacy mappings. The canonical path is already exercised by analysis search, the stateful sequence model, and the manual battle interaction execution seam. UI/manual producers and other compatibility-facing code may still construct dictionaries deliberately.

The migration rule is therefore:

```text
legacy producer
      ↓
normalize_action()
      ↓
GameAction
      ↓
GameState.execute_action()
      ↓
make_action() transition authority
```

New consumers should prefer `GameAction` at execution boundaries. Legacy dictionaries should remain only where an existing public/compatibility contract still requires them.

### Contract

Every action crossing an engine execution boundary should have one canonical representation with:

- normalized action type;
- two integer board coordinates for origin and target;
- action-specific payload only when required;
- deterministic serialization to/from the Ares protocol where applicable;
- no UI-specific objects.

### Non-goal

Do not encode game rules inside the action object. An action describes intent; the rules/state layer determines whether that intent is legal and how it changes the state.

## 4. C2 — validation and execution

### Current authority

`GameState.make_action()` is the current authoritative Python state transition. It handles movement, attacks, stuns, spawns, spells, TWC, timers, terminal detection and incremental hash updates.

`GameState.execute_action()` is a convenience boundary that normalizes/accepts the canonical action representation and forwards the resulting fields into `make_action()`.

### Important distinction

There are two different questions:

1. **Is this action legal in this state?**
2. **Given this accepted action, what is the resulting state?**

These must remain separately testable even while the implementation remains concentrated in `GameState`.

### Current transition invariants

A successful real action currently performs the following lifecycle in one authoritative path:

```text
validate coordinates/source
→ apply action semantics
→ update TWC
→ flip side to move
→ advance timers/effects
→ recompute terminal status
→ invalidate/reset derived score as required
```

Simulation calls are explicitly supported through `is_simulation` and must not create real-game replay side effects.

### Required future guardrails

Before extracting `GameState` into multiple classes, add deterministic tests that assert for representative actions:

- pre-state is unchanged when a clone is executed;
- post-state RWEN is canonical;
- post-state hash equals the hash of the reconstructed state;
- TWC follows the documented permanent-vs-temporary capture rule;
- lifecycle timers/effects advance exactly once;
- terminal state is identical across implementations;
- replay capture is absent from simulation paths.

## 5. C3 — legal-action contract

### Independent specification

`tools/analytics/legal_action_oracle.py` is deliberately independent from the concrete piece legality helpers and is therefore the specification-side comparator for legal actions.

It must not call:

- `Piece.get_valid_moves()`;
- `Piece.get_valid_attacks()`;
- `Piece.get_valid_spells()`;
- native Ares move generation.

### Native implementation

`ai/cpp_engine/movegen.cpp` is the native implementation under comparison.

The deterministic campaign includes FrostMage/Nevada after confirming that the independent oracle and native generator describe the same legal target envelope for that action class.

### Evidence boundary

C3 agreement means **legal-action agreement only**. It does not prove:

- post-action state equivalence;
- make/unmake equivalence;
- search equivalence;
- evaluation equivalence;
- strength equivalence.

Any test/report that claims more must name the stronger layer explicitly.

## 6. C4 — semantic transition equivalence

The repository already contains meaningful C4 evidence, including Python/C++ make-unmake fixtures and persistent sequence checks.

### Required semantic comparison

For a common initial state and a canonical action sequence, the two implementations must be compared at each step on observable state identity:

```text
state before
  ↓ action
state after
  ├─ serialized state
  ├─ state hash / identity
  ├─ side to move
  ├─ TWC
  ├─ lifecycle fields
  ├─ effects
  └─ terminal status
```

Where a native undo operation exists, the sequence must additionally satisfy:

```text
make(action)
→ undo
→ exact root-state restoration
```

### Priority order

New C4 tests should favour transitions that exercise lifecycle and derived state, not merely ordinary board movement. Particularly important classes are:

- temporary-piece capture;
- permanent-piece capture and TWC reset;
- stun → death progression;
- timed effects;
- special spells;
- spawn/cooldown lifecycle;
- jump/swap/barricade-style state changes;
- terminal transitions;
- hash-sensitive mutations.

## 7. C5 — Ares bridge/protocol

### Current boundary

`ai/engine_bridge.py` already provides a dedicated subprocess transport abstraction with explicit lifecycle states and failure classes.

`ai/bot.py` is responsible for turning Python game state into an Ares request and converting the returned action text into the product's action representation.

### Current protocol surface

At minimum, the product currently relies on concepts including:

- `isready`;
- `position rwen ...`;
- `go nodes N`;
- `go infinite`;
- `stop`;
- `bestmove`;
- `info`;
- `clearhash`;
- diagnostic handling for `bestmove 0000`.

### Contract target

The Ares protocol should become a standalone, versioned interface specifying:

```text
protocol version
state/RWEN version
action format
search-limit semantics
feature flags (e.g. TT observability)
normal response semantics
terminal-position semantics
error/diagnostic semantics
```

Compatibility behaviour such as Python-side FrostMage `STUN → SPELL nevada` normalization must be documented as a temporary adapter rule with a clear removal criterion, not treated as an undocumented engine feature.

## 8. Current architecture and intended direction

The current implementation is not yet cleanly decomposed into separate modules for every layer. That is acceptable. The immediate goal is to make the contracts explicit before moving code.

```text
                    ┌─────────────────────────┐
                    │      GameState (C0)      │
                    │ state + derived identity │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Action boundary (C1)  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ Validation / transition │
                    │      authority (C2)     │
                    └───────┬─────────┬───────┘
                            │         │
                 ┌──────────▼─┐   ┌──▼──────────┐
                 │ Oracle C3  │   │ Native C3   │
                 └──────┬─────┘   └─────┬───────┘
                        │               │
                        └──────┬────────┘
                               ▼
                    ┌──────────────────────┐
                    │ C4 transition checks │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │ Ares protocol / C5   │
                    └──────────────────────┘
```

The UI, replay system and Arena consume these contracts. They should not become alternate rule authorities.

## 9. Implementation sequence

### Step C1.1 — action boundary — substantially complete

The canonical `GameAction` value object and `normalize_action()` adapter are now present. `GameState.execute_action()` accepts the typed representation while preserving legacy mappings for compatibility. Analysis search, stateful sequence execution, and manual interaction execution already normalize before crossing the engine execution boundary.

The remaining C1 work is incremental migration of additional consumers where the compatibility contract is not public or protocol-facing. Do not force a repository-wide producer rewrite merely to remove every dictionary literal.

### Step C4.1 — deterministic post-state contract

Extend existing cross-backend sequence tests with explicit per-step assertions for serialized state and derived identity. Reuse existing make/unmake infrastructure instead of building a parallel harness.

### Step C0.1 — explicit serializer

Move RWEN compatibility from import-time monkey-patching towards an explicit serializer API, preserving exact current text format and adding a serializer version for future evolution.

### Step C5.1 — protocol specification

Document the current Ares wire contract, then add machine-checkable version/feature negotiation only when a concrete compatibility need exists.

### Later extraction

Only after these contracts are stable should larger refactors split `GameState` into board/effects/turn/lifecycle components or reduce `main.py` responsibilities. Refactoring first would multiply the number of moving pieces while the semantics are still being proved.

## 10. What must remain unchanged unless explicitly decided

- Independent oracle remains independent.
- C3 legal-action evidence is not presented as strength evidence.
- TWC permanent-vs-temporary semantics remain as currently documented.
- Simulation paths do not become real replay records.
- RWEN remains canonical for current Ares bridge consumers until a versioned replacement exists.
- Search/NNUE optimization does not redefine game rules.
- Product/UI code must not become a second game-rule authority.

## 11. Exit criteria for the C0-C5 stabilization phase

The phase can be considered complete when repository documentation and tests make all of the following unambiguous:

1. what constitutes a canonical state;
2. what constitutes a canonical action;
3. where action legality is decided;
4. where action execution is decided;
5. how Python and native implementations are compared;
6. which fields must match after transitions;
7. how serialization and hashing identify a state;
8. which protocol guarantees the bridge provides;
9. which evidence supports correctness versus search/strength claims.

Only then should the roadmap prioritize deeper Ares/NNUE optimization or major product expansion.
