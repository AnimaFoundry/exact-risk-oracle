# Independent saved-evidence review

27 October 2026. Internal separate-agent review; not external replication or
peer review. The reviewer implemented the reusable conic comparator and then
wrote a new standard-library evidence checker that imports none of the solver,
original checker, generator, design, runner, scoring or CVXPY modules.

The replay passed on the final saved cohort. It checked all 15 frozen file hashes,
freeze/guard/run chronology, receipt hashes and recorded environment consistency.
It independently enumerated complete action schedules for all 48 calendars and
recovered exactly the saved 753 feasible count vectors and canonical schedules.
It reconstructed the estimator coefficients from counts and weights, checked all
2,259 exact certificates using upper-bound attainment, and recomputed the complete
signed five-point probability grids for all 753 unique allocations.

The 753 saved independent-reference values and their attaining points agree with
the checked certificates; the reference optimizer itself was not rerun. Every
conic record was checked against input-derived scaling, saved normalized loading
and epigraph vectors, residuals, acceptance status and object reuse/call indices.
The complete decision tables, exact ties, numerical near sets, regret values,
status counts, and timing aggregation reproduce the saved summary exactly.

## Result interpretation

There is one tie-robust grid decision loss in 48 scenarios (`decision-023`). Its
unique grid-selected candidate has certified risk `466/12675`, while the exact
and accepted conic selection attain `1373/38025`. The exact regret is `1/1521`.
All 47 other scenarios have no grid-tied choice with positive regret. This is a
finite existence example, not a prevalence estimate or general decision benefit.

The stronger reusable comparator produced 2,205 `optimal`, 12
`optimal_inaccurate`, and 42 algebraic-zero records. All numerical risk errors are
small (maximum approximately 1.1473e-10), but the frozen acceptance rule excludes
the 12 inaccurate statuses. Those outputs and warnings are retained. The conic
comparison gate and speed-claim gate correctly remain false; the descriptive
timing ratios cannot be promoted to a successful speed comparison or a claim
that the conic solver computed materially wrong risks.

The independent checker has 14 handwritten post-freeze mutation tests, covering
altered certificates, candidate omission, grid values, numerical statuses,
rescaling, solver-call counts, ties, nonfinite evidence and duplicate JSON keys.
No formal outcome was changed to make a test pass. The earlier pre-execution
nonfinite serialization defect was repaired before freezing and is retained in
the runner review history.

Continuous optimizer calls during this replay: 0. Model calls: 0. External API
cost: 0. Saved timings were recalculated as aggregates, not remeasured. The
checker is post-freeze verification tooling, not a prospectively frozen outcome
analysis or independent institutional replication.
