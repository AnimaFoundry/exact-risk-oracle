"""Independent exact upper/lower certificate checker. SPDX-License-Identifier: MIT.

Does not import the solver or reproduce its breakpoint search. It checks a
weighted-Cauchy upper bound and equality of an explicitly evaluated witness.
"""
from fractions import Fraction


def exact(x):
    if isinstance(x, bool) or not isinstance(x, (int, str, Fraction)):
        raise TypeError("Exact rational required")
    return Fraction(x)


def verify(d, v, certificate):
    try:
        d, v = list(map(exact, d)), list(map(exact, v))
        x = list(map(exact, certificate["x"]))
        lam = list(map(exact, certificate["loading"]))
        if not d or len({len(d), len(v), len(x), len(lam)}) != 1:
            return False
        if any(z < 0 for z in d + v + lam) or any(abs(z) > 1 for z in x):
            return False
        ratio = Fraction(0)
        for di, vi, li in zip(d, v, lam):
            b = vi + li
            if b == 0:
                if di != 0:
                    return False
            else:
                ratio += di * di / b
        upper = sum(lam)
        lower = sum(di * xi for di, xi in zip(d, x)) ** 2
        lower -= sum(vi * xi * xi for vi, xi in zip(v, x))
        return (ratio <= 1 and lower == upper
                and exact(certificate["objective"]) == upper
                and exact(certificate["risk"]) == (sum(v) + upper) / 4)
    except (ValueError, TypeError, ZeroDivisionError, KeyError):
        return False
