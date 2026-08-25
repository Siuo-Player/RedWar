# Protected Ares hold-out CI

Run the GitHub Actions **RedWar AI Arena** workflow manually with `holdout=true` on `main` to execute protected Ares validation.

This mode is deliberately separate from the promotion Arena. It validates the frozen `ARES_HOLDOUT_V1` manifest, checks each opening-derived seed, alternates challenger colour, and publishes the hold-out identity and result summary as an artifact.

The normal promotion path remains unchanged. Hold-out cases and results must not be used to tune the current Ares revision or to redefine the protected manifest after observing a result.