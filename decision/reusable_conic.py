"""Reusable independent conic comparator for the fixed-dimensional risk family.

Original implementation, SPDX-License-Identifier: MIT.
This module neither imports the exact solver nor uses its breakpoint algorithm.
One CVXPY DPP problem is constructed per instance and reused with warm starts.
Returned floating-point bounds are numerical diagnostics, not exact certificates.
"""

from __future__ import annotations

from fractions import Fraction
import math
from time import perf_counter
from typing import Any, Sequence
import warnings


SOLVER_OPTIONS = {
    "tol_gap_abs": 1e-10,
    "tol_gap_rel": 1e-10,
    "tol_feas": 1e-10,
    "max_iter": 200,
}
RESIDUAL_TOLERANCE = 1e-7


def _inputs(values: Sequence[Fraction], name: str, dimension: int) -> list[Fraction]:
    result = list(values)
    if len(result) != dimension:
        raise ValueError(f"{name} must have the constructed dimension")
    if any(not isinstance(value, Fraction) for value in result):
        raise TypeError(f"{name} must contain fractions.Fraction values")
    if any(value < 0 for value in result):
        raise ValueError(f"{name} must be nonnegative")
    return result


def audit_solution(d, v, loading, epigraph, solver_objective) -> dict[str, Any]:
    """Recompute normalized SOC, majorizer and objective residuals from floats.

    The checker deliberately permits zero denominators only at zero d entries.
    It never clips a returned loading, repairs a point, or changes a risk value.
    """
    vectors = [list(d), list(v), list(loading), list(epigraph)]
    if not vectors[0] or any(len(row) != len(vectors[0]) for row in vectors):
        raise ValueError("Equal nonempty vectors are required")
    d, v, loading, epigraph = vectors
    finite = all(math.isfinite(float(z)) for row in vectors for z in row)
    finite = finite and math.isfinite(float(solver_objective))
    result: dict[str, Any] = {
        "finite": finite,
        "nonnegative_violation_normalized": None,
        "epigraph_nonnegative_violation": None,
        "soc_violation": None,
        "epigraph_sum_violation": None,
        "cone_sum": None,
        "cone_violation": None,
        "positive_active_denominators": False,
        "objective_disagreement_normalized": None,
        "accepted": False,
    }
    if not finite:
        return result
    denominator = [vi + li for vi, li in zip(v, loading)]
    if not all(math.isfinite(z) for z in denominator):
        result["finite"] = False
        return result
    active_positive = all(bi > 0 for di, bi in zip(d, denominator) if di > 0)
    soc_residual = max(
        0.0,
        max(math.hypot(2 * di, bi - zi) - (bi + zi)
            for di, bi, zi in zip(d, denominator, epigraph)),
    )
    cone_sum = math.fsum(di * di / bi for di, bi in zip(d, denominator)
                         if di > 0) if active_positive else None
    result.update(
        nonnegative_violation_normalized=max(0.0, -min(loading)),
        epigraph_nonnegative_violation=max(0.0, -min(epigraph)),
        soc_violation=soc_residual,
        epigraph_sum_violation=max(0.0, math.fsum(epigraph) - 1.0),
        cone_sum=cone_sum,
        cone_violation=max(0.0, cone_sum - 1.0) if cone_sum is not None else None,
        positive_active_denominators=active_positive,
        objective_disagreement_normalized=abs(math.fsum(loading) - solver_objective),
    )
    checked = [result[key] for key in (
        "nonnegative_violation_normalized", "epigraph_nonnegative_violation",
        "soc_violation", "epigraph_sum_violation", "cone_violation",
        "objective_disagreement_normalized",
    )]
    result["finite"] = all(value is None or math.isfinite(value) for value in checked)
    result["accepted"] = bool(
        result["finite"] and active_positive
        and all(value is not None and value <= RESIDUAL_TOLERANCE for value in checked)
    )
    return result


