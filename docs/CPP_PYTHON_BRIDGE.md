# Python ↔ C++ Ares bridge

## Purpose

RedWar currently has a Python rules/UI layer and a C++ Ares hot path. This document defines the stable boundary between them so the transport can change without changing callers or game semantics.

The current implementation is a subprocess adapter. The intended long-term implementation is an in-process C++ binding. The two implementations must satisfy the same caller-facing contract.

## Contract

The Python side may rely on four capabilities:

1. `ensure_running()` — establish an engine instance that can accept commands.
2. `send_command(command)` — send one complete engine command.
3. `read_response()` — receive one complete response line.
4. `close()` — release engine resources.

`CppEngineBot` owns game-facing interpretation. The bridge owns process/transport lifecycle. This separation is intentional: protocol transport must not decide what constitutes a legal RedWar action.

## Current protocol

The compatibility adapter currently maps to the Ares CLI:

```text
position rwen <complete battle state>
go nodes <N>
    → bestmove <action>

position rwen <complete battle state>
go infinite
    → bestmove <action> after stop
```

The engine also exposes `isready`, `stop`, `eval`, `eval classical`, and NNUE diagnostics through the same transport.

RWEN is the existing battle-state serialization contract. Under the current local mode, the complete battle state is public and can be supplied to Ares. A future hidden-information mode must define a separate observation boundary before exposing any bridge API to it.

## Migration rule

A future in-process binding should implement `EngineBridge` without changing `CppEngineBot` callers. It should preserve:

- deterministic RWEN parsing/serialization;
- legal-action semantics;
- `S → make(M) → unmake(M) → S` reversibility;
- explicit terminal `bestmove 0000` handling;
- search cancellation semantics;
- error visibility rather than converting transport failures into legal moves.

The subprocess implementation remains the compatibility oracle until the in-process implementation has equivalent differential coverage.

## Non-goals of this first migration step

This change does **not** move BoardState into C++, introduce a pybind11 module, rewrite the Python game state, or change Ares search/evaluation. Those are separate migrations that require differential and property-based evidence.
