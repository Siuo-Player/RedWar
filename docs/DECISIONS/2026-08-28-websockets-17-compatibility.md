# Decision — websockets 17 compatibility

**Date:** 2026-08-28  
**Scope:** Python runtime dependency used by `online/server/app.py` and `online/network/client.py`  
**Status:** validation in dedicated PR

## Change

Upgrade `websockets` from 12.0 to 17.0.1.

## Compatibility check

The current server uses `websockets.serve()` with a single connection handler and the client uses `websockets.connect()`, asynchronous iteration and `send()`. A regression test now starts the real server on a loopback ephemeral port and validates the setup handshake through a real `websockets` client.

The existing connection-closed exception handling remains under the `websockets.exceptions` namespace used by the implementation.

## Boundary

No protocol messages, game rules, action semantics or server authority are changed. The test validates the existing protocol against the upgraded dependency rather than introducing a second protocol implementation.
