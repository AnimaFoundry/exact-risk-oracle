# Independent implementation review

Date: 2026-10-27. Reviewed files: `aim/exact_risk_oracle/oracle.py`, `check_certificate.py`, and `tests/test_oracle.py`. The reviewer did not modify production code. This review precedes the proposed finite experiment freeze; it is not a result from that experiment.

## Finding

No concrete solver or certificate soundness defect was found in the inspected implementation. The existing nine development test methods passed locally with:

    python -m unittest discover -s aim/exact_risk_oracle/tests -p test_oracle.py -v

The reported test execution was 0.002 seconds. This is a local development check, not Linux CI, a performance benchmark, or an independent experimental replication.

## Solver analysis

The solver rejects unequal, empty, negative, floating-point, and boolean inputs. Exact integer, Fraction, and rational-string inputs are accepted. `from_estimator` enforces weights summing to one, nonnegative integer counts, 0 <= coefficient <= weight, and coefficient zero at count zero. Its d and v transformation matches the reviewed bias-variance identity.

The active list includes exactly coordinates with d > 0 and v > 0. The initial `a` is their sum d^2/v; the initial `c` is the total d mass of v = 0 coordinates. Coordinates with d = 0 do not alter either aggregate, irrespective of their variance. When c = 0 and a <= 1, the zero witness/loading is the correct certificate, including the flat a = 1 case.

When the positive-root branch is entered, each iteration examines the interval before the next breakpoint, then moves the whole equal-breakpoint group from the unsaturated to the saturated aggregate. Testing `a < 1` before dividing is necessary and correctly implemented. The two inclusive interval comparisons admit a root exactly on either endpoint. Equal breakpoints are grouped, so they cannot cause a spurious intermediate active set. The final interval has all active coordinates saturated; exact arithmetic makes a = 0 there, so division by 1 - a is safe.

The early `break` leaves the current group unconsumed, which is harmless: subsequent witness/loading construction uses the original d and v, not the partially consumed group iterator. Sorting tuples additionally orders tied breakpoints by d and v, but this does not affect grouping or correctness.

The computed loading and witness satisfy the reviewed closed-form construction. In particular, a positive d with v = 0 receives positive loading and witness one on the positive-root branch. A d = v = 0 coordinate uses witness zero rather than dividing by zero. All-zero variance, all-zero bias, and zero-variance/positive-bias mixtures are covered by the branch invariants.

The O(k log k) **arithmetic-operation** statement is accurate: sorting is followed by an O(k) sweep and O(k) output construction. It must not be reported as an O(k log k) bit-complexity bound. Python Fraction comparisons, gcd operations, and integer arithmetic depend on operand lengths. The algorithm may stop early, so the returned interval count is an examined-interval diagnostic rather than a problem-independent complexity measure.

## Certificate checker analysis

The checker imports no solver and performs no breakpoint search. It enforces matching vector lengths, nonnegative d/v/loading, a feasible witness in [-1,1]^k, the zero-denominator condition, the weighted-Cauchy ratio bound, exact equality between the witness objective and the loading upper bound, and consistency of the reported objective/risk.

These checks are sufficient for a global lower/upper proof. Permitting negative witness coordinates is sound because the original domain is symmetric and weighted Cauchy applies to all signs. Solver witnesses happen to be nonnegative. Invalid rational strings and missing required proof fields fail closed through the listed exceptions.

The fields `t` and `intervals` are deliberately ignored. They are **unverified diagnostic metadata**, not part of the mathematical certificate. Downstream displays or reports must not describe them as independently verified unless a separate diagnostic check is added. The verifier proves the certificate for the d/v vectors supplied by its caller; it does not authenticate an experiment's inputs or verify the original statistical assumptions.

## Recommended pre-freeze regression additions

The existing tests cover principal cases but do not isolate every certificate obligation. Add the following disclosed development cases before freezing the experiment:

1. A positive root at coincident breakpoints: d = (1/4,1/8,1/8), v = (0,1/16,1/16). Expected t = 1/2 and objective = 1/8. This exercises the inclusive root test before a tied group, including one missing/zero-variance coordinate.
2. A valid certificate whose witness is changed to zero, while loading/objective/risk remain unchanged and its positive optimum is retained. It must be rejected because the lower bound no longer attains the upper bound, even though the witness remains inside the box.
3. For d = (1/6,1/3), v = (1/9,1/36), submit x = loading = zero, objective zero, and risk = sum(v)/4. This internally consistent-looking forgery must be rejected by the ratio bound; it must not pass merely because lower and reported upper are equal.
4. Remove or alter `t` and `intervals` in an otherwise valid certificate, and require verification to remain true. This documents their intentional exclusion from the proof rather than accidentally relying on them later.

These are known development diagnostics, not future holdout cases. They must not be counted as evidence of a general empirical success rate.

## Proposed finite-budget review

The proposed limits are coherent for a bounded CPU-only verification: 128 fresh rational estimator cases with k = 1..6 and an independent exact face reference for all; a quarter grid on the first 64 cases restricted to k <= 5; 48 small and eight scale SOCP comparisons with scale k <= 256; and 12 exact-only scale cases spanning k = 16..4096. The plan adds no model calls or external inference cost.

Before freeze, the protocol must specify the exact dimension allocation, deterministic generator, coefficient/count/weight ranges, random seed if any, maximum rational input sizes, ordering, and a finite wall-clock limit with a fail-closed timeout record. The first-64 dimension restriction must be enforced in the generator rather than asserted after generation. Confirmatory fixtures must not copy the disclosed examples or reuse frozen negative-audit cases.

The budget counts should identify overlap: which SOCP cases are drawn from the 128 small cases, and which scale cases are additional inputs. Count solver invocations explicitly; no automatic retries, solver substitution, or post-result extra timing repetitions. Freeze solver name/version and tolerances before execution. Report setup time separately if comparing numerical solver cost with the exact routine.

Require exact agreement with the independent face reference and exact certificate verification on every applicable case. Degenerate reference failures remain unresolved evidence rather than silently omitted cases. SOCP is a strong known formulation but its finite-precision result is not itself an exact certificate; record solver status and numerical residuals, and never relax acceptance thresholds after seeing disagreement. The numerical baseline's scale limit must be visible when discussing the larger exact-only cases.

A quarter-grid failure quantifies discretization error; it does not show superiority over the known exact SOCP method. Runtime comparisons measure computational advantage on the frozen suite, not better statistical estimators or empirical sensing performance. A successful finite suite does not prove algorithmic novelty. No new experiment has been executed in this review.
