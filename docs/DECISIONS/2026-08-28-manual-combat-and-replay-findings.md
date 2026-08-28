# Manual combat and replay findings — 2026-08-28

## Evidence

A manual developer-UI game exposed three distinct classes of behavior that needed explicit treatment:

1. repeated Nevada selection could be caused by ambiguous UI interaction rather than deliberate player intent;
2. a game can terminate after 50 actions without a real-piece capture because the canonical rule is a no-capture material tiebreak;
3. zero-ply replay records are not useful representations of a played game and had appeared in developer replay output.

The same replay also showed a long run of Nevada actions, making it important not to infer FrostMage balance from that session until the UI intent ambiguity is removed.

## Capture semantics

A capture is counted for the no-capture counter when a **non-temporary** piece is removed. Temporary pieces such as `Bone`, `Ghoul`, and `StoneWall` have a finite `lifespan` and do not reset the counter when destroyed.

For stun-based combat, the first stun leaves a real target alive and stunned; the second stun removes the real target and therefore resets `turns_without_capture` to zero.

This is now covered by a deterministic regression test.

## Nevada boundary semantics

Nevada centers use Manhattan distance 3 and are clipped to the board. A FrostMage near an edge or corner must retain every legal in-board center; centers outside the board are simply not candidates.

The current Python and C++ generators already follow this geometry. A corner regression was added to protect the contract against future changes.

The FrostMage's own square is not a legal Nevada center.

## UI intent

A board destination is not necessarily a unique action. The manual UI must resolve all legal action interpretations for that destination instead of silently prioritizing movement or another action.

A friendly destination must first be checked for legal spell actions before the UI changes the selected friendly piece. Offensive spells aimed at an allied target require explicit confirmation; support spells retain their normal friendly-target semantics.

## Replay retention and cleanup

Canonical replay archives remain evidence and are not rewritten by developer cleanup.

The developer replay directory may contain stale/accidental zero-ply records. The DEV entrypoint now removes only those records automatically at startup. Schema-v2 developer UI sessions are preserved.

## Balance interpretation

The manual FrostMage session is useful diagnostic evidence but not a valid pricing experiment. UI-induced repeated Nevada choices confound player intent, so no cost change is justified from that session alone.

Further balance work should use controlled configurations and retained replay telemetry after the interaction contract is stable.
