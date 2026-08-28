# Python ↔ C++ Ares bridge

## Purpose

RedWar has a Python rules/UI layer and a C++ Ares hot path. This document defines the stable boundary between them so the transport can change without changing callers or game semantics.

The current implementation remains a subprocess adapter. The intended long-term option is an in-process C++ binding, but it must preserve the same caller-facing semantics and must first beat the subprocess baseline on evidence, not assumption.

## Contract

The Python side may rely on four capabilities:

1. `ensure_running()` — establish an engine instance that can accept commands.
2. `send_command(command)` — send one complete engine command.
3. `read_response(timeout=None)` — receive one complete response line within a bounded wait.
4. `close()` — release engine resources.

The subprocess implementation also exposes an explicit `restart()` recovery primitive. Restart is never implicit after a failed request.

`CppEngineBot` owns game-facing interpretation. The bridge owns process/transport lifecycle. This separation is intentional: transport code must not decide what constitutes a legal RedWar action.

## Lifecycle

The subprocess adapter exposes:

```text
NEW → RUNNING → CLOSED
          └→ FAILED
```

`FAILED` is sticky until an explicit `restart()`. A read after process failure cannot silently create a new process.

## Failure classes

At minimum:

```text
EngineBridgeTimeout
EngineBridgeProcessExit
EngineBridgeProtocolError
EngineBridgeError
```

A bridge failure must never become:

```text
legal move
zero evaluation
normal terminal result
```

## Request provenance

Every sent command receives a monotonic local `request_id` and is retained as a `BridgeRequest` containing:

```text
request_id
command
send timestamp
state identity when the command carries RWEN
```

RWEN state identity is represented by SHA-256 of the canonical payload. This is local provenance; it does not alter the Ares wire protocol.

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

`stdout` is reserved for protocol responses. `stderr` is drained separately and retained as a bounded diagnostic tail so protocol output cannot be contaminated by diagnostics and diagnostics cannot block the engine.

## Timeout and recovery policy

`read_response()` has a 15-second default bound. A timeout changes lifecycle to `FAILED` and raises `EngineBridgeTimeout`.

Recovery is explicit:

```text
failure
→ inspect classified error/provenance
→ explicit restart when policy permits
```

The bridge never restarts itself merely because a response is absent.

`CLOSED` is terminal for that bridge object; it must not be restarted accidentally after normal shutdown.

## Migration rule

A future in-process binding should implement `EngineBridge` without changing `CppEngineBot` callers. It should preserve:

- deterministic RWEN parsing/serialization;
- legal-action semantics;
- `S → make(M) → unmake(M) → S` reversibility;
- explicit terminal `bestmove 0000` handling;
- search cancellation semantics;
- error visibility rather than converting transport failures into legal moves;
- equivalent request/result provenance where meaningful.

The subprocess implementation remains the compatibility oracle until an in-process implementation has equivalent differential coverage and measurable product benefit.

## Non-goals of the hardening step

This change does **not** move BoardState into C++, introduce a pybind11 module, rewrite Python game state, or change Ares search/evaluation. Those remain separate migrations requiring differential/property evidence and independent strength/performance validation.
