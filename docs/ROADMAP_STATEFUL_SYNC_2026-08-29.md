# Roadmap synchronization — stateful testing — 2026-08-29

The latest PROJECT-STUDIES synthesis establishes the post-sidebar order as:

```text
sidebar + visual QA
→ bridge hardening
→ stateful/property/fuzz/recovery
→ replay/telemetry
→ strength calibration
→ RPG search / move ordering
→ NNUE
```

RedWar has now completed the bridge-hardening package. This PR begins the next package with a legality-aware, deterministic sequence generator and replay-state invariants.

It deliberately does not claim Python/C++ equivalence by itself; the existing C++ differential machinery remains the oracle for cross-implementation comparison.
