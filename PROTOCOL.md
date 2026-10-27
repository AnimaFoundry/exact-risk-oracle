# Exact continuous risk oracle: finite validation protocol

Version 1, 27 October 2026. New original synthetic inputs. The earlier
energy-missingness audit and its frozen files remain unchanged. This is
mathematical/software validation, not a sample of deployments or model behavior.
The toy examples already used during derivation are development data.

## Question and prospective decision rule

Can a dedicated rational threshold algorithm provide a continuous worst-risk
value, an attaining parameter witness, and an independently checked exact upper
bound, with useful computation cost compared with a maintained general conic
solver? It does not propose a new estimator or claim new polynomial tractability.
Its scope is fixed, non-expansive centered affine estimators with independent
binomial strata and exogenous fixed counts. Statistical assumptions are inputs,
not facts established by the certificate.

Mandatory correctness gates: all 128 new small cases exactly match independent
exhaustive face/KKT enumeration; every produced certificate passes the independent
weighted-Cauchy checker; the first 16 cases also match direct binomial expectation
at the witness. Any mismatch stops a positive correctness claim and is retained.

Operational-value gate: exact certificates must pass, at least one of the 64
five-point-per-coordinate grids must strictly understate continuous risk, and
median solver-plus-verifier time must be at least twice as fast as the general
SOCP implementation on the eight shared scale cases. This is a declared engineering
criterion, not a significance test or a claim about all hardware/solvers.
An equivalent previously published algorithm defeats an algorithmic novelty
claim; a useful implementation can still merit a methods paper. No global
patent novelty or freedom-to-operate conclusion is made.

## Inputs, controls, and budget

- Generator uses a fixed published seed, 271027031, with no outcome-driven search.
  The generated JSON is hashed before any validation evaluation.
- 128 small cases: first 64 have k=1..5; next 64 k=1..6. Positive integer raw
  weights are normalized; n=0..3 for the first 16, otherwise 0,1,2,5,13;
  shrinkage coefficients are 0,1/4,1/2,3/4,1 times the stratum weight.
  Missing strata force coefficient zero. These are a deterministic synthetic
  suite, not IID operating data or untouched confirmation of an attack effect.
- All 128 compare with exact enumeration of all 0/free/1 faces. Singular faces
  reduce to subfaces, as proved in the independent review.
- First 64 additionally compare the complete p-grid {0,1/4,1/2,3/4,1}^k.
- First 16 evaluate full independent binomial outcome probabilities at the
  produced maximizing p, rather than using the risk formula again.
- First 48 compare a general CVXPY/Clarabel SOCP with fixed settings and no retry.
- Eight shared scale cases: k=16,32,64,256, two original inputs each. Both methods
  receive identical d,v; known arithmetic-zero SOCP branches stay in the report.
- Twelve larger exact-only cases: k=16,64,256,1024,4096,16384, two each. No conic
  runtime claim is extrapolated to these unmeasured sizes.
- Total 148 oracle calls, 128 exact reference calls, 64 grids, 16 full
  expectations, at most 56 conic solves. One timed call per input/method; imports
  excluded, input conversion/construction/canonicalization included. CPU wall
  budget 600 seconds, measured from runner start after imports. Check deadline
  between cases; no forced mid-solver kill. Stop and retain partial rows
  if the next operation begins after the deadline. A single solver is separately
  bounded by its iteration limit; 600 seconds is a between-case stop rule.
- No model calls, no external inference API, no new private data, no hardware
  trial. All results, numerical warnings and solver failures are retained.

## Scoring and comparison

All rational computations use Python Fraction; float inputs are rejected by the
exact API. Exact equality is required for certificate/reference/expectation.
The conic baseline uses its own dual representation; numerical objective error
and residuals are reported. Absolute risk error <=1e-7 is an agreement diagnostic,
not an exact certificate. Do not call approximate solver residuals a formal proof.
Record dimensionality, certificate bit lengths, method time, full certificate,
reference value, grid value and conic metadata. No p-values from grid rows.

One RUN_GUARD prevents accidental re-execution of the recorded benchmark. Tests
and saved-certificate replay may run independently without repeating the matrix.
Freeze covers source, tests, protocol, fixtures and dependency versions before
execution. A post-freeze bug requires retaining the failed run and a separately
declared protocol/version, never replacing rows or adjusting thresholds.
