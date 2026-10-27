# Independent review of the saved sampling-decision results

Date: 2026-10-27. Internal AI-agent mathematical and interpretation review.
This is not external peer review, field replication, or another optimizer run.
The reviewer read the frozen protocol, scoring code, raw saved rows, original
synthetic calendars, freeze and run receipts. No model or optimization request
was issued. All checks below recompute arithmetic from saved evidence only.

## Evidence integrity and scope

The operative freeze was created at `2026-10-27T06:57:28.999651Z`, before the
recorded queue start `2026-10-27T06:57:43.863842Z`. All 15 named source, protocol,
fixture and test hashes still match the freeze. The queue completed at
`2026-10-27T06:57:58.752425Z`; the runner's after-import measured wall interval
was 14.41067880007904 seconds. Three passes over 753 distinct candidate
allocations in 48 scenarios produced 2,259 rows. These are 48 decision scenarios,
not 2,259 independent decision experiments.

The reviewer reconstructed each row's `a,d,v` from the raw normalized weights,
fixed shrinkage constant and candidate counts. Independent direct Fraction
arithmetic checked nonnegative loadings, box feasibility, the diagonal-bound
ratio, equality between the attaining witness and upper bound, and the risk
identity on all 2,259 saved certificates. Every first-pass risk also matches
its saved independent face-reference result: 753/753. This did not re-execute
the reference optimization. Saved grid witnesses attain their recorded values
and never exceed the certified continuous risk.

The frozen protocol explicitly separates a grid decision witness from successful
completion of the full conic comparison. Earlier prospective-review wording about
requiring all numerical comparisons before a positive comparative claim must be
read subject to that final, pre-execution distinction. No post-result weakening
of the operative frozen gate is necessary or justified.

## One exact decision witness, with 47 null comparisons retained

Only `decision-023` has a grid-minimizing allocation whose certified risk exceeds
the best feasible risk. Its grid optimum is unique, so the result cannot be
explained by an unfavorable tie-breaking rule. All other 47 scenarios have zero
regret for every grid-minimizing candidate. There are 68 first-pass candidate
grid understatements, but most do not change the allocation decision; this
distinction is central to the study.

The witness has weights `(6/13,5/13,2/13)`, shrinkage `c=1/2`, and four unit-energy
sampling opportunities across six slots. Both relevant allocations are feasible
under the same frozen calendar, using all four available observations:

| Evaluator choice | Counts | Reported grid risk | Certified continuous risk |
|---|---|---|---|
| Grid's unique minimum | `(2,2,0)` | `97/2704` | `466/12675` |
| Exact and accepted conic choice | `(2,1,1)` | `1373/38025` | `1373/38025` |

Their exact risk difference is `1/1521`. Relative to the grid-selected plan's
certified risk, the reduction is `25/1398`, approximately 1.78827%. This is a
reduction in the mathematically defined continuous worst-case mean squared error,
not an observed reduction in real-world defects, a sampled empirical MSE, or a
population-average effect.

For `(2,2,0)`, the stored attaining transformed parameter is
`x=(5/18,1/3,1)`, corresponding to `p=(23/36,2/3,1)`. The grid uses its own maximum
at `x=(1/2,1/2,1)` and misses that interior worst case. For `(2,1,1)`, the zero
transformed vector attains the exact bound with zero diagonal loading. The
certificate proof covers the entire probability box for each allocation.

The accepted conic comparator also chooses `(2,1,1)` on all three passes for
this scenario. Therefore this result supports an exact-versus-coarse-grid
decision distinction; it does not show superior statistical decisions relative
to a correctly solved conic formulation.

The defensible conclusion is existence of one decision improvement in the
declared finite synthetic family. Reporting `1/48` as an estimated deployment
failure probability, or extrapolating the 1.78827% effect to typical applications,
would exceed the evidence.

## General-conic acceptance failed its prospective strict gate

The raw status counts are 2,205 `optimal`, 12 `optimal_inaccurate`, and 42
algebraic zero-bias results. There were 2,217 actual conic solves. The strict
acceptance count is 2,247/2,259, so `conic_comparison_gate` is false. The twelve
unaccepted records are four distinct candidate inputs repeated three times:

| Scenario | Candidate index | Counts | Exact risk |
|---|---:|---|---|
| decision-010 | 2 | `(0,2)` | `1/16` |
| decision-046 | 16 | `(0,2,0,1)` | `11449/63504` |
| decision-046 | 19 | `(1,0,0,0)` | `361/1764` |
| decision-046 | 30 | `(2,0,0,1)` | `529/3969` |

All twelve have a recorded residual audit of `accepted: true`; their risk errors
are below `1e-14`. They fail the higher-level rule because their returned status
is `optimal_inaccurate`, whereas the frozen acceptance rule requires `optimal`.
Across all records, the maximum absolute risk discrepancy is
`1.147292538750122e-10`, comfortably below the separately declared `1e-7` error
threshold. This is not evidence that twelve allocations were incorrectly chosen.
It is evidence that the requested strict status-and-residual contract was not
fully met. Neither the status requirement nor the result may be changed after
inspection.

The two affected scenarios correctly receive
`INCONCLUSIVE_NUMERICAL_FAILURE` rather than a decision selected from a reduced
set of accepted candidates. Their summary field `conic_choice_stable: false`
means a fully accepted decision is unavailable; it must not be described as
observed numerical choice instability. The other 46 scenarios have accepted
choices that remain optimal under the exact risk scoring.

## Timing is descriptive, not a successful speed claim

The retained per-scenario warm ratio summary has median
`9.258568559921835`, minimum `5.116156472725131`, and maximum
`16.173164255280113`; cold-to-reused median is `13.247541122028522`. The warm
summary first takes each scenario's median over passes 2 and 3, then summarizes
those 48 ratios. Build time is included in the cold batch and not charged again
to later passes. All measured scenarios, including the two conic-incomplete
ones, remain in the descriptive timing report.

Because the conic comparison gate failed, `speed_claim_eligible` and
`speed_2x_gate` are false. The study must not claim that it passed a reusable-
solver speed superiority test, even though the stored descriptive ratios exceed
two. Excluding the failing scenarios after inspection to manufacture a successful
gate would change the prespecified analysis.

The earlier approximately 29.88 ratio involved a different, one-shot formulation
and a different dimensional/input cohort. The present approximately 9.26 value
cannot be used to isolate a causal effect of caching alone. Neither value is a
universal speed factor or a cross-machine result.

## Disposition and next boundary

The saved evidence supports publication as a mixed-result companion: a rigorous
single grid-decision counterexample, 47 no-gain comparisons, exact-method
correctness on the new cohort, and an unsuccessful strict three-way conic
acceptance gate. No new generation, retries, threshold relaxation, private data,
model inference, or external inference fees were used in this review.

Before any subsequent numerical investigation, preserve this completed cohort
and guard. New work should distinguish status handling, the mathematical
formulation and runtime behavior, without asserting a solver defect from this
evidence alone. Any public application must separately establish its statistical
assumptions and decision relevance; synthetic correctness does not establish
external demand or deployment utility.
