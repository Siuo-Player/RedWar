# Protected Ares hold-out CI

The protected hold-out is a validation experiment, not a promotion gate.

Use `workflow_dispatch` with `holdout=true` on `main` to compare the requested Ares revision against the selected baseline on `data/validation/ARES_HOLDOUT_V1.json`.

The run must publish:

- hold-out set id;
- canonical SHA-256 of the manifest;
- seed/opening identity for every case;
- challenger colour;
- result and plies;
- raw JSON summary as an artifact.

The normal A/B Arena promotion path is unchanged. Hold-out results must not be copied into development or regression sets as a consequence of the result.