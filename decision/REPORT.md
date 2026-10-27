# Does exact risk improve sampling decisions?

AnimaFoundry Research | 27 October 2026 | v1.1.0 companion to the unchanged
v1.0.0 methods manuscript. Internal verification, not external peer review.

## Result

One of 48 frozen original synthetic scenarios exhibited a strictly better
sampling allocation when evaluated by continuous worst-case risk instead of a
five-point probability grid. The other 47 had no decision regret among any of
the grid's tied minimizers. The reusable general conic baseline chose the same
optimal allocation in the positive example. This is a finite existence result,
not an estimate of how frequently applications benefit or a new statistical estimator.

The complete three-way numerical-comparison gate did **not** pass: 12 of 2,259
conic records returned `optimal_inaccurate`. Their numerical risk errors were
small, but the frozen rule required `optimal` (or the stated algebraic branch).
No status requirement was relaxed, no solve retried and no failed candidate
discarded. These records do not demonstrate a wrong allocation or a solver bug.

## Design and evidence

The [prospective protocol](PROTOCOL.md), source and inputs were hashed before
the single run. The new seed was 271027117. There were 48 scenarios crossing
dimensions 2,3,4, fixed shrinkage constants 0,1/2,1,2 and four exogenous calendars.
Each calendar offered at most four unit-energy sampling opportunities with fixed
eligible strata. Idle was permitted; there was no energy storage or adaptation
to observed outcomes. Known weights and independent binomial observations remain
assumptions, not findings. All coefficients were fixed by a_i=w_i*n_i/(n_i+c),
with a_i=0 at n_i=0.

The frozen calendars yielded 753 distinct feasible count allocations, including
all-zero counts. Every method evaluated every allocation in three complete passes:
2,259 exact evaluations with certificate checks, 2,259 exact-arithmetic grid
evaluations and 2,259 conic evaluations. Of the latter, 42 used an explicit zero-bias
algebraic branch and 2,217 invoked Clarabel. These are technical repetitions of
48 scenarios, not 2,259 independent research units. Each allocation also received
one independently implemented exhaustive-face reference calculation.

The grid was p={0,1/4,1/2,3/4,1}^k. Absolute-value symmetry reduced the evaluated
grid to x={0,1/2,1}^k without changing its maximum. The stronger comparator used
one vectorized, DPP-checked CVXPY/Clarabel SOCP per scenario, reused across all
allocations and passes with warm_start=True. It received no exact answers or
oracle-based initialization. Program construction was separately charged to the
first pass; subsequent passes retained the program. All timing samples, numerical
vectors, warnings and outcomes are saved.

| Check | Observed result |
|---|---|
| Completed scenarios / distinct allocations | 48 / 753 |
| Exact certificates accepted | 2,259 / 2,259 |
| Independent exact reference agreement | 753 / 753 |
| Allocations whose grid understated risk, first pass | 68 / 753 |
| Scenarios with tie-robust decision improvement | 1 / 48 |
| Scenarios with any grid-minimizer regret | 1 / 48 |
| Conic records accepted by frozen rule | 2,247 / 2,259 |
| Maximum absolute conic risk discrepancy, all records | 1.1473e-10 |
| Exact correctness gate | PASS |
| Full conic-comparison / speed-claim gate | NOT PASSED |

The run started at 2026-10-27T06:57:43.863842Z and ended at
2026-10-27T06:57:58.752425Z. Measured execution time after imports was 14.411 seconds
on Windows 11 / Python 3.12.14. The cap was 900 seconds checked between calls,
not a hard in-call timeout. No model calls, external API charges, private material,
old-cohort reuse or outcome-guided input selection occurred.

## A decision difference with the same observation budget

Scenario `decision-023` has weights (6/13,5/13,2/13), c=1/2, four opportunities
and 29 feasible allocations. The frozen calendar permits both choices below.

| Evaluator | Selected counts | Reported minimum | Certified continuous risk |
|---|---|---|---|
| Coarse grid | (2,2,0) | 97/2704 | 466/12675, about 0.0367653 |
| Exact oracle | (2,1,1) | 1373/38025 | 1373/38025, about 0.0361078 |
| Reusable conic | (2,1,1) | numerical approximation to 1373/38025 | 1373/38025 |

