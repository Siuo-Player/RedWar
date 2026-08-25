# Decision — batch strength estimator superseded by paired Arena methodology

## Date
2026-08-25

## Type
Decision / repository maintenance

## Discovery
PR #78 (`refactor(arena): make strength estimate order-invariant`) contained an order-invariant batch Elo estimator and Wilson interval, but the PR was based on an older `main` and remained unmerged. After PR #80 introduced paired games with identical openings and inverted challenger colours plus pentanomial aggregation, the standalone #78 implementation was no longer the correct next integration point.

## Decision
Close #78 instead of forcing a merge or resolving its stale history in place. Preserve its methodological idea (batch, order-invariant descriptive strength estimation) as a reusable concept, but reimplement it later on top of the paired-game/pentanomial data model.

## Rationale
The primary Arena experiment now has a stronger experimental unit: a two-game colour-inverted pair. A strength estimator that ignores this structure risks treating observations as independent and losing the variance-reduction rationale behind paired testing. The Fishtest/Stockfish methodology and the project's Arena statistical documentation therefore take precedence over the older standalone estimator.

## Consequence
No functionality from #78 is silently considered merged. Any future strength-estimation implementation must be based on the current `main` and the paired-game representation from PR #80, after a real Arena run validates the data pipeline.

## Next validation
Run the current Arena on `main`, inspect complete/incomplete pairs and pentanomial bins, then decide how normalized Elo and sequential testing should consume the observed structure.

## Evidence
- PR #78: https://github.com/Siuo-Player/RedWar/pull/78
- PR #80: https://github.com/Siuo-Player/RedWar/pull/80
- Fishtest statistical methodology: https://official-stockfish.github.io/docs/fishtest-wiki/Fishtest-Mathematics.html
