# Independent SOCP baseline and novelty boundary

Date: 2026-10-27. Status: implementation prepared; benchmark NOT PERFORMED.

## Exact problem and independent formulation

For supplied nonnegative rational vectors `d` and `v`, the quantity of interest is

`M(d,v) = max_{0 <= x_i <= 1} (d^T x)^2 - sum_i v_i x_i^2`.

The corresponding risk is `(sum_i v_i + M(d,v))/4`.  The conic baseline in
`aim/exact_risk_oracle/socp_baseline.py` independently constructs

`min sum_i lambda_i`

subject to `lambda_i >= 0` and

`sum_{i:d_i>0} d_i^2/(v_i+lambda_i) <= 1`.

CVXPY expresses each term through `quad_over_lin(d_i, v_i + lambda_i)` and
Clarabel solves the resulting cone program. The baseline does not import the
production oracle, its sorting routine, its breakpoints, its root, its witness,
or its result.  It does not use the old finite energy audit or any model output.

The matrix condition behind this program is

`Diag(v+lambda) - d d^T >= 0`.

Consequently, every exactly feasible loading vector gives

`(d^T x)^2 - sum_i v_i*x_i^2 <= sum_i lambda_i*x_i^2 <= sum_i lambda_i`.

This is the diagonal-loading dual of the basic semidefinite relaxation of the
homogeneous box quadratic. The nonnegative `d` structure makes the off-diagonal
entries of `Diag(v) - d d^T` nonpositive. Its homogeneous linear term is zero,
which is inside the already known exact conic-relaxation case. The current
project therefore cannot claim the first polynomial-time or first exact conic
solution to this class. A solver-independent rational certificate and a
specialized implementation must be evaluated as narrower contributions.

Coordinates with `d_i=0` are omitted from the solver, with optimal loading zero.
This also avoids undefined `0/0` expressions. If `d_i>0` and `v_i=0`, the
quadratic-over-linear effective domain requires a positive loading; no variance
floor is substituted. If all `d_i=0`, the algebraic optimum is zero at `x=0`,
and the result is labelled `analytic_zero_d` with zero solver calls.

## API and numeric contract

`solve(d: Sequence[Fraction], v: Sequence[Fraction]) -> dict`

The record includes `risk`, `objective`, the separately reported solver
objective, the returned loading vector, solver status, solver settings, iteration
count, timings, independently recomputed residuals, and `numerically_accepted`.
All coordinates must be exact nonnegative `Fraction` instances; vector lengths
must match. The function rejects invalid inputs rather than changing their sign
or inventing missing values.

The objective and loadings are solved in a normalized scale

`s = max(sum_i d_i^2, max_i v_i)`;
`d' = d/sqrt(s)`, `v' = v/s`, `lambda' = lambda/s`.

The inputs alone determine this scale. No exact-oracle answer or selected test
outcome determines it. Returned objectives and loadings are converted back to
the original scale.

Frozen solver settings are Clarabel `tol_gap_abs=1e-10`, `tol_gap_rel=1e-10`,
`tol_feas=1e-10`, `max_iter=200`, one solver invocation, and no retry or alternate
solver. An exception or absent result remains an explicit failed record.

Independent numerical residual checks use tolerance `1e-7`:

- all returned quantities must be finite;
- every active denominator must be positive;
- the maximum negative loading in normalized units must be at most the tolerance;
- the recomputed cone sum must exceed one by at most the tolerance;
- the normalized solver objective and the sum of returned loadings must agree
  within the tolerance.

`numerically_accepted` additionally requires the status `optimal`;
`optimal_inaccurate` is preserved but is not accepted. Small negative loadings
are preserved, not silently clipped. These checks concern reported primal
feasibility of the dual program and internal objective consistency; they do not
independently prove numerical optimality. Comparison against the rational oracle
must report the objective error separately.

**A small floating residual is not an exact certificate.**
`objective_is_exact_certificate` is always false for this baseline record.
The solver's approximate objective is not called a rigorous upper bound, even
if its cone violation passes the tolerance. Benchmark conclusions must distinguish
the mathematical exactness of the conic formulation from floating-point solver
accuracy, status, and failures.

