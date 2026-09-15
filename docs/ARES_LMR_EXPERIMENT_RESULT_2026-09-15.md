# Ares LMR experiment — authoritative result

## Experiment

This records the final result of the controlled single-ply Late Move Reduction (LMR) experiment defined by issue #494 and implemented for PR #507.

The candidate was deliberately conservative:

- reduction of one child ply;
- only late `MOVE` actions;
- minimum search depth 4;
- minimum move index 3;
- first/root-PV move excluded;
- TT principal move excluded;
- all non-`MOVE` actions excluded;
- active STUN continuations excluded;
- reduced searches were re-searched at full depth when the reduced result improved the relevant null-window bound.

No evaluator, rules, gameplay, or balance change was part of the candidate.

## Correctness validation

The authoritative Ares workflow for PR #507 passed the structural validation preceding promotion:

- challenger build: PASS;
- baseline build: PASS;
- protected tactical suite: PASS, all 7 cases at all 3 tested node budgets;
- deterministic search comparator: PASS (`SEARCH REGRESSION: PASS`).

## Authoritative strength result

The valid cumulative promotion run was **Ares workflow #23**, run `35027785973`, on candidate commit `bee74c3dd07d4f41224d7ab9c67f0d0ad2c3c613`.

The workflow used the repaired cumulative result-file handling and evaluated the fixed sequential looks of 96, 192, 320, and 512 complete games.

| Look | Games | Point estimate (Elo) | One-sided lower bound (Elo) | Decision |
| ---: | ---: | ---: | ---: | :--- |
| 96 | 96 | 0.00 | -58.45 | continue |
| 192 | 192 | +14.48 | -29.07 | continue |
| 320 | 320 | +26.11 | -6.52 | continue |
| 512 | 512 | +12.22 | -13.58 | **reject** |

At the final 512-game look, the promotion gate reported:

> `MAX_GAMES reached without statistical proof of challenger superiority`

The lower bound remained negative, so the experiment did not establish the required strictly-positive effect under the active #372 promotion authority.

The earlier 100-game diagnostic result associated with PR #500 is not used as promotion evidence. The first 96-game look from the earlier infrastructure-faulted run is also not a substitute for the valid cumulative run.

## Disposition

PR #507 remains unmerged. The LMR candidate is **not promoted to main**.

This result closes this specific single-ply LMR experiment. A future LMR attempt should be treated as a new hypothesis/experiment with independently justified design and fresh evidence; this result should not be reinterpreted as proof that every possible LMR scheme is invalid.

## Evidence

- Definition: issue #494
- Candidate: PR #507
- Final authoritative run: Ares workflow #23, run `35027785973`
- Evidence artifact: `redwar-ares-authoritative-507`, artifact `10420239661`
