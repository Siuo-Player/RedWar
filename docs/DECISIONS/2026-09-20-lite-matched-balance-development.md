# Decision — 1.0-Lite matched Balance Lab development campaign

## Status

Approved as a development-only instrument. No balance or Ares policy changes are included.

## Problem addressed

The first 96-condition campaign (#546, run 35450276404) is valid for contextual screening, but hero effects are confounded by:
- fixed White initiative;
- one game per condition;
- frequent hero overlap between both teams;
- unequal team draft costs.

## Frozen design

The second campaign uses only exact configured-cost hero substitutions. A candidate and control hero must have the same configured cost, and they replace each other while the other five heroes are shared.

For each independent base context:
1. candidate is White and control is Black;
2. the same composition context is vertically reflected with team identities swapped;
3. control is White and candidate is Black.

The two games are one matched observation.

Every game therefore has identical total team draft cost, identical shared fillers, and reversed candidate/colour assignment.

## Current roster eligibility

The current draftable roster yields one legal exact-cost pair with enough remaining budget to field six unique draftable heroes per side:

- FrostMage ↔ Phantom: 5 points each.

Dragoon and Nightshade both cost 193, but neither can fit a legal six-hero roster under the 200-point team budget because the other five unique draftable heroes already require more than 7 points.

All other heroes have no exact-cost control counterpart under the current roster.

The runner fails closed if the current eligibility set changes.

## Replication

There are 48 independent base contexts for the current eligible pair and two games per context:
- 48 matched observations;
- 96 games total;
- deterministic requested seeds start at 3,000,000,000 with step 17;
- each requested seed resolves to the first legal unique composition/placement context;
- resolved seeds and initial-position hashes are persisted.

Each context varies:
- the five shared filler heroes;
- deterministic placement order.

No exact matched context is repeated.

## Provenance and evidence

Each raw game records:
- campaign and pair identifiers;
- candidate/control hero;
- candidate side;
- exact white/black hero roster;
- shared fillers and placement;
- requested/resolved seed and resolution attempt;
- equal team draft cost;
- initial/final RWEN;
- initial-position hash;
- full action trace;
- terminal reason and winner;
- source SHA, rules version, engine SHA-256, compiler identity and hero-config SHA-256.

The analysis layer is paired. Aggregate win rates are retained only as descriptive diagnostics and are not a balance authority.

## Protected data

The protected hold-out namespace begins at the previously reserved 2,000,000,000 + 7 × index space and is not resolved or consumed by this runner.

## Explicit exclusions

This campaign does not:
- change hero prices or mechanics;
- change rules;
- change Ares policy;
- make a competitive-strength claim;
- declare any hero balanced or unbalanced;
- compensate for first-player advantage globally;
- execute the protected hold-out.