`time_seconds` includes normalization, conic expression construction,
canonicalization, solving and residual calculation; dependency imports are
excluded. `optimization_wall_seconds` measures the call to `problem.solve`,
which includes CVXPY canonicalization. `solver_reported_seconds` is separately
retained and must not be substituted for end-to-end time without disclosure.
The first solve can have library startup overhead. No assertion about speed
follows from writing this implementation.

## Required comparison and falsifiers

The frozen new experiment should use the same `d,v` instances for every method,
preserve all statuses, and report both absolute objective error and the declared
residuals. It should include zero loading, missing-sample (`v=0,d>0`), near-flat,
tied-breakpoint, and multiple-active-coordinate cases. These are mathematical
test cases, not hardware, model-training or real-world missingness validation.

Any mismatch between an exact oracle claim and an independent exact verifier
refutes the exact implementation claim. A failed or inaccurate conic solve is
reported as a baseline failure on that instance, not as a proof of a general
solver deficiency. An already published same-scope algorithm or equally cheap
exact certificate refutes a novelty claim; a general conic exactness theorem is
already known and must be credited. Comparable end-to-end cost from the strong
baseline would defeat the practical speed claim. A floating speed win alone
would not establish hardware energy savings, optimal sensing policy, new
estimator theory, or patent novelty.

## Source attribution

1. Sunyoung Kim and Masakazu Kojima. **Exact Solutions of Some Nonconvex
   Quadratic Optimization Problems via SDP and SOCP Relaxations**.
   *Computational Optimization and Applications* 26(2), 143-154 (2003).
   DOI: <https://doi.org/10.1023/A:1025794313696>.
   Author-submitted primary entry:
   <https://optimization-online.org/2002/04/467/>.
   This establishes the relevant existing conic exactness lineage; it is not
   an algorithm invented by this project.
2. Samuel Burer, Karthik Natarajan, and Rick Willemsen. **On the Semidefinite
   Representability of Continuous Quadratic Submodular Minimization With
   Applications to Pricing and Moment Problems**. Primary manuscript, posted
   2025-04-04; repository record updated 2026-08-31.
   <https://optimization-online.org/wp-content/uploads/2025/04/submodular-1.pdf>.
   Proposition 1 restates the nonpositive-linear-term exactness result of
   Kim and Kojima, including the zero-linear-term case used here. The broader
   arbitrary-linear-term relaxation is not universally exact.
3. Stephen Becker and M. Jalal Fadili. **A Quasi-Newton Proximal Splitting
   Method**. *Advances in Neural Information Processing Systems* 25 (2012).
   Primary preprint: <https://arxiv.org/abs/1206.1156>.
   Primary proceedings:
   <https://papers.neurips.cc/paper_files/paper/2012/hash/e034fb6b66aacc1d48f445ddfb08da98-Abstract.html>.
   Its diagonal-plus-rank-one proximal calculus and exact sorted breakpoints
   are algorithmic antecedents. Its convex positive-definite-metric setting
   differs from the nonconvex quadratic maximum evaluated here; the existence
   of a one-dimensional reduction or sorting step alone is not a novelty claim.

The implementation was written for this experiment from the displayed conic
formulation. No external implementation or private example was copied. Runtime
dependency versions and licenses must be recorded by the parent experiment
before a release. No benchmark or model inference was executed during this
baseline preparation.

## Pre-freeze toy smoke check

Syntax compilation passed. Four declared algebraic toy cases were then checked:
all-zero `d` (no solver call), one coordinate with `d=1/2,v=1/8`, a missing-sample
coordinate with `d=1/2,v=0`, and the flat boundary `d=1/2,v=1/4`. These made exactly
three Clarabel calls. All had accepted numerical status/residuals and agreed
with their hand-computed objectives `0`, `1/8`, `1/4`, and `0`, respectively,
within absolute `1e-7`. This is a development smoke check, not a benchmark or
independent empirical validation. The source was subsequently tightened to
reject nonfinite rescaled output; the benchmark remains NOT PERFORMED.
