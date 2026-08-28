# Decision — Public repository security hygiene

**Date:** 2026-08-28  
**Scope:** public-repository vulnerability reporting, dependency update configuration, CodeQL analysis, and workflow security posture  
**Status:** proposed via dedicated PR

## Verified

- The RedWar repository is public and the authenticated agent has repository administration/write permission.
- No `SECURITY.md` or `.github/dependabot.yml` existed on `main` before this work package.
- No `github/codeql-action` workflow existed on `main` before this work package.
- A repository search found no `pull_request_target` usage and no direct workflow references to secrets/credentials in the checked search scope.
- Existing normal CI workflows already use read-only `GITHUB_TOKEN` permissions where explicitly declared; the new CodeQL workflow uses only `contents: read`, `security-events: write`, and `actions: read` because SARIF upload requires security-events write access.
- `.gitignore` excludes common local credentials and generated build/training artifacts, including `.env`, virtual environments, executables, NNUE checkpoints, generated datasets, and logs.

## Changes

### SECURITY.md

Adds a private-reporting policy and explicitly warns that the repository is public.

### Dependabot

Adds weekly version-update configuration for:

- `pip` dependencies in `/`;
- GitHub Actions in `/`.

The configuration does not grant Dependabot write access to `main`; updates arrive as pull requests and remain subject to repository governance.

### CodeQL

Adds a non-required security-analysis workflow for C++ and Python on pushes to `main`, pull requests, weekly schedule, and manual dispatch.

The workflow does not become a required status check for ordinary PR merges. It is complementary security evidence, not a replacement for `tests` or `ai-quality-gate`.

## Administrative settings not verified by this integration

The available repository API did not expose current values for:

- Dependabot alerts;
- Dependabot security updates;
- secret scanning;
- push protection.

These are GitHub Settings features and must not be represented as enabled merely because configuration files exist in the repository.

## Security conclusion

This package improves repository-level hygiene without changing game, Ares, Arena, thresholds, or product behaviour. Historical secret scanning remains a separate assurance task; the current-content audit must not be treated as proof that no credential has ever existed in Git history.
