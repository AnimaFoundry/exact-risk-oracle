"""Independent floating-point conic baseline for the homogeneous risk problem.

This module intentionally does not import the exact oracle or its breakpoint
algorithm.  It formulates the established diagonal-loading conic upper bound
directly and solves it once with CVXPY/Clarabel.  Floating solver output is not an
exact mathematical certificate, even when the reported residuals are small.

No model, network, random generator, or benchmark data is used by this module.
"""

from __future__ import annotations

from fractions import Fraction
import math
from time import perf_counter
from typing import Any, Sequence


SOLVER_OPTIONS = {
    "tol_gap_abs": 1e-10,
    "tol_gap_rel": 1e-10,
    "tol_feas": 1e-10,
    "max_iter": 200,
}
RESIDUAL_TOLERANCE = 1e-7


def _inputs(values: Sequence[Fraction], name: str) -> list[Fraction]:
    result = list(values)
    if any(not isinstance(value, Fraction) for value in result):
        raise TypeError(f"{name} must contain fractions.Fraction values")
    if any(value < 0 for value in result):
        raise ValueError(f"{name} must be nonnegative")
    return result


def solve(d: Sequence[Fraction], v: Sequence[Fraction]) -> dict[str, Any]:
    """Approximate max_x (d.x)^2 - sum_i v_i*x_i^2 for x in [0,1]^k.

    Parameters are exact nonnegative rationals.  Returned ``objective`` is the
    floating-point dual objective; ``risk`` adds sum(v) and divides by four.
    Neither is an exact certificate.  ``numerically_accepted`` requires an
    optimal solver status and independently recomputed residuals below the
    declared tolerance.  The solver is called at most once, without retries.

    Timing includes expression construction, CVXPY canonicalization and the
    solver call, but excludes the initial CVXPY/NumPy import.  The time spent
    strictly in ``problem.solve`` is also returned.  No result is rounded,
    clipped, or substituted after a solver failure.
    """
    d_exact = _inputs(d, "d")
    v_exact = _inputs(v, "v")
    if len(d_exact) != len(v_exact):
        raise ValueError("d and v must have the same length")

    active = [index for index, value in enumerate(d_exact) if value > 0]
    variance_sum = float(sum(v_exact, Fraction(0)))
    base: dict[str, Any] = {
        "method": "independent_diagonal_loading_socp",
        "solver": "CLARABEL",
        "dimension": len(d_exact),
        "active_dimension": len(active),
        "solver_options": dict(SOLVER_OPTIONS),
        "residual_tolerance": RESIDUAL_TOLERANCE,
        "objective_is_exact_certificate": False,
        "solver_calls": 0,
        "numerically_accepted": False,
        "objective": None,
        "risk": None,
        "solver_objective": None,
        "lambda": None,
        "residuals": None,
        "time_seconds": 0.0,
        "optimization_wall_seconds": 0.0,
        "solver_reported_seconds": None,
        "iterations": None,
    }
    if not active:
        # With d=0, the maximum is zero at x=0.  This is an algebraic
        # degenerate case, not a successful invocation of a conic solver.
        base.update(
            status="analytic_zero_d",
            objective=0.0,
            risk=variance_sum / 4.0,
            solver_objective=0.0,
            **{"lambda": [0.0] * len(d_exact)},
            residuals={
                "finite": math.isfinite(variance_sum),
                "nonnegative_violation_normalized": 0.0,
                "cone_violation": 0.0,
                "cone_sum": 0.0,
                "positive_active_denominators": True,
                "objective_disagreement_normalized": 0.0,
            },
            numerically_accepted=math.isfinite(variance_sum),
        )
        return base

    # Optional dependencies are imported only on actual solver use.  This also
    # lets readers inspect the module without installing an optimization stack.
    import cvxpy as cp
    import numpy as np

    started = perf_counter()
    # Scaling preserves q: d' = d/sqrt(s), v' = v/s, lambda' = lambda/s.
    # It is selected directly from inputs, not from the exact solution.
    scale_exact = max(
        sum((value * value for value in d_exact), Fraction(0)),
        max(v_exact, default=Fraction(0)),
    )
    scale = float(scale_exact)
    if not math.isfinite(scale) or scale <= 0 or not math.isfinite(variance_sum):
        raise ValueError("inputs cannot be represented by finite positive float scaling")
    normalized_d = np.array(
        [math.sqrt(float(d_exact[index] ** 2 / scale_exact)) for index in active],
        dtype=float,
    )
    normalized_v = np.array(
        [float(v_exact[index] / scale_exact) for index in active], dtype=float
    )
    if not np.all(np.isfinite(normalized_d)) or np.any(normalized_d <= 0):
        raise ValueError("positive d entry overflowed or underflowed after float scaling")
    if not np.all(np.isfinite(normalized_v)):
        raise ValueError("v entry overflowed after float scaling")
    if any(v_exact[index] > 0 and normalized_v[position] == 0
           for position, index in enumerate(active)):
        raise ValueError("positive v entry underflowed after float scaling")
    loading = cp.Variable(len(active), nonneg=True, name="diagonal_loading")
    terms = [
        cp.quad_over_lin(normalized_d[position], normalized_v[position] + loading[position])
        for position in range(len(active))
    ]
    problem = cp.Problem(cp.Minimize(cp.sum(loading)), [cp.sum(terms) <= 1.0])
    base["normalization_scale"] = scale
    base["cvxpy_version"] = cp.__version__
    base["solver_calls"] = 1
    optimization_started = perf_counter()
    try:
        problem.solve(solver="CLARABEL", verbose=False, **SOLVER_OPTIONS)
    except Exception as error:
        base.update(
            status="solver_error",
            error_type=type(error).__name__,
            error=str(error)[:500],
            time_seconds=perf_counter() - started,
            optimization_wall_seconds=perf_counter() - optimization_started,
        )
        return base
    base["optimization_wall_seconds"] = perf_counter() - optimization_started
    base["status"] = str(problem.status)
    base["solver_reported_seconds"] = problem.solver_stats.solve_time
    base["iterations"] = problem.solver_stats.num_iters
    if loading.value is None or problem.value is None:
        base["time_seconds"] = perf_counter() - started
        return base

    # Recompute feasibility from the returned vector, independently of CVXPY's
    # own residual/status fields.  Keep small negative values as evidence.
    load = [float(value) for value in loading.value]
    denominator = [float(normalized_v[i]) + load[i] for i in range(len(active))]
    finite = all(math.isfinite(value) for value in load + denominator)
    positive = finite and all(value > 0 for value in denominator)
    cone_sum = (
        math.fsum(float(normalized_d[i]) ** 2 / denominator[i] for i in range(len(active)))
        if positive else None
    )
    dual_normalized = math.fsum(load) if finite else None
    solver_normalized = float(problem.value)
    finite = finite and math.isfinite(solver_normalized)
    if cone_sum is not None:
        finite = finite and math.isfinite(cone_sum)
    nonnegative_violation = max(0.0, -min(load)) if finite else None
    cone_violation = max(0.0, cone_sum - 1.0) if positive and finite else None
    disagreement = (
        abs(dual_normalized - solver_normalized)
        if finite and dual_normalized is not None else None
    )
    residuals = {
        "finite": finite,
        "nonnegative_violation_normalized": nonnegative_violation,
        "cone_violation": cone_violation,
        "cone_sum": cone_sum if finite else None,
        "positive_active_denominators": positive,
        "objective_disagreement_normalized": disagreement,
    }
    base["residuals"] = residuals
    if finite and dual_normalized is not None:
        objective = dual_normalized * scale
        expanded_load = [0.0] * len(d_exact)
        for position, index in enumerate(active):
            expanded_load[index] = load[position] * scale
        risk = (variance_sum + objective) / 4.0
        solver_objective = solver_normalized * scale
        if all(math.isfinite(value) for value in expanded_load + [objective, risk, solver_objective]):
            base["lambda"] = expanded_load
            base["objective"] = objective
            base["risk"] = risk
            base["solver_objective"] = solver_objective
        else:
            finite = False
            residuals["finite"] = False
            base["error"] = "rescaled_result_not_finite"
    base["numerically_accepted"] = bool(
        problem.status == cp.OPTIMAL
        and finite
        and positive
        and nonnegative_violation is not None
        and nonnegative_violation <= RESIDUAL_TOLERANCE
        and cone_violation is not None
        and cone_violation <= RESIDUAL_TOLERANCE
        and disagreement is not None
        and disagreement <= RESIDUAL_TOLERANCE
    )
    base["time_seconds"] = perf_counter() - started
    return base
