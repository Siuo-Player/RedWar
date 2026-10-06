# Historical real-Arena evidence update

**Issue:** #488  
**Baseline inspected:** `8bc99ccbf2cf1f7e7e22bd83cab4f8fda762d8f5`  
**Status:** evidence registration only; #488 remains open and no promotion authority changes.

## Newly registered real version edge

PR #507 produced a real authoritative Ares promotion run after the promotion-path import fix in PR #509.

- GitHub Actions workflow run: `35027785973`
- Artifact: `10420239661`
- Artifact digest: `sha256:6138be65dd5619e3d0122173dfe4d5d00f6d7b4fa73eba8e012c8178ea42b304`
- Challenger version: `bee74c3dd07d4f41224d7ab9c67f0d0ad2c3c613`
- Baseline version: `48dd4df0f6809d072190291bceebb09ddfe52e5f`
- Recorded rules version: `bee74c3dd07d4f41224d7ab9c67f0d0ad2c3c613`
- Fixed node budget: 10,000
- Games: 512
- Complete colour-inverted pairs: 256
- Challenger colour balance: 256 white / 256 black
- Openings: 256 fresh conditions
- Valid games: 512
- Draws: 0
- Invalid games: 0
- Result: 265 challenger wins / 247 baseline wins
- Pair bins: WW=39, split=187, LL=30

The four stage files are stored in the authoritative artifact and are contiguous by global game index:

| Stage | Game indexes | Games | SHA-256 |
|---|---:|---:|---|
| 96 | 0–95 | 96 | `c05d561bfd7ed3ffed43bc151e46420703e752eb92862b559ce30881127f2094` |
| 192 | 96–191 | 96 | `557b3839cf37f6d860d4f84f9994c0b1b884e63397204ce4448c17e27daa0043` |
| 320 | 192–319 | 128 | `0cc22b8ef6ce703a549358384c177bed3a71713abf2713a9e5f19791c443f257` |
| 512 | 320–511 | 192 | `3416bff38bbd12eca77b87cabc8715220c2f6379c0ef0915ba212d85e7a1c8a6` |

The deterministic concatenation of those four original JSONL files has SHA-256:

`b33ada8e75ff6d0edaa0df7a4d315c0041c9d6ceb6ccb3e6a1563916cb0fd87e`

## Authoritative gate outcome

The same run reached every declared cumulative stage:

| Cumulative games | Elo-equivalent point estimate | One-sided lower bound | Decision |
|---:|---:|---:|---|
| 96 | 0.00 | -58.45 | continue |
| 192 | 14.48 | -29.07 | continue |
| 320 | 26.11 | -6.52 | continue |
| 512 | 12.22 | -13.58 | reject |

The final `reject` is the authoritative promotion decision for PR #507. It is recorded here as historical evidence, not as evidence that the candidate is universally weaker.

## Lifecycle qualification

The promotion collector creates one challenger and one baseline `CppEngineBot` per stage and reuses them for that stage. The independent lifecycle investigation on main established that process-global TT persistence is sufficient to reproduce the previously observed persistent-vs-fresh A/A divergence under the tested diagnostic protocol.

Therefore this edge is:

- valid as an observation produced by the authoritative promotion instrument;
- provenance-addressed and reusable for descriptive historical comparison;
- **not** lifecycle-neutral evidence.

No attempt is made here to correct, reweight, or reinterpret the promotion result.

## Why the older 100-game control is not a version edge

The existing committed 100-game real-strength dataset uses:

`37b94d51b810b7ef698139f896afd30eee50fa5a` ↔ `f6a1ee4beb160ee4e23e7e044fba0f78aa5961ac`

but that experiment is an A/A control, not a version-to-version comparison. GitHub compare confirms that `f6a1ee4...` adds only `docs/DECISIONS/2026-08-27-strength-control-run.md` on top of `37b94d5...`, with no engine-file changes. Its 50–50 result therefore validates the measurement baseline rather than adding a new historical rating edge.

The older #471 A/B result is also not promoted into the compatible graph because its stored experiment metadata reports `unknown` version/rules identities and uses the older 100-game Arena protocol.

## Historical graph status

The only currently registered compatible version-to-version edge is:

`48dd4df0f6809d072190291bceebb09ddfe52e5f` ↔ `bee74c3dd07d4f41224d7ab9c67f0d0ad2c3c613`

This is one connected component containing two Ares versions, but it is not yet a multi-version historical graph with a shared intermediate version. The ledger deliberately remains fail-closed:

**connected historical graph: not yet established for #488 acceptance.**

The next valid evidence is at least one additional provenance-compatible real Arena comparison sharing one endpoint with the current edge (or an equivalently strong multi-edge set) so the historical calibration can be fit over multiple connected Ares versions.

Commit lineage is not treated as an Arena comparison edge, and A/A controls are not promoted into version comparisons.

## Authority boundary

This registration does not:

- alter the promotion gate;
- close #372;
- claim a calibrated historical Elo scale;
- convert diagnostic results into promotion evidence;
- infer strength from NNUE/performance measurements.

It only makes an already-executed real Arena version comparison durable and auditable for the remaining #488 historical-evidence work.
