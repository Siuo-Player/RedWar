# Strength calibration Run A — execution trigger

This commit is an operational trigger for the predeclared Strength calibration control.

The execution workflow resolves the exact run from:

`data/arena/strength/plans/2026-08-27-replication-v3.json`

Run:

`strength-calibration-2026-08-27-control-replication`

No experimental parameters are declared or modified by this marker. The workflow remains responsible for resolving the frozen engine/rules SHA, seed set, node budget, paired-colour policy, validity/termination policy and `promotion_authority=false` before execution.
