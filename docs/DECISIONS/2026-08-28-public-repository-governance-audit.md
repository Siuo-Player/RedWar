# Decision — Public repository governance and release audit

**Date:** 2026-08-28  
**Scope:** GitHub public-repository governance, licensing, attribution and release readiness  
**Status:** audit recorded; one GitHub administrative rule remains to be corrected outside the code PR

## Verified repository state

- Repository `Siuo-Player/RedWar` is public.
- The default branch is `main`.
- The repository reports administrative/write access for the authenticated agent.
- The active GitHub ruleset `Protect main` exists and targets the default branch.
- The ruleset currently requires pull requests, one approval, stale-review dismissal, status checks `tests` and `ai-quality-gate`, strict/up-to-date checks, and blocks branch updates that are non-fast-forward or direct updates.

## Ruleset discrepancy

The intended project policy requires review-thread resolution. The current ruleset has:

```text
required_review_thread_resolution = false
```

This audit does not claim the rule was corrected because the available GitHub integration exposes ruleset reads but no ruleset-update operation.

The current ruleset also has a `RepositoryRole` bypass actor configured with `always` bypass mode. This is recorded as observed state rather than silently changed policy.

## Required checks

The actual GitHub job names verified in the repository workflows are:

```text
tests
ai-quality-gate
```

Experimental Arena/Strength workflows remain separate from ordinary required PR checks.

## License decision

The repository now materializes the previously documented intended policy:

- general project-owned code outside `ai/`: MIT;
- project-owned Ares code in `ai/`: GPL-3.0-or-later;
- third-party components retain their own licenses.

## Game Icons decision

Local PNG assets in `ui/assets/` are treated as third-party derivatives and must retain the upstream attribution requirements.

The official upstream corpus is `game-icons/icons`, and its published license information states CC BY 3.0 with contributor attribution requirements.

An automated matcher has been added. It is conservative and cannot promote an icon to a positive attribution status from filename similarity alone.

Because the current agent environment cannot reproducibly obtain and rasterize the full local+upstream image corpus together, the initial manifest deliberately records all 19 local PNGs as `UNRESOLVED`. No author has been invented.

## Security observation

A limited current-content search found no matches for common GitHub-token/private-key markers `ghp_` and `BEGIN PRIVATE KEY`. This is not a complete historical secret scan and must not be described as proof that the repository history has never contained a secret.

## Follow-up

1. Correct `required_review_thread_resolution` in the `Protect main` ruleset using a GitHub administration interface that supports ruleset mutation.
2. Run `tools/licensing/match_game_icons.py` against a pinned checkout of the official Game Icons corpus and review any `AMBIGUOUS`/`UNRESOLVED` results.
3. Preserve the resulting provenance manifest in the repository.
