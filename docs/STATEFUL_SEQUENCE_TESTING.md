# RedWar — Stateful Sequence Testing

This document defines the first state-aware property-testing layer after bridge hardening.

## Principle

Randomness chooses among actions that are legal in the current state; it does not invent arbitrary commands. The existing GameState remains authoritative for Python semantics, while the C++ differential suites remain the cross-implementation oracle.

## Guarantees

A generated sequence is:

- deterministic for a fixed seed and starting state;
- composed only of actions legal at the moment they are selected;
- replayable from the same root state;
- comparable through canonical RWEN state representations and state hashes.

## Failure evidence

Future differential adapters should retain at minimum:

```text
seed
starting RWEN
action prefix
first differing index
Python state
C++ state
bridge provenance
```

This layer intentionally does not reimplement Ares rules, scoring, or move generation semantics.
