# Independent final manuscript review

Date: 2026-10-27. Verdict: **PASS for mathematical argument and claim/evidence consistency at the reviewed hash. No blocking correction identified.** This is an internal AI-agent review, not peer review, patent review, or a release authorization replacing the remaining packaging/CI checks.

Reviewed manuscript: `aim/exact_risk_oracle/paper.md`.

SHA-256: `101e874e257f4279d958d92fd6d7618ad6513b1ab9f2e16f8fe809fdf3fa967a`.

Reviewed supporting materials: frozen `PROTOCOL.md`, saved `results/rows.jsonl`, `summary.json`, `receipt.json`, the existing mathematical/implementation/SOCP reviews, and the independent saved-evidence review. No frozen file was edited. No matrix, optimization, model inference, face enumeration, or binomial outcome experiment was repeated. A separate standard-library calculation read the raw rows to recompute the reported aggregates and timing table; it did not import project modules.

## Proof and scope

The bias-variance identity is correct for fixed coefficients and independent binomial counts. The manuscript correctly states that it does not certify outcome-dependent sampling, uncertain weights, correlation, or missingness assumptions. Sign alignment, scalar square conjugacy, the saturated/unsaturated derivative, and its monotonic ratio are valid. The sorted-root construction matches the reviewed implementation.

Both the soundness proof and the construction proof are correct. The upper-bound checker uses weighted Cauchy-Schwarz and a feasible attaining witness; it does not require a trustworthy breakpoint search. Zero variance with positive bias, zero bias, irrelevant zero/zero coordinates, coincident breakpoints, and the A_0 = 1 flat case are covered by the stated definitions. Metadata is appropriately separated from the mathematical certificate.

For additional exposition, a nonblocking sentence could make positive-root existence explicit: after the zero-root branch is excluded, the ratio in (4) exceeds one as t approaches zero, while at t = D it is at most sum_i d_i/D = 1. Its continuity and monotonicity therefore locate a root in (0,D]. This completes an already valid argument more visibly for readers; it does not change the algorithm or results.

The O(k log k) statement is explicitly an arithmetic/comparison count. The paper correctly does not infer a matching bit-complexity bound from the observed 41-bit certificate components.

## Recomputed saved-row figures

The following manuscript figures agree with the raw records:

- 148 cases and 148 valid-certificate flags.
- 128 exact reference agreements and 16 direct-expectation agreements.
- 64 saved grids, of which six strictly understate risk.
- Maximum grid gap 25/14112, approximately 0.001772, at `small-056`.
- 56 conic comparison records, comprising 54 recorded solver calls and two algebraic zero-d cases.
- Maximum absolute conic risk discrepancy 1.2387751519016277e-9.
- Shared-case median conic / (exact solve + check) time ratio 29.877619844869855.
- All four timing-table rows reproduce the manuscript's rounded values.
- Twelve exact-only cases; maximum k = 16384. Its two-case median solve/check durations are 371.5336499735713/231.33099998813123 ms.
- Maximum saved certificate numerator/denominator length: 41 bits.

The timestamps, platform, versions, and 4.877-second rounded wall time agree with the saved receipt. The final frozen protocol explicitly includes k = 16384, so the result is not an unexplained expansion from the earlier proposed 4096 limit. This review verifies saved evidence consistency, not external attestation of the machine or timestamps. The separate saved-evidence review supplies an independent exact lower/upper certificate replay; reference and full-outcome enumerations were not repeated during manuscript review.

## Prior art, originality, and timing claims

The paper gives adequate credit to historical binomial-combination estimators, exact SDP/SOCP relaxations, and sorted one-dimensional breakpoint techniques. It specifically identifies the c = 0 submodular box case as already tractable. Its proposed contribution is a specialized executable rational method and certificate, not a new estimator, a first polynomial-time algorithm, or a patent novelty finding. No stronger novelty conclusion is justified by the bounded literature screen, and none is asserted.

The 29.88 ratio is described as an end-to-end implementation comparison. The text states that general-conic time includes expression construction and canonicalization, that exact timing includes d/v construction, and that imports are excluded. It separately acknowledges untested warm/cached formulations and different solvers. Therefore the manuscript does not misrepresent this ratio as a universal property of the numerical solver's iterations. Two inputs per size and one timed execution per method are disclosed. The large exact-only cases are not presented as conic comparisons.

The operational gate is reported as a prospective engineering criterion, not a statistical significance or deployment result. The numerical conic baseline's success is preserved. The next allocation-decision experiment is explicitly NOT PERFORMED, and the old model queues are not represented as reopened or as evidence for this method.

## Release boundary

This review supports the manuscript's current mathematical and measured claims. It does not itself verify the generated PDF layout, deterministic PDF rebuild, final license inventory, remote Git contents, Linux CI, or release URLs. Those require their own evidence before a published-release claim. Any subsequent substantive edit changes the reviewed manuscript hash and should be identified in the final release record.