The exact risk reduction is 1/1521, about 0.00065746 in squared-error risk, or
25/1398 = 1.7883% relative to the grid-selected allocation's certified risk.
Both decisions use four samples. Each evaluator has a unique minimizer in this
example, so the improvement is not manufactured by a tie-breaking convention.
The result persisted across all three technical passes. The independently
implemented face reference agreed for all 29 candidate risks.

This does not prove that sampling a previously unobserved stratum is universally
better. The earlier reserve-one hypothesis remains rejected as a universal rule.
Here the benefit follows from the particular weights, estimator and availability
contract; all 47 no-improvement scenarios remain in the report and raw evidence.
Nor did the exact method improve the allocation over the successful conic solution.

## Numerical warnings and timing

The 12 unaccepted conic records are four distinct allocations repeated three times:
`decision-010` counts (0,2), and `decision-046` counts (0,2,0,1), (1,0,0,0),
(2,0,0,1). Their retained residual checks passed and the numerical risk errors
were tiny. The reason for rejection was the `optimal_inaccurate` status under the
predeclared strict rule. Selection for those two scenarios is marked inconclusive,
rather than choosing among only the accepted candidates. The recorded false
`conic_choice_stable` flag there means no fully accepted decision sequence;
it is not evidence of observed allocation instability.

Across all 48 scenarios, descriptive conic/exact batch-time ratios had cold
median 13.25 (range 7.94-28.63) and warm median 9.26 (range 5.12-16.17). Warm
ratios first summarize the two warm passes within each scenario, then scenarios.
These include the two scenarios with numerical-status rejections, so the complete
predeclared speed-claim gate is false. We report the measurements, not a new
validated universal speedup. Timers include exact certificate checking and conic
parameter/solve/residual work; imports and shared input construction are excluded.

The earlier 29.88 ratio measured different dimensions and inputs against a
one-shot conic formulation. The change from 29.88 to 9.26 cannot be attributed
solely to caching: this is not a matched ablation of reuse. No solver settings,
tolerances or statuses were changed after the new results appeared.

## Public applications and feedback

A separate bounded screen evaluated eight public targets. Most did not satisfy
the oracle's contract. Conditional minimax regret, confidence-interval coverage,
general covariance bugs and arbitrary quadratic matrices are different problems;
no claim of solving them is made. See [the source screen](PUBLIC_SCREEN.md).

Two already-public binomial examples in Will Fithian's Berkeley Stat 210A reader
were checked separately under a second small frozen protocol: two oracle calls,
two exact references and 170 direct binomial-outcome terms. The risks 1/81 and
1/100 matched. This is known-example verification, not a new theorem or part of
the 48-scenario synthetic cohort. A current denominator typo was also verified:
the intended (X+2)/20 at n=16 has constant risk 1/100, whereas the printed nonlinear
(X+2)/(X+4) gives risk 1/4 at p=0. The latter boundary check does not use the
oracle, because the nonlinear formula is outside its contract. A concise correction
is submitted through the course repository; actual status is recorded separately
in [external feedback](EXTERNAL_FEEDBACK.md). No maintainer acceptance is presumed.

## Verification, rights and limits

Before the formal queue, 68 package tests passed, including new calendar, grid,
tie, comparator and strict-JSON evidence-preservation controls. The comparator's
development tests exposed an `optimal_inaccurate` status on a handwritten toy;
only an overstrict test expectation was corrected, not solver tolerances. Before
freeze, nonfinite-failure serialization was repaired and regression-tested.
The final freeze retains all 15 operative files. These changes occurred before
formal results; there was no post-result protocol or method repair.

Independent saved-evidence verification reconstructs candidates, certificate
bounds, grids, numerical residuals, choices and summary counts without rerunning
the optimization queue. Internal AI-agent review and CI are not institutional
replication, peer review or a second timed experiment. See the release receipt
for the actual completed environment checks.

All new implementation and synthetic content are original and under the package
MIT license. No course source, text paragraphs, figures or implementation were
copied. The public teaching example is attributed to Will Fithian and the
[CC BY 4.0 reader](https://github.com/berkeley-stat210a/fall-2026/blob/88ca90db1c5fb7d337890a3a59d274d719c551d9/license.qmd).
The known estimator, risk identity and conic methods retain the paper's attribution.
No new dependency, private case, patent novelty or freedom-to-operate claim is added.

Remaining work is application-driven: obtain a legitimate fixed-count consumer
with verified model assumptions and meaningful decision costs. These exposed
inputs are now consumed evidence, not a future holdout set. There is no automatic
budget for a larger matrix, retuning the comparator, or new model inference.
