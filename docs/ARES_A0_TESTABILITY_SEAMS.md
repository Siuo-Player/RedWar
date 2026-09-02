# Ares A0 — Testability Seams

Status: `PARTIAL`

This document records the upstream seams required to run A0 correctness/evaluation-validity experiments without relying on hidden engine state.

## S1 — Transposition-table control

The C++ protocol exposes:

```text
setoption name UseTT value true
setoption name UseTT value false
clearhash
```

`UseTT=false` disables TT persistence by preventing search writes while the table is cleared when the option is disabled. `clearhash` replaces the table with fresh entries. This allows the harness to distinguish:

```text
TT OFF
TT ON + clearhash
TT ON + warm TT
```

This seam does not claim that the three modes are semantically equivalent; it only makes them independently controllable.

## S2 — Pure finite node budget

The protocol contract for:

```text
go nodes N
```

sets the search time limit to infinity. The engine therefore cannot terminate a node-bounded search because of wall-clock timeout.

Before `bestmove`, the engine emits:

```text
info string search nodes=<actual> node_limit=<requested> node_bound_reached=<0|1> time_abort=0 terminal_no_move=<0|1> tt=<0|1>
```

This makes the requested budget, observed node count, node-bound status, and TT mode directly inspectable.

The A0 harness must still reject cells where `actual_nodes > requested_nodes` or where the process/protocol fails.

## S3 — Canonical state read-back

The protocol exposes:

```text
state canonical
```

which returns:

```text
state rwen <canonical RWEN>
state hash <BoardState hash>
```

The RWEN is serialized from the live C++ `BoardState`, including pieces, effects, side to move and TWC. Permanent lifespans use the canonical `N` representation.

The returned numeric hash is the engine's existing board hash; it is not a SHA-256 digest and must not be treated as one.

## A0 interpretation

These seams enable the following experiment chain:

```text
C1 TT ON/OFF equivalence
C2 node-bounded determinism
C3 independent legal-action oracle
C4 evaluator differential
C5 lifecycle/opening-state integrity
```

A passing seam test or green CI does **not** imply `A0 = PASS`. A0 remains `OPEN`, `BLOCKED`, `PARTIAL`, or `PASS` according to the evidence produced by the actual experiments.

## Provenance

Implemented on the RedWar `main` base at the time of PR creation on 2026-09-02. The implementation PR is separate from the exact A/A-B diagnostic fixture PR so diagnostic evidence cannot be confused with the production experiment harness.
