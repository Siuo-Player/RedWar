# Strength calibration Run A — evidence recovery

**Status:** recovered provenance summary; raw observation remains in GitHub Actions artifact

## Evidence

The original Run A workflow completed its 100-game Arena experiment successfully. The preserved artifact is `9673256631` from workflow run `33139108032`, with digest `sha256:2e8e0aeb7b7bfd43a12311a0fc6a1dd62ad77dbf1d1fb6397d6c2d1ffe2ec8be`.

The raw JSONL extracted from that artifact has SHA-256 `5d9667f0ea532e17fe2b777d17dc79dcd2d60519023d67ef87842a26bf7982da` and contains 100 records / 50 complete colour-inverted pairs / 0 invalid records / 0 draws.

## Frozen provenance

- experiment: `strength-calibration-2026-08-27-v3`
- run: `strength-calibration-2026-08-27-control-replication`
- engine/rules: `81d018d3dd9d509e6ed1e4ba801adfab0d6fe5ef`
- seed policy: `control-seed-set-a`
- population: `ares-dev-population-v1`
- node budget: `10000`
- workflow head: `bf6e9a209a0f4ed1ee7754474d5f20d0f8e56e4a`

## Result

The control produced 50 challenger wins and 50 baseline wins. The descriptive Elo-equivalent delta is approximately `-0.3132`; the existing `±755.08` value is explicitly an engineering uncertainty proxy, not a calibrated confidence interval.

## Recovery boundary

The raw JSONL remains preserved in the original Actions artifact and was not edited or rewritten. This repository commit persists the provenance and validated summary so conversation history is not the only record of the experiment.

The summary is not a promotion result and has `promotion_authority=false`.
