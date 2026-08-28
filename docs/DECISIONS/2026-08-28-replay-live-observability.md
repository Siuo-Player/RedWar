# Decision — live replay and manual-test observability

**Date:** 2026-08-28  
**Status:** Implemented

Completed local games now persist a canonical replay automatically. The first real action captures the battle-start state; search/simulation actions are excluded. Completion writes the replay to the local append-only archive.

Engine-level accepted/rejected action attempts are persisted separately as diagnostics so later analysis can distinguish canonical moves from rejected inputs. These diagnostics are evidence about the interaction with the rules, not part of the canonical game sequence.

Local replay data remains outside version control.