class ReusableConic:
    """A fixed-dimensional DPP SOCP; solve(d, v) makes at most one solver call.

    ``build_seconds`` excludes initial optional-library imports. Per-call
    ``time_seconds`` includes input validation/scaling, parameter assignment,
    cached canonicalization, warm-started solve and independent residual checks.
    The first call still includes first compilation; no hidden priming occurs.
    An all-zero d input is an explicitly labelled algebraic case, not a solve.
    Keep the same object across calls to measure reuse; make a fresh object to
    include cold construction. Construction is never silently charged per call.
    """

    def __init__(self, dimension: int):
        if isinstance(dimension, bool) or not isinstance(dimension, int) or dimension < 1:
            raise ValueError("dimension must be a positive integer")
        import cvxpy as cp
        import numpy as np

        started = perf_counter()
        self._cp, self._np = cp, np
        self.dimension = dimension
        self._d = cp.Parameter(dimension, nonneg=True, name="scaled_bias")
        self._v = cp.Parameter(dimension, nonneg=True, name="scaled_variance")
        self._loading = cp.Variable(dimension, nonneg=True, name="loading")
        self._epigraph = cp.Variable(dimension, nonneg=True, name="ratio_epigraph")
        denominator = self._v + self._loading
        # ||(2*d_i, B_i-z_i)|| <= B_i+z_i iff d_i^2 <= B_i*z_i.
        # This explicit rotated-cone representation is DPP, including zero d.
        cone = cp.SOC(denominator + self._epigraph,
                      cp.vstack([2 * self._d, denominator - self._epigraph]), axis=0)
        self.problem = cp.Problem(cp.Minimize(cp.sum(self._loading)),
                                  [cone, cp.sum(self._epigraph) <= 1.0])
        self.is_dpp = bool(self.problem.is_dpp())
        if not self.is_dpp:
            raise RuntimeError("Reusable formulation is unexpectedly not DPP")
        self.build_seconds = perf_counter() - started
        self.calls = 0
        self.solver_calls = 0

    def solve(self, d: Sequence[Fraction], v: Sequence[Fraction]) -> dict[str, Any]:
        started = perf_counter()
        d_exact = _inputs(d, "d", self.dimension)
        v_exact = _inputs(v, "v", self.dimension)
        self.calls += 1
        variance_sum = float(sum(v_exact, Fraction(0)))
        base: dict[str, Any] = {
            "method": "reusable_vectorized_dpp_socp",
            "solver": "CLARABEL", "cvxpy_version": self._cp.__version__,
            "dimension": self.dimension, "active_dimension": sum(z > 0 for z in d_exact),
            "call_index": self.calls, "solver_calls": 0,
            "prior_solver_calls": self.solver_calls,
            "warm_start_requested": True, "enforce_dpp": True, "is_dpp": self.is_dpp,
            "solver_options": dict(SOLVER_OPTIONS),
            "residual_tolerance": RESIDUAL_TOLERANCE,
            "objective_is_exact_certificate": False,
            "numerically_accepted": False, "objective": None, "risk": None,
            "solver_objective": None, "lambda": None, "epigraph": None,
            "residuals": None, "warnings": [], "time_seconds": 0.0,
            "optimization_wall_seconds": 0.0, "solver_reported_seconds": None,
            "iterations": None,
        }
        if not math.isfinite(variance_sum):
            raise ValueError("variance sum cannot be represented by a finite float")
        if not any(d_exact):
            base.update(
                status="analytic_zero_d", objective=0.0, risk=variance_sum / 4.0,
                solver_objective=0.0, **{"lambda": [0.0] * self.dimension},
                epigraph=[0.0] * self.dimension,
                residuals={"accepted": True, "finite": True,
                           "cone_violation": 0.0, "cone_sum": 0.0},
                numerically_accepted=True,
            )
            base["time_seconds"] = perf_counter() - started
            return base

        # Entirely input-derived normalization; no exact result or outcome tuning.
        scale_exact = max(sum((z * z for z in d_exact), Fraction(0)), max(v_exact))
        scale = float(scale_exact)
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError("inputs have no finite positive float normalization")
        d_norm = [math.sqrt(float(z * z / scale_exact)) for z in d_exact]
        v_norm = [float(z / scale_exact) for z in v_exact]
        if not all(math.isfinite(z) for z in d_norm + v_norm):
            raise ValueError("normalized input is not finite")
        if any(exact > 0 and floating == 0 for exact, floating
               in zip(d_exact + v_exact, d_norm + v_norm)):
            raise ValueError("a positive normalized input underflowed")
        self._d.value = self._np.asarray(d_norm)
        self._v.value = self._np.asarray(v_norm)
        base["normalization_scale"] = scale
        base["normalization_scale_exact"] = str(scale_exact)
        base["solver_calls"] = 1
        self.solver_calls += 1
        optimization_started = perf_counter()
        with warnings.catch_warnings(record=True) as captured:
            warnings.simplefilter("always")
            try:
                self.problem.solve(solver="CLARABEL", warm_start=True,
                                   enforce_dpp=True, verbose=False, **SOLVER_OPTIONS)
            except Exception as error:
                base.update(status="solver_error", error_type=type(error).__name__,
                            error=str(error)[:500])
            finally:
                base["warnings"] = [{"category": str(w.category.__name__),
                                     "message": str(w.message)[:500]} for w in captured]
                base["optimization_wall_seconds"] = perf_counter() - optimization_started
        if base.get("status") == "solver_error":
            base["time_seconds"] = perf_counter() - started
            return base
        base["status"] = str(self.problem.status)
        base["solver_reported_seconds"] = self.problem.solver_stats.solve_time
        base["iterations"] = self.problem.solver_stats.num_iters
        if self._loading.value is None or self._epigraph.value is None or self.problem.value is None:
            base["time_seconds"] = perf_counter() - started
            return base
        loading = [float(z) for z in self._loading.value]
        epigraph = [float(z) for z in self._epigraph.value]
        solver_objective = float(self.problem.value)
        residuals = audit_solution(d_norm, v_norm, loading, epigraph, solver_objective)
        base["residuals"] = residuals
        # Preserve complete normalized vectors even when residual acceptance fails.
        base["lambda_normalized"] = loading
        base["epigraph"] = epigraph
        if residuals["finite"]:
            objective = math.fsum(loading) * scale
            risk = (variance_sum + objective) / 4.0
            expanded_loading = [z * scale for z in loading]
            if all(math.isfinite(z) for z in [objective, risk] + expanded_loading):
                base.update(objective=objective, risk=risk,
                            solver_objective=solver_objective * scale,
                            **{"lambda": expanded_loading})
            else:
                residuals["finite"] = False
                residuals["accepted"] = False
                base["error"] = "rescaled_result_not_finite"
        base["numerically_accepted"] = bool(
            self.problem.status == self._cp.OPTIMAL and residuals["accepted"]
        )
        base["time_seconds"] = perf_counter() - started
        return base
