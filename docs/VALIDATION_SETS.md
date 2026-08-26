# RedWar — Validation Set Policy

RedWar separates evidence into three non-substitutable classes:

| Set | Purpose | Protected |
|---|---|---|
| Regression | Cases that must not regress | No |
| Development | Cases used to guide an engineering hypothesis | No |
| Hold-out | Frozen cases opened only for validation | **Yes** |

The protected hold-out is stored in `data/validation/ARES_HOLDOUT_V1.json`. Its canonical SHA-256 and case count must be recorded whenever an experiment consumes it.

## Rules

1. A development change may be informed by regression and development evidence.
2. A development change must not be tuned against the protected hold-out.
3. Hold-out results are validation evidence, not development evidence.
4. Regression, development and hold-out results must remain separately labelled in reports.
5. The hold-out manifest is immutable for an experiment once its canonical SHA-256 has been recorded.

This policy exists to prevent benchmark overfitting and to keep strength claims reproducible.
