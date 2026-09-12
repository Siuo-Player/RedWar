# Historical Arena rating — real-evidence validation

**Issue:** #488  
**Status:** descriptive validation only; not promotion evidence

## Input

The current committed real Arena Strength dataset was inspected:

- `data/arena/strength/2026-08-27-control-100.json`
- schema: `redwar-strength-dataset-v1`
- evidence class: `real_arena`
- raw SHA-256: `19738166542806738c72468e2b10ba87f1dd8762603caa28638f4aa5ea0d98bf`
- workflow run: `33027350530`
- artifact: `9628952365`
- rules version: `37b94d51b810b7ef698139f896afd30eee50fa5a`
- node budget: `10000`
- 100 valid games / 50 complete colour-inverted pairs
- challenger wins: 50
- baseline wins: 50
- draws: 0
- invalid games: 0
- opening count: 16
- colour policy: alternating per game
- pairing policy: same opening per pair with inverted challenger colour

Source dataset canonical SHA-256:
`bc396752a0791437d487f4aaa5dde57721a6db99930789228f951447a2cbd165`

## Historical-rating fit

For this evidence slice, the baseline version
`37b94d51b810b7ef698139f896afd30eee50fa5a` was used as the temporary zero-Elo
anchor, and the challenger version
`f6a1ee4beb160ee4e23e7e044fba0f78aa5961ac` was fitted against it.

The regularized Bradley–Terry model from
`tools/analytics/historical_rating_calibration.py` gives:

| Version | Internal Elo | Approx. 1-sigma SE |
|---|---:|---:|
| `37b94d51b810b7ef698139f896afd30eee50fa5a` | 0.0 | 0.0 (fixed anchor) |
| `f6a1ee4beb160ee4e23e7e044fba0f78aa5961ac` | 0.0 | 34.7 |

The zero point is therefore not evidence of equal playing strength in a
human-calibrated sense. It is simply the result of a 50/50 real Arena result
under the internal identification constraint.

## Graph/coverage finding

The committed real Strength datasets currently expose only one compatible
challenger-vs-baseline comparison edge for this schema. Consequently there is
not yet a multi-version connected historical comparison graph from which a
meaningful global historical rating scale can be estimated.

The global model therefore passes the important real-data integration checks:

- real evidence is consumable;
- provenance metadata is retained;
- the result is finite;
- no artificial draw outcome is introduced;
- the promotion gate is not invoked;
- no disconnected component is manufactured through the regularization prior.

But the historical rating product is **not yet empirically calibrated as a
multi-version scale**. More compatible real Arena comparisons between
versions are required.

## Interpretation

This artifact validates pipeline compatibility, not Ares product strength.
It does not prove that either version is strong enough for #372, and it does
not justify promoting, rejecting, or replacing an Ares champion.
