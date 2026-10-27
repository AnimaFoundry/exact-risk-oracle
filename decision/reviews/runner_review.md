# Pre-execution decision-runner review

Date: 2026-10-27. Reviewer: separate AI agent implementing the reusable conic
comparator. This is an internal code/protocol review, not external peer review.
No formal input risk, optimizer call, new experiment, or old frozen queue was run.

## Scope

Read `decision/run.py`, `decision/scoring.py`, `decision/PROTOCOL.md`,
`decision/design.py`, generator source and handwritten design/scoring controls.
Checked budget enforcement, repeat/reuse semantics, timing, ties and negative
result handling. Formal input values and outcomes were not inspected.

## Finding requiring pre-freeze repair

The conic comparator retains raw normalized vectors on numerical nonfinite
outputs. The runner serializes both a row and its exception's `partial_row`
with `allow_nan=False`. If a returned vector contains NaN or infinity, the first
serialization raises, and saving `failure.json` raises again on the same value.
This can prevent the durable failure, setup and final receipt from being saved.

Before freezing, encode nonfinite observations explicitly as strings in the
evidence layer, while retaining numerical rejection and never using their
encoded forms as accepted scores. Alternatively, have the comparator emit
explicit nonfinite strings on the rejected raw-vector fields. Include a
handwritten regression control for durable failure serialization. This is an
evidence-preservation defect; it does not suggest acceptance of nonfinite output
or justify a numerical retry.

## Checks satisfied by the reviewed design

- The fixture has at most 48 scenarios / 1,344 unique count allocations; three
  complete passes cap each method at 4,032 evaluations. Reference enumeration
  is once per unique allocation. The freeze records actual counts and hashes.
- The 900-second check is explicitly between calls, not a hard mid-solver
  timeout. Clarabel separately has a 200-iteration cap. Exclusive guard creation
  prevents replay, and ordinary exceptions preserve a current partial row.
- One `ReusableConic` object is constructed per scenario and reused across all
  candidates and all three passes. Parameters and dimensions remain fixed in
  one DPP problem; no hidden warmup, retry or oracle-derived initialization.
- Shared candidate/input preparation is outside all method timers. Exact
  solving includes certificate verification; conic timing includes parameter
  update, solve and residual audit. The separately measured build cost is added
  only to first-pass batch timing. First compilation remains in the first call.
- Ordering rotates over the three passes; these are technical repetitions of
  the same scenarios, not independent statistical samples. Warm batch ratios
  are compared on the complete identical candidate set.
- Exact/grid ties retain their complete minimizer sets. Tie-robust gain uses
  the **best** regret among grid minimizers, preventing lexicographic artifacts
  from being reported as unavoidable decision gains.
- Conic decisions use only conic numerical values and a fixed near-tie tolerance.
  One rejected conic value makes that scenario numerically inconclusive; failed
  records are not silently removed to choose among a more convenient subset.
- The overall conic/speed gate requires all required numerical outputs accepted
  and within the frozen error tolerance. A conic failure cannot be labelled an
  exact-solver speed victory, and does not erase an independently proven
  grid-versus-exact decision difference.
- No risk outcome is used by the synthetic generator or candidate enumeration.
  The full feasible count set includes idling; coefficients are fixed from the
  scenario's predeclared estimator rule.

## Interpretation limits

The cohort is tiny and synthetic (dimension 2--4, observation opportunities at
most four). It can show finite decision examples or their absence, but cannot
establish operational prevalence, general speedups, or physical energy benefits.
Existing code plus certificate soundness supports correctness under the stated
fixed independent-binomial contract; no statistical assumption is validated by
the software. A post-run independent saved-evidence audit remains required.

Status at this review: one evidence-serialization repair requested before freeze;
no other blocking protocol/runner defect identified in this bounded inspection.

## Repair verified before execution

The parent added recursive `saved_safe` evidence encoding before row append/write
and in the JSON dump helper. NaN/positive infinity/negative infinity are retained
as explicit `nonfinite_float` marker objects; acceptance flags and absent risk
values are unchanged. A handwritten test covers all three markers and strict
JSON serialization. I inspected the revised runner/test; the original finding
is resolved. No remaining blocker identified before freeze. The earlier finding
is retained above rather than rewritten out of the development history.
