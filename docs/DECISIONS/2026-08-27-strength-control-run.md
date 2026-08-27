# Strength control run — 100 games

**Purpose:** validate the current Arena Strength schema, paired-game structure, validity/termination provenance, contextual metadata and raw artifact retention without changing Ares search/evaluation.

This branch intentionally contains no AI change. The challenger commit differs from `origin/main` only by this documentation marker, so any measured delta is treated as a control/no-change experiment rather than evidence of a strength improvement.

Expected experiment configuration from `ai_strength_experiment.yml`: 100 games, 10,000 nodes per move, paired fixed openings, inverted colors, explicit Strength population context, current raw JSONL and summary artifacts retained for 30 days.

Promotion remains disabled for this run.
