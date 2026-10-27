# Exact Risk Oracle

An exact rational worst-risk calculator with an independently checkable certificate
for fixed centered affine estimators of weighted independent binomial probabilities.

Read the [English methods paper](paper.md) or [six-page PDF](paper.pdf).
This is a specialized implementation and research artifact, not a claim of a new
estimator, first-ever polynomial tractability, patent novelty, or deployment validation.
See [source attribution and rights](SOURCE_AND_RIGHTS.md).

## What it does

For nonnegative rational vectors `d,v`, solve
`max_{x in [-1,1]^k} (d.x)^2 - sum(v_i*x_i^2)`.
Return a maximizing witness and nonnegative diagonal loading. A separate checker
proves an upper bound by weighted Cauchy-Schwarz and verifies that the witness
attains it. The exact solver and checker require only Python's standard library.

For the statistical interpretation, counts are fixed/exogenous, observations are
independent binomial variables, weights are known, and coefficients obey `0<=a<=w`.
Zero-count strata require `a=0`. The checker does not establish these assumptions.

```python
from fractions import Fraction as F
from oracle import from_estimator
from check_certificate import verify

d, v, answer = from_estimator([F(1,2), F(1,2)], [1,1], [F(1,3), F(1,6)])
assert answer.risk == F(7,108)
assert verify(d, v, answer.to_dict())
print(answer.to_dict())
```

## Recorded evidence

One frozen original synthetic run, no model calls and USD 0 external inference:

- 148/148 exact certificates verified.
- 128/128 independently implemented exhaustive-face optima matched.
- 16/16 direct binomial expectations matched.
- 6/64 complete quarter grids understated continuous risk.
- 56/56 conic baseline records agreed numerically; 54 actual Clarabel solves.
- Eight shared scale cases: median general-conic / (exact+check) time ratio 29.88.

The conic baseline also succeeded. Timings include conic construction and
canonicalization; warm cached programs and other optimized formulations were not
compared. One-machine timings do not establish a universal speedup. Large-scale
exact-only cases have no measured conic comparison. Full results and limitations
are in [the protocol](PROTOCOL.md), [summary](results/summary.json), and
[receipt](results/receipt.json). All generated inputs and certificates are retained.

## Verify without repeating the benchmark

From this repository directory, Python 3.12 or later:

```sh
python -m unittest discover -s tests -v
python verify_saved.py
```

The independent saved-evidence checker uses no optimization dependency and does
not repeat the benchmark. The 25 original development tests remain in the frozen
record; any later verifier tests are additional publication checks.

PDF rebuild (separate optional dependency):

```sh
python -m pip install -r requirements-render.txt
python build_paper.py --output build/rebuilt.pdf
```

The ordinary runner refuses to overwrite `results/RUN_GUARD.json`. Reproduce the
benchmark only in a separate copy with a fresh results location prepared by the
researcher, preserving the original evidence. Install `requirements-benchmark.txt`
for its optional CVXPY/Clarabel baseline. A new run has new timings and is not the
recorded Windows run. Never describe saved-byte CI as a second benchmark execution.

## Research handoff

[RESEARCH_CARDS.md](RESEARCH_CARDS.md) records the three proposed directions,
why two were not selected, and explicit falsifiers. The most useful next study is
whether exact risk changes a real sampling-design decision under the same budget.
That study is **NOT PERFORMED**. No claim of improved sensing, field performance,
or model correctness follows from the present software result.

Original code, text and synthetic data: MIT. No private conversations, personal
case counts, user trajectories, external source code or model weights are included.
The full font license accompanies the subset-embedded PDF. Dependencies are not
vendored and retain their own licenses.
