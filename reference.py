"""Independent, exact small-dimensional reference for a box-quadratic risk.

This module uses exhaustive face enumeration and rational Gaussian elimination.
It deliberately does not import, implement, or call a scalar-envelope algorithm.
Its exponential complexity is appropriate for a reference, not production use.

For nonnegative rational vectors d and v, maximize

    4 R(x) = sum(v) + (sum(d_i * x_i))**2 - sum(v_i * x_i**2)

over [-1, 1]^k.  Replacing x by abs(x) cannot reduce the objective, so the
enumeration may use [0, 1]^k.  A complete justification for skipping singular
faces is in the accompanying reference review.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from typing import Iterable


RationalInput = int | Fraction
FaceCoordinate = int | None  # None means a free coordinate; 0 or 1 is fixed.


@dataclass(frozen=True)
class ReferenceMaximum:
    """An exact maximizing point and transparent enumeration diagnostics."""

    four_risk: Fraction
    x: tuple[Fraction, ...]
    face: tuple[FaceCoordinate, ...]
    faces_examined: int
    rank_deficient_faces: int
    feasible_candidates: int

    @property
    def risk(self) -> Fraction:
        return self.four_risk / 4


def _nonnegative_rationals(
    values: Iterable[RationalInput], name: str
) -> tuple[Fraction, ...]:
    result = []
    for value in values:
        # Floating inputs can silently encode a different rational problem.
        # Require the caller to make any conversion policy explicit.
        if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
            raise TypeError(f"{name} must contain only int or Fraction values")
        rational = Fraction(value)
        if rational < 0:
            raise ValueError(f"{name} must be componentwise nonnegative")
        result.append(rational)
    return tuple(result)


def _unique_linear_solution(
    matrix: list[list[Fraction]], rhs: list[Fraction]
) -> tuple[Fraction, ...] | None:
    """Solve a square rational system, returning None for every singular case.

    Both consistent singular and inconsistent singular systems are skipped.
    Completeness follows from face reduction, not an arbitrary particular
    solution of a singular system.
    """

    n = len(rhs)
    augmented = [row[:] + [value] for row, value in zip(matrix, rhs)]
    for column in range(n):
        pivot_row = next(
            (row for row in range(column, n) if augmented[row][column] != 0),
            None,
        )
        if pivot_row is None:
            return None
        augmented[column], augmented[pivot_row] = (
            augmented[pivot_row],
            augmented[column],
        )
        pivot = augmented[column][column]
        augmented[column] = [entry / pivot for entry in augmented[column]]
        for row in range(n):
            if row == column:
                continue
            multiplier = augmented[row][column]
            if multiplier:
                augmented[row] = [
                    entry - multiplier * pivot_entry
                    for entry, pivot_entry in zip(
                        augmented[row], augmented[column]
                    )
                ]
    return tuple(augmented[row][-1] for row in range(n))


def maximize_reference(
    d: Iterable[RationalInput],
    v: Iterable[RationalInput],
    *,
    max_dimension: int = 10,
) -> ReferenceMaximum:
    """Return the exact maximum by checking all 3**k faces.

    A face fixes each coordinate to 0 or 1, or leaves it free.  For free
    indices F and a = sum(d_i for fixed-one indices), stationarity is

        (d_F d_F^T - diag(v_F)) x_F = -a d_F.

    Every vertex and every feasible unique solution is evaluated.  A singular
    stationary face need not be searched internally: a null direction reaches
    a proper subface with precisely the same objective.  All subfaces are
    already enumerated.  No eigenvalue test is needed, since evaluating extra
    feasible stationary points cannot raise the result above the global max.

    Among enumerated maximizing points, ties prefer the lexicographically
    smallest x.  This is only a deterministic output convention; the returned
    point need not describe the complete set of maximizers.
    """

    dd = _nonnegative_rationals(d, "d")
    vv = _nonnegative_rationals(v, "v")
    if len(dd) != len(vv):
        raise ValueError("d and v must have the same dimension")
    if isinstance(max_dimension, bool) or not isinstance(max_dimension, int):
        raise TypeError("max_dimension must be a nonnegative integer")
    if max_dimension < 0:
        raise ValueError("max_dimension must be nonnegative")
    k = len(dd)
    if k > max_dimension:
        raise ValueError("dimension exceeds the declared exhaustive-search limit")

    constant = sum(vv, Fraction(0))
    best_value: Fraction | None = None
    best_x: tuple[Fraction, ...] | None = None
    best_face: tuple[FaceCoordinate, ...] | None = None
    faces_examined = 0
    rank_deficient_faces = 0
    feasible_candidates = 0

    for face in product((0, 1, None), repeat=k):
        faces_examined += 1
        free = [i for i, state in enumerate(face) if state is None]
        point = [Fraction(0 if state is None else state) for state in face]
        if free:
            fixed_sum = sum(
                (dd[i] for i, state in enumerate(face) if state == 1),
                Fraction(0),
            )
            matrix = [
                [
                    dd[i] * dd[j] - (vv[i] if i == j else 0)
                    for j in free
                ]
                for i in free
            ]
            rhs = [-fixed_sum * dd[i] for i in free]
            solution = _unique_linear_solution(matrix, rhs)
            if solution is None:
                rank_deficient_faces += 1
                continue
            if any(value < 0 or value > 1 for value in solution):
                continue
            for i, value in zip(free, solution):
                point[i] = value

        feasible_candidates += 1
        xx = tuple(point)
        linear = sum((di * xi for di, xi in zip(dd, xx)), Fraction(0))
        value = constant + linear * linear - sum(
            (vi * xi * xi for vi, xi in zip(vv, xx)), Fraction(0)
        )
        if (
            best_value is None
            or value > best_value
            or (value == best_value and best_x is not None and xx < best_x)
        ):
            best_value = value
            best_x = xx
            best_face = face

    # At least the all-zero vertex exists, including in dimension zero.
    assert best_value is not None and best_x is not None and best_face is not None
    return ReferenceMaximum(
        four_risk=best_value,
        x=best_x,
        face=best_face,
        faces_examined=faces_examined,
        rank_deficient_faces=rank_deficient_faces,
        feasible_candidates=feasible_candidates,
    )
