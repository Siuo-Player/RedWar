# Issue #318 — Next Implementation Boundary — 2026-09-09

The completed architecture audit identifies six duplicated design-parameter candidates. The first safe repeated vocabulary is canonical spell metadata: specialized Python spell generators currently repeat spell names that already exist in each hero's `spells` declaration.

The next implementation slice is intentionally narrower than a new spell DSL: consume the existing canonical `spells` declaration for `FrostMage`, `Pyromancer`, `Cleric`, `Trickster`, and `Geomancer`, add regression protection, and only then consider geometric metadata. Unique transition semantics remain specialized.

No balance, strength, or search-performance claim follows from this boundary.
