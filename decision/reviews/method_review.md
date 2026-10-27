# Prospective sampling-decision methods review

Date: 2026-10-27. Internal independent AI-agent review of the design before
evaluation. This document does not report experimental outcomes or establish
external peer review. No evaluation fixture has been run by this reviewer.

## Scope and final prospective design

The new question is whether replacing a finite probability grid with a continuous
risk certificate changes a sampling allocation for the better. A smaller error in
a reported risk maximum is not itself a better allocation. The original 148
solver-validation cases and the earlier reserve-one audit are consumed development
evidence; neither is a fresh evaluation set here.

The reviewed plan contains 48 original synthetic scenarios: dimensions
`k in {2,3,4}`, fixed shrinkage constants `c in {0,1/2,1,2}`, and four calendar
replicas. The predeclared new generator seed is 271027117. Each scenario draws
positive integer weights in 1..9 and normalizes them exactly. No generation step
may evaluate risk, search for a grid failure, or reject a difficult outcome.

Replica power budgets are `(2,3,4,4)`, with horizon `B+2` and exactly `B` powered
slots. Availability is fixed before observations. Replica 0 allows every channel;
replica 1 uses nonempty random subsets; replica 2 uses subsets of size `k-1`;
replica 3 repeatedly allows one fixed channel. The last is a restricted-coverage
control, not a guaranteed null-effect case: it still permits 0..B observations of
that channel. Every powered slot may be idle or sample one eligible channel.
There is no carryover, outcome-adaptive action, or hidden extra resource.

Enumerate every reachable count vector and retain a deterministic representative
schedule for audit. Duplicate schedules producing the same counts must not count
as additional decisions, because the model's risk depends on counts alone. All
three evaluators receive precisely this candidate set. The maximum of
`choose(B+k,k)` candidates per scenario gives at most 1,344 candidates in total;
three timing repetitions give at most 4,032 evaluations per method. An independent
full-face reference runs once per candidate, at most 1,344 calls. The wall budget
and exact interruption semantics must appear in the final frozen protocol.

For each candidate, the estimate is fixed prospectively by
`a_i = w_i*n_i/(n_i+c)`, with `a_i=0` whenever `n_i=0`; for `c=0` and observed
strata this reduces to `a_i=w_i`. The zero-count branch avoids undefined `0/0`.
The design chooses counts before any Bernoulli outcome. Its guarantee assumes
known weights, independent Bernoulli trials, constant within-stratum probabilities,
and exogenous availability. No application or missingness mechanism is validated
merely by satisfying the arithmetic contract.

## Fair comparisons and interpretation

1. The coarse grid is the complete product of probabilities
   `{0,1/4,1/2,3/4,1}`. Reduction to nonnegative transformed coordinates
   `x in {0,1/2,1}` preserves its maximum because `d>=0` and replacing `x` by
   `abs(x)` cannot reduce the objective. This is an algebraic optimization of the
   same grid, not a smaller or outcome-selected baseline. Exact rational grid
   arithmetic makes equality and tie sets explicit.
2. The exact method must return a valid certificate for every candidate and agree
   with the independent full-face enumeration. The reference must not call the
   oracle or reproduce its one-dimensional breakpoint route.
3. The general comparator is a reusable, parameterized conic program with a fixed
   documented tolerance. Its build cost, initial cold pass, and later warm passes
   are reported separately. Retaining the problem across candidates is necessary
   to address the main limitation of the previous one-shot comparison. Returned
   vectors must be independently checked numerically; solver success alone is
   not a mathematical certificate.
4. A scenario with any unaccepted conic candidate must be retained as incomplete
   for that comparison. Selecting only from its successful candidates silently
   changes the feasible decision set and is not allowed. Numerical near-optimal
   sets must use a tolerance fixed before evaluation, not exact results to tune
   a favorable threshold.
5. Rotate method ordering deterministically across scenarios/repetitions if
   feasible. Keep all timing observations, including cold starts and outliers.
   Repetitions of the same input are timing replicates, not additional independent
   decision problems. Do not extrapolate a ratio from these small dimensions to
   large deployments, different estimators, or all optimization libraries.

## Decision endpoint and falsifiers

For candidate `j`, let `R_j` be its certified continuous worst-case risk, and let
`R* = min_j R_j`. The decision regret is exactly `R_selected-R*`.

Report the common deterministic lexicographic selection, every exact grid tie,
the numerical conic near-optimal set, and minimum/maximum certified regret over
each tie or near-tie set. Report whether the exact minimizers overlap each set.
Do not describe a harmless choice between exactly tied designs as an improvement.

The primary finite decision-gain witness requires
`min(R_j for j in grid_minimizers) > R*`: every grid-minimizing choice is
suboptimal under exact risk. A lexicographic grid selection with positive regret
but an optimal alternative in the same grid tie set is a tie-dependent secondary
finding, not the primary witness. No positive regret in the suite means that
decision improvement was not demonstrated in this suite, even if grid values
understate risk. A single witness establishes existence within this declared
finite task family, not a population failure rate or typical deployment gain.

The conic method solves the same optimization problem, so it should usually make
an equally good decision. Agreement is positive evidence for a valid strong
baseline. A cost advantage over it may coexist with no statistical decision
advantage. If caching removes the timing advantage, the original one-shot result
remains historical evidence but a reusable-workload speed claim fails.

Any oracle/reference mismatch, invalid certificate, incorrect feasible-set
enumeration, changed frozen input, or result-dependent threshold invalidates the
corresponding positive claim. Numerical failures, timeouts, missing rows and
partial comparisons remain visible; they are not converted into attacks won or
silently rerun. New private data, model inference, and external inference fees
are outside this experiment.

## Review disposition

The latest idle-allowed design and `decision/PROTOCOL.md` are methodologically
suitable for a small falsifiable decision study. The protocol specifies a
900-second between-call wall stop, keeps cold and warm timings separate, rotates
method order by pass, and requires every numerical comparison to pass before a
positive comparative decision claim. The remaining uncertainty is the empirical
result, not an assumed benefit.

The independently authored `tests/test_decision_design.py` passed all 16 methods
before evaluation, using only handwritten controls. It compares dynamic-program
candidate generation with complete schedule enumeration, the symmetry-reduced
grid with the full signed grid, and explicitly distinguishes tie-dependent from
tie-robust regret. Additional controls cover empty power calendars, no carryover,
idle choices, duplicate schedules, restricted coverage, zero-count uncertainty,
fractional shrinkage, incomplete arrays, invalid counts and malformed calendars.
Command: `python -m unittest discover -s tests -p test_decision_design.py -v`
from the standalone package directory. The observed run took 0.016 seconds.

This reviewer has not generated or run the formal evaluation fixture. Approval
remains contingent on the final pre-execution freeze, comparator checks and the
runner enforcing its written stop and evidence rules.

