# Decision — 1.0-Lite Ares baseline selection boundary

## Status

**Selection not yet frozen.** This decision records what is and is not eligible to become the 1.0-Lite Balance Baseline.

## Repository evidence

The player-facing C++ Ares profiles currently exposed by `ai/bot.py` are 100k, 500k and 1M nodes. Separately, `ai/BENCHMARK_SCENARIO.md` defines a 150k-node performance/correctness benchmark. These are different concerns and must not be conflated.

`tools/analytics/trainer.py` is also not a baseline source. Its training telemetry deliberately selects controllers from a mixed pool containing `BotAleatorio`, 1k, 5k and 10k-node training bots, and it generates random drafts from the current catalogue. Those choices are useful for broad diagnostics/training telemetry, but they do not define one fixed Ares policy, one fixed skill context, or one controlled draft population suitable for Lite balance evidence.

The scheduled `auto_balancer.yml` workflow still runs this trainer and then invokes `auto_pricer.py` in `--no-write` mode. Both remain diagnostic/telemetry infrastructure, not balance authority.

## Consequence

The 1.0-Lite Balance Baseline must be selected separately from:

- player-facing difficulty defaults;
- the 150k performance benchmark;
- mixed training telemetry;
- `auto_pricer.py` output;
- the competitive Ares promotion track in #372.

No hero/economy tuning should be treated as baseline-backed evidence until one exact Ares profile/policy, deterministic seed protocol, controlled population/draft definition and provenance-valid record contract are explicitly frozen.

## Next phase

Create a controlled baseline-selection experiment whose purpose is **instrument reliability and reproducibility**, not hero ranking or automatic balancing. The experiment should compare candidate fixed Ares profiles under the same engine/ruleset, matched conditions, colour symmetry and bounded game/turn limits, recording complete provenance and invalid/hang diagnostics.

The result selects a reproducible execution policy for Lite. It does not claim that the selected policy is the strongest Ares and does not itself authorize balance changes.
