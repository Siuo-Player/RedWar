# Decision — Public repository security hygiene

**Date:** 2026-08-28  
**Scope:** public-repository vulnerability reporting, dependency update configuration, CodeQL analysis, and workflow security posture  
**Status:** implemented on `main` via PR #154; administrative security settings remain partially unverified

## Verified

- The RedWar repository is public and the authenticated agent has repository administration/write permission.
- No `SECURITY.md` or `.github/dependabot.yml` existed on `main` before this work package.
- No `github/codeql-action` workflow existed on `main` before this work package.
- A repository search found no `pull_request_target` usage and no direct workflow references to secrets/credentials in the checked search scope.
- Existing normal CI workflows already use read-only `GITHUB_TOKEN` permissions where explicitly declared; the CodeQL workflow uses only `contents: read`, `security-events: write`, and `actions: read` because SARIF upload requires security-events write access.
- `.gitignore` excludes common local credentials and generated build/training artifacts, including `.env`, virtual environments, executables, NNUE checkpoints, generated datasets, and logs.

## Implemented

### SECURITY.md

A private-reporting policy was added and explicitly warns that the repository is public.

### Dependabot

Weekly version-update configuration was added for:

- `pip` dependencies in `/`;
- GitHub Actions in `/`.

The configuration does not grant Dependabot write access to `main`; update proposals remain pull requests subject to repository governance. See the GitHub documentation for `dependabot.yml` version-update configuration: https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/configuration-options-for-dependency-updates.

### CodeQL

A non-required security-analysis workflow was added for C++ and Python on pushes to `main`, pull requests, weekly schedule, and manual dispatch.

The workflow does not become a required status check for ordinary PR merges. It is complementary security evidence, not a replacement for `tests` or `ai-quality-gate`.

The initial C++ CodeQL attempt failed because `autobuild` selected `setup.py` without installing Cython. That failure was diagnosed and corrected by switching to CodeQL manual build mode and the repository's existing explicit C++ builder. The corrected CodeQL C++ and Python analyses both passed on PR #154.

CodeQL Action v4 is the current supported major line of the official CodeQL Action repository: https://github.com/github/codeql-action.

## Validation

PR #154 was merged after all relevant validation completed successfully:

```text
Test Suite             ✅
AI Quality Gate        ✅
CodeQL Python          ✅
CodeQL C++             ✅
```

The AI quality gate correctly skipped the expensive Ares benchmark/Arena because the security PR contained no executable Ares changes.

## Administrative settings not verified by this integration

The available repository API did not expose current values for:

- Dependabot alerts;
- Dependabot security updates;
- secret scanning;
- push protection.

These are GitHub Settings features and must not be represented as enabled merely because configuration files exist in the repository. The corresponding GitHub security settings are documented separately at: https://docs.github.com/en/code-security.

## Security conclusion

This package improves repository-level hygiene without changing game, Ares, Arena, thresholds, or product behaviour. Historical secret scanning remains a separate assurance task; the current-content audit must not be treated as proof that no credential has ever existed in Git history.
