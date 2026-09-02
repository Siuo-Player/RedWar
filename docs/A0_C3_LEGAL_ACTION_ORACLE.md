# A0 C3 — Independent Legal-Action Oracle

## Status

Design gate. No promotion claim is attached to this document.

## Objective

Provide an independent reference for legal-action validation so that Python/C++ differential tests are not the only source of truth.

The oracle must be simpler than Ares, rule-explicit, deterministic and independently reviewable.

## Principles

- Do not reuse C++ move-generation functions inside the oracle.
- Do not call Ares search to decide whether an action is legal.
- Derive expected legality from the canonical RedWar rule model and small independently written predicates.
- Compare semantic actions, not implementation-specific ordering.
- Preserve action type, origin, target, spell/spawn identity and relevant area semantics.

## Required coverage

The first implementation must cover, at minimum:

```text
MOVE
ATTACK
STUN
SPELL
SPAWN
```

and the persistent state dimensions that can change legality:

```text
side to move
stun timer
lifespan
spawn cooldown
terrain/effect state
TWC where a rule depends on it
board occupancy
```

## Oracle contract

For an input canonical state `S`, produce a canonical set:

```text
O(S) = { semantic legal actions }
```

The implementation under test must produce:

```text
I(S)
```

The primary correctness criterion is:

```text
O(S) == I(S)
```

Ordering is ignored unless a separate move-ordering test explicitly asks for it.

## Independent invariants

The oracle suite must include hand-authored and metamorphic checks such as:

- every generated action has a legal origin containing a piece of the side to move;
- no generated action targets outside the board;
- MOVE cannot violate occupancy/path constraints for its movement geometry;
- ATTACK cannot target a friendly piece;
- a stunned piece cannot generate actions when the rules prohibit acting;
- a spell forbidden by an active Inquisitor aura is absent;
- spawn actions respect spawn availability and cooldown;
- action semantics survive colour/side symmetry transformations where the rules are symmetric;
- translating an isolated local pattern without changing relevant boundaries preserves the transformed action relation;
- `generate(S)` followed by make/unmake of each action restores `S` exactly;
- no action is duplicated semantically.

## Negative tests

The oracle must explicitly test illegal-but-plausible actions:

- blocked movement;
- occupied friendly destination;
- invalid attack geometry;
- spell outside range/pattern;
- spell while silenced;
- spawn while unavailable/cooldown-active;
- action from enemy piece;
- action from stunned piece;
- malformed or out-of-board coordinates.

## Differential campaign

Validation should combine:

1. a fixed hand-authored corpus covering each mechanic;
2. deterministic pseudo-random states;
3. metamorphic transformations;
4. states extracted from valid real replays;
5. minimized counterexamples when a mismatch occurs.

For every mismatch, store:

```text
canonical state identity
oracle action set
implementation action set
difference
rule/config identity
seed/source identity
first failing transformation, when applicable
```

## Acceptance gate

C3 is considered passed only when:

- the independent oracle is implemented;
- fixed mechanic corpus has zero unexplained mismatches;
- randomized campaign has zero unexplained mismatches;
- metamorphic checks pass;
- each mismatch has a reproducible minimized artifact or an explicitly accepted fixture exception;
- the oracle itself has tests that do not depend on the implementation under test.

A green CI run without oracle independence does not count as C3 evidence.
