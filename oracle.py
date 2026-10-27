"""Exact certificate-producing specialization for rank-one coupled box risk.

Original implementation, SPDX-License-Identifier: MIT.
Arithmetic-operation complexity O(k log k); not a bit-complexity claim.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import groupby


def rational(x):
    if isinstance(x, bool) or not isinstance(x, (int, F, str)):
        raise TypeError("Use exact integers, Fractions, or rational strings")
    return F(x)


@dataclass(frozen=True)
class Certificate:
    t: F
    x: tuple[F, ...]
    loading: tuple[F, ...]
    objective: F
    risk: F
    intervals: int

    def to_dict(self):
        return {"t": str(self.t), "x": list(map(str, self.x)),
                "loading": list(map(str, self.loading)),
                "objective": str(self.objective), "risk": str(self.risk),
                "intervals": self.intervals}


def solve(d, v):
    """Maximize (d.x)^2-sum(v_i*x_i^2) over [-1,1]^k.

    Returns an exact attaining witness and diagonal-majorizer certificate.
    d and v must be nonnegative exact rationals. risk adds sum(v) and divides
    by four, matching the documented centered Bernoulli estimator reduction.
    """
    d, v = tuple(map(rational, d)), tuple(map(rational, v))
    if not d or len(d) != len(v) or any(z < 0 for z in d + v):
        raise ValueError("Equal nonempty nonnegative vectors required")
    active = sorted((vi / di, di, vi) for di, vi in zip(d, v) if di and vi)
    a = sum((di * di / vi for _, di, vi in active), F(0))
    c = sum((di for di, vi in zip(d, v) if vi == 0), F(0))
    t, intervals = F(0), 0
    if c or a > 1:
        left = F(0)
        for right, entries in groupby(active, key=lambda z: z[0]):
            intervals += 1
            if a < 1 and left <= c / (1 - a) <= right:
                t = c / (1 - a)
                break
            for _, di, vi in entries:
                a -= di * di / vi
                c += di
            left = right
        else:
            intervals += 1
            t = c / (1 - a)
            if t < left:
                raise ArithmeticError("Threshold invariant failed")
    loading = tuple(max(F(0), t * di - vi) for di, vi in zip(d, v))
    x = tuple(t * di / (vi + li) if vi + li else F(0)
              for di, vi, li in zip(d, v, loading))
    objective = sum(loading, F(0))
    return Certificate(t, x, loading, objective,
                       (sum(v, F(0)) + objective) / 4, intervals)


def from_estimator(weights, counts, coefficients):
    """Centered estimator 1/2+sum a_i*(K_i/n_i-1/2); n_i=0 implies a_i=0."""
    w, a = tuple(map(rational, weights)), tuple(map(rational, coefficients))
    n = tuple(counts)
    if not w or len(w) != len(a) or len(w) != len(n) or sum(w) != 1:
        raise ValueError("Equal vectors and weights summing to one required")
    if any(isinstance(ni, bool) or not isinstance(ni, int) or ni < 0 for ni in n):
        raise ValueError("Counts must be nonnegative integers")
    if any(wi < 0 or ai < 0 or ai > wi or (ni == 0 and ai != 0)
           for wi, ai, ni in zip(w, a, n)):
        raise ValueError("Require 0<=a<=w and a=0 at unobserved strata")
    d = tuple(wi - ai for wi, ai in zip(w, a))
    v = tuple(ai * ai / ni if ni else F(0) for ai, ni in zip(a, n))
    return d, v, solve(d, v)
