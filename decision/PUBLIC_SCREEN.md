# Bounded public-problem screen — 27 October 2026

Screen completed at 2026-10-27T06:54:59Z. Eight concrete targets were evaluated.
This is a relevance screen, not evidence that all public problems were searched.
No messages, issues, pull requests, or emails were sent by this screening agent.
No model inference, private data, source archive, or external inference fee was
used. General web searches located candidates; GitHub targets were read through
the connected GitHub API, including current issue state rather than just search
snippets. The sixth and seventh targets were read on the original question site.

## Applicability contract

The existing oracle solves the continuous box maximum
`(d dot x)^2 - sum(v_i*x_i^2)` for nonnegative rational `d,v`, or the documented
fixed centered affine estimator of independent binomial strata with known weights
and exogenous fixed counts. A shared word such as "rank one", "stratified", or
"certificate" does not establish applicability. Conditional minimax regret,
confidence intervals, correlated covariance estimation, general quadratic
matrices, and outcome-dependent allocation do not automatically reduce to it.

## Eight targets and decisions

| # | Primary target | State observed | Fit and decision |
|---|---|---|---|
| 1 | [cmrdesign applied-user feedback #10](https://github.com/juancyamin/cmrdesign/issues/10) | OPEN; updated 2026-08-05T10:49:46Z; zero comments | Closely related application, but CMR minimizes regret over a pilot-derived variance rectangle. Our fixed-estimator worst MSE is a different objective. Do not present the oracle as a replacement, faster implementation of CMR, or bug fix. Not selected for unsolicited results. |
| 2 | [mt-metrics-eval seed bug #28](https://github.com/google-research/mt-metrics-eval/issues/28) | OPEN; updated 2026-09-28T08:22:03Z | Actual issue is seed zero/global RNG state in stratified selection. No worst-risk optimization. OUT_OF_SCOPE. |
| 3 | [antenna stratified sampling #1554](https://github.com/RolnickLab/antenna/issues/1554) | OPEN; updated 2026-10-22T00:19:46Z | SQL sampler registry, equal/proportional quotas, reproducibility. No specified binomial risk objective or compatible statistical contract. OUT_OF_SCOPE. |
| 4 | [precise Tyler covariance #85](https://github.com/microprediction/precise/issues/85) | OPEN; updated 2026-09-25T01:13:14Z | Rank-one collapse is a recursive covariance/SPD issue. The box-risk solver cannot repair it. OUT_OF_SCOPE. |
| 5 | [RealRooted quadratic PSD rays #1991](https://github.com/PerAlexandersson/RealRooted/issues/1991) | OPEN; updated 2026-10-25T09:36:30Z | A general matrix-polynomial Gram/LMI formalization over the half-line, not this rank-one box objective. OUT_OF_SCOPE. |
| 6 | [Cross Validated: confidence intervals at zero in a stratified survey](https://stats.stackexchange.com/questions/629809/r-confidence-intervals-for-proportion-of-zero-in-a-stratified-random-sample) | Existing question and answer; asked 2023-10-27 | Wants confidence coverage with survey weights/finite-population sampling and possibly clusters. Exact MSE is not an answer to this question. OUT_OF_SCOPE; no answer posted. |
| 7 | [Mathematics Stack Exchange: showing an estimator is minimax](https://math.stackexchange.com/questions/2886255/showing-that-estimator-is-minimax) | Existing question and answer; asked 2018-08-17 | Loss is relative squared error `(1-estimate/p)^2`, not ordinary squared error. OUT_OF_SCOPE; no answer posted. |
| 8 | [Berkeley Stat 210A: public binomial-estimation example](https://stat210a.berkeley.edu/fall-2026/reader/estimation.html) and [current source](https://github.com/berkeley-stat210a/fall-2026/blob/88ca90db1c5fb7d337890a3a59d274d719c551d9/reader/estimation.qmd#L355) | Current public source and rendered page contain a denominator typo; all issue and PR collections were empty at the screen time | Correct centered estimator is directly compatible with k=1 oracle. The mistyped nonlinear estimator is not. SELECTED as one narrow documentation correction, subject to parent verification and a final duplicate check. This is a known theorem/typographical correction, not a new mathematical solution. |

The count refers to evaluated concrete targets, not every search hit. Irrelevant
search snippets were not promoted into targets or downloaded as datasets.

## Selected concrete finding: Berkeley denominator correction

Repository: `berkeley-stat210a/fall-2026`; current main commit
`88ca90db1c5fb7d337890a3a59d274d719c551d9` (commit date
2026-10-06T14:17:42Z), public and unarchived, issues enabled. Source file
`reader/estimation.qmd` blob `7ba655a73de975663f95bab7d476e0e10910b9dd`.

The source defines the centered estimator using denominator `n+4` at lines 136
and 337, but the final minimax sentence at line 355 instead uses `X+4`.
The live Fall 2026 page repeats the latter in its minimax paragraph. The older
[author-hosted lecture](https://www.stat.berkeley.edu/~wfithian/courses/stat210a/models.html)
also contains the discrepancy. Only the current public source is proposed as
the report target; do not send duplicate reports to all historical copies.

For fixed `n=16`, the intended expression is `(X+2)/20`. Direct calculation gives

```text
Var((X+2)/20) = 16*p*(1-p)/400
Bias((X+2)/20) = (2-4*p)/20
MSE = [16*p*(1-p) + (2-4*p)^2]/400 = 1/100.
```

The oracle input is `weights=[1]`, `counts=[16]`, `coefficients=[4/5]`.
It has `d=[1/5]`, `v=[1/25]`, and expected exact risk `1/100`, with zero objective
and zero loading; any `p` attains the constant risk. This expected result was
derived before executing any new public-example code. At initial screening it
was unexecuted; the separately authorized bounded verification below was then run.

By contrast, with the printed expression `(X+2)/(X+4)`, at `p=0` one has `X=0`
almost surely and the estimate equals `1/2`, so MSE is `1/4`. If an open parameter
interval is intended, the risk tends to `1/4` as `p` tends to zero. This elementary
boundary check suffices; the oracle must not be called with a false mapping of
the nonlinear printed expression. Confirming constant risk does not alone prove
minimaxity over all estimators; that broader result is already treated in the
course's minimax chapter and is not a novelty claim here.

Other displayed estimators offer optional teaching checks: `X/16` maps to `a=1`
and worst risk `1/64`; `(X+1)/18` maps to `a=8/9` and worst risk `1/81`.
These are source-motivated known examples, not new untouched synthetic evaluation
cases, not evidence for decision gains, and not performance benchmarks. The
third shifted estimator `(X+1)/16` falls outside the centered contract.

## Venue, rights, and bounded draft

The repository README identifies it as the official course-site source. The
root and `.github/` inventories contain no CONTRIBUTING file or issue template.
The README says not to expose solutions to assigned work; this report concerns
an already-public reader formula and its internal inconsistency. No assignment,
solution, exam, or private companion repository was inspected.
The course syllabus routes technical discussion away from email; use the public
repository issue, not an unsolicited mathematical email.

[license.qmd](https://github.com/berkeley-stat210a/fall-2026/blob/88ca90db1c5fb7d337890a3a59d274d719c551d9/license.qmd)
declares CC BY 4.0. No course source, lecture paragraph, plot, or code is proposed
for copying into the MIT solver package. Any small original worked example must
attribute Will Fithian and link the source; report it as a verification of a
known example. No implementation novelty or patent conclusion follows.

Suggested one-issue title:

> Denominator typo in the n=16 minimax example in reader/estimation.qmd

Suggested self-contained body (parent to verify and post, if still current):

```markdown
In [reader/estimation.qmd, line 355](https://github.com/berkeley-stat210a/fall-2026/blob/88ca90db1c5fb7d337890a3a59d274d719c551d9/reader/estimation.qmd#L355),
the final minimax sentence writes `(X+2)/(X+4)`. Should the denominator be
`n+4`, matching the earlier definitions at lines 136 and 337?

For `n=16`, the intended estimator `(X+2)/20` has squared-error risk

`[16 p(1-p) + (2-4p)^2]/400 = 1/100`,

constant in `p`. The printed `(X+2)/(X+4)` instead has risk `1/4` at `p=0`
(or that limit as `p` tends to zero), because then `X=0` and its output is `1/2`.

Suggested correction: `\frac{X + 2}{X + 4}` → `\frac{X + 2}{n + 4}`.
The same discrepancy is visible on the published Fall 2026 estimation page.
```

This asks for a specific correction rather than advertising our package. A link
to a small saved validation can be added if useful after it is actually run.
Do not claim maintainer agreement, adoption, or resolution before a response.
The parent should check for intervening fixes/duplicate issues immediately before
posting, retain the returned issue URL/UTC, and inspect actual feedback later.

## Closest non-selected project: cmrdesign

Primary files read at main `bdcec68f5fe79ebc01228a88f4cac36044c2b9b2`:
README, CONTRIBUTING, LICENSE, docs/methods.md, docs/faq.md,
spec/api_review.md, spec/math_spec.md, python/src/cmrdesign/stratified.py,
python/src/cmrdesign/allocation.py, examples/python/05_stratified.py, and
.github/ISSUE_TEMPLATE/alpha_feedback.yml. MIT license is explicit.

The package separates variance-confidence construction and conditional minimax
regret allocation, includes a full-rectangle closed form, and audits realized
integer shares. Its existing feedback invitation is genuine, but the inspected
behavior does not present a demonstrated defect that our oracle fixes. A future
proposal would need a justified fixed centered-estimator consumer; adding bias
or missing strata changes the objective and must not be sold as a drop-in speedup.
No issue or comment was sent there.

## Result boundary

One actionable, narrow public documentation finding was located; no directly
applicable unsolved general optimization issue was established. The other seven
targets remain negative relevance evidence. A verified correction is useful but
does not count as a new solver capability, independent demand validation, an
external research adoption, or a second original invention.

## Separately authorized public-example verification

The parent authorized exactly two oracle calls, two exact face references, and
170 direct binomial-outcome summands at five fixed probabilities. This is a
separate budget from the synthetic sampling-decision experiment and is now
consumed. No retained synthetic decision inputs were read or used by this agent.

- Freeze UTC: `2026-10-27T06:57:19.262723Z`.
- Run UTC: `2026-10-27T06:57:23.714817Z` to `2026-10-27T06:57:23.752127Z`.
- After-import elapsed time: 0.0022489000111818314 seconds; not a speed benchmark.
- Expected worst risks `1/81` and `1/100` both matched exact polynomial maxima,
  the oracle certificates, and independently enumerated face optima.
- All ten direct expectations matched the risk polynomials. The second
  polynomial was exactly constant, independently of this five-point diagnostic.
- The nonlinear typo's `p=0` risk `1/4` was evaluated directly; no oracle mapping
  or claim of its full global maximum was made.
- Four frozen source hashes unchanged. No retry, model call, or external fee.
- Saved-evidence verification passed without new oracle/reference calls.

Files under `aim/exact_risk_oracle/decision/`:

| File | SHA-256 |
|---|---|
| public_examples.py | e21226a62f1edbf46bee6719fddeea483c922de9ba16281403faeaead591556a |
| public_examples_protocol.json | 4cdbc589045d0c7a85e6754c272cfb077fbc96dc1c60efd77b2e18d7dc1755ad |
| public_examples_result.json | 764d46a503732ad8f3b1b0d1fe3925c43897e0f008b174a0f39440c335066e1f |

`public_examples_guard.json` preserves the start and prevents replay. Use
`python decision/public_examples.py --verify` from the standalone package to
check saved evidence. Do not delete the guard or count this known example as
new held-out evaluation data. The standalone issue draft is
`BERKELEY_ISSUE_DRAFT.md` in this internal evidence directory. No post has been
made by this screening agent.
