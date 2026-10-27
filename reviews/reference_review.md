# Independent exact face-enumeration reference

Status: development reference, not a completed frozen validation experiment.
Date: 2026-10-27.

## Scope and independence

`aim/exact_risk_oracle/reference.py` independently maximizes the supplied
quadratic using rational arithmetic, exhaustive face enumeration, and Gaussian
elimination. It does not import or call a production scalar-envelope oracle,
does not use its breakpoints or scalar formula, and does not import any earlier
audit or model-experiment data. Its inputs and outputs are exact integers or
`fractions.Fraction` values. Floating inputs are rejected rather than silently
changing the problem through binary rounding.

The objective is

\[
Q(x)=4R(x)=\sum_i v_i +(d^T x)^2-\sum_i v_i x_i^2,
\qquad d_i,v_i\geq0,\quad x\in[-1,1]^k.
\]

Replacing every coordinate by its absolute value preserves the diagonal term
and weakly increases the squared linear term, since
`abs(sum(d_i*x_i)) <= sum(d_i*abs(x_i))`. Therefore maximizing over `[0,1]^k`
has exactly the same value. This relies on nonnegative `d`; signed coefficients
are outside the declared interface.

## Enumeration and stationary equations

For each of the `3**k` faces, every coordinate is fixed to zero, fixed to one,
or free. Write `F` for its free coordinates and
`a = sum(d_i for fixed-one coordinates)`. Restricted stationarity is

\[
H_F x_F=-a d_F,\qquad
H_F=d_Fd_F^T-\operatorname{diag}(v_F).
\]

Every vertex is evaluated. If `H_F` is nonsingular, exact Gaussian elimination
produces its unique stationary point; it is evaluated if every coordinate lies
in the closed interval `[0,1]`. Endpoint stationary points may be duplicates,
which is harmless. No local maximum test is required: extra feasible saddle
points or minima cannot have value greater than the global maximum.

All rank-deficient systems are skipped. This includes both consistent flat
stationary families and inconsistent systems. The diagnostic field is named
`rank_deficient_faces`; it does not assert that each skipped face has a
stationary point.

## Completeness with singular and zero cases

**Proposition.** The enumerated candidate set contains a global maximizer.

**Proof.** Compactness gives a global maximizer. Among global maximizers choose
one whose minimal containing face has smallest dimension. If that face is a
vertex, it is enumerated. Otherwise this maximizer lies in its relative
interior, so all free partial derivatives vanish. If its free quadratic matrix
`H_F` (half the Hessian) were singular, choose a nonzero null vector `z`. Moving from the stationary
point to `x_F + t z` changes the quadratic by

\[
2t z^T(H_F x_F+a d_F)+t^2z^TH_Fz=0.
\]

The relative interior allows a nonzero interval of such movements, and the
bounded box allows movement to a boundary endpoint. At that endpoint the
objective is unchanged and the point lies on a strictly smaller face, contrary
to minimality. Thus the chosen face has a nonsingular stationary system, whose
unique solution is enumerated. This argument also covers zero `d`, zero `v`,
and an identically constant objective. No generic-position assumption or
floating tolerance is used. QED.

The proof concerns a finite exact algorithm and does not assert that checking
only vertices is sufficient. The development example `d=(1,1), v=(4,1)` has
the nonvertex maximizing point `(1/3,1)` and value `Q=16/3`.

## Complexity and operational boundary

The reference uses `3**k` face states and at most cubic rational elimination per
face, with rational bit complexity additional to arithmetic-operation counts.
The default interface explicitly rejects dimensions above 10. This is a small
instance reference, not an efficient production algorithm or an empirical
scaling result. The limit may be explicitly lowered or raised by the caller;
no claim about runtime at the limit has been tested here.

## Development-only tests

`aim/exact_risk_oracle/tests/test_reference.py` contains hand-derived toys for: the empty problem;
one-dimensional concave, convex, and constant cases; zero variance; all-zero
coefficients; a nonvertex edge maximizer; a singular stationary diagonal;
an inconsistent singular face; mixed zero coordinates; rational coefficients;
and permutation/scaling of the same edge toy. It also checks declared input
rejections. All are exposed development inputs, not independent holdout data.

The original identical toy suite was first placed at repository-root
`tests/test_reference.py`. The standalone package copy changes only its import
path and is the file to include in the package freeze. The focused development
run completed on Windows using
`python -m unittest discover -s aim/exact_risk_oracle/tests -p test_reference.py -v`:
14 tests passed.
This was a development run only, not clean Linux acceptance.

No exhaustive coefficient matrix, random benchmark, production-oracle
comparison, or statistical experiment is authorized by these development
tests. The parent must freeze the new finite protocol and fixtures before
starting that validation. Theoretical completeness of this reference does not
prove production correctness or invention novelty.

## Recommended frozen validation

Use a newly frozen rational coefficient grid with explicit cases for singular
free Hessians, zero coefficients, and boundary ties. Compare the production
maximum exactly to this independent maximum, independently substitute each
reported witness into the objective, and verify bounds and sign reduction.
Record every failure; do not silently modify fixtures or call development data
a holdout. A dense numerical grid may be a tertiary check but is not an exact
oracle. A second direct brute grid should not substitute for face enumeration.

The clean Linux test run and any production comparison remain to be performed
under the parent protocol. This reference needs no full private-data checks.
