# Decision — live replay and rejected-input observability

**Date:** 2026-08-28  
**Status:** In implementation

Real local games must produce inspectable replay evidence. Accepted actions are canonical sequence evidence; rejected player inputs are diagnostic telemetry and must never alter game state.

For the manual-test loop, preserve at least source/target coordinates, requested action when known, outcome, and rejection reason. Search simulations must remain excluded from player replay evidence.
