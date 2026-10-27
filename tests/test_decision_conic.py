"""Original handwritten development controls; no frozen evaluation input use."""
from fractions import Fraction as F
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from decision.reusable_conic import ReusableConic, audit_solution


class ResidualAuditTests(unittest.TestCase):
    def test_attaining_simple_point(self):
        result = audit_solution([1.0], [0.0], [1.0], [1.0], 1.0)
        self.assertTrue(result["accepted"])

    def test_missing_bias_denominator_is_rejected(self):
        result = audit_solution([1.0], [0.0], [0.0], [0.0], 0.0)
        self.assertFalse(result["accepted"])
        self.assertFalse(result["positive_active_denominators"])

    def test_zero_dimension_terms_are_permitted(self):
        self.assertTrue(audit_solution([0.0, 1.0], [0.0, 0.0],
                                       [0.0, 1.0], [0.0, 1.0], 1.0)["accepted"])

    def test_negative_loading_is_rejected(self):
        self.assertFalse(audit_solution([0.0], [2.0], [-0.25], [0.0], -0.25)["accepted"])

    def test_bad_epigraph_and_objective_are_rejected(self):
        for epigraph, objective in [([2.0], 1.0), ([0.5], 1.0), ([1.0], 0.5)]:
            self.assertFalse(audit_solution([1.0], [0.0], [1.0], epigraph, objective)["accepted"])

    def test_nonfinite_and_dimensions(self):
        self.assertFalse(audit_solution([1.0], [0.0], [float("nan")], [1.0], 1.0)["accepted"])
        with self.assertRaises(ValueError):
            audit_solution([], [], [], [], 0)


@unittest.skipUnless(importlib.util.find_spec("cvxpy") and importlib.util.find_spec("clarabel"),
                     "optional conic dependencies unavailable")
class ReusableConicDevelopmentTests(unittest.TestCase):
    def test_constructed_problem_is_dpp_and_reused(self):
        model = ReusableConic(1)
        problem_id = id(model.problem)
        for d, v, expected in [(F(3, 7), F(2, 49), F(1, 7)),
                                (F(1, 9), F(2, 81), F(0)),
                                (F(2, 9), F(0), F(4, 81))]:
            result = model.solve([d], [v])
            self.assertIn(result["status"], ("optimal", "optimal_inaccurate"))
            self.assertTrue(result["residuals"]["accepted"], result)
            # An inaccurate status must remain a recorded nonacceptance even
            # when this handwritten point happens to have an accurate value.
            self.assertEqual(result["numerically_accepted"], result["status"] == "optimal")
            self.assertAlmostEqual(result["objective"], float(expected), places=7)
            self.assertEqual(id(model.problem), problem_id)
            self.assertTrue(result["is_dpp"])
            self.assertTrue(result["warm_start_requested"])
        self.assertEqual(model.solver_calls, 3)
        self.assertEqual(result["prior_solver_calls"], 2)

    def test_active_mask_changes_without_rebuild(self):
        model = ReusableConic(3)
        cases = [([F(0), F(1, 5), F(0)], [F(0), F(0), F(2, 7)], F(1, 25)),
                 ([F(2, 5), F(0), F(1, 5)], [F(0)] * 3, F(9, 25))]
        for d, v, expected in cases:
            result = model.solve(d, v)
            self.assertTrue(result["numerically_accepted"], result)
            self.assertAlmostEqual(result["objective"], float(expected), places=7)
            self.assertEqual(len(result["lambda"]), 3)

    def test_zero_d_is_labelled_and_does_not_call_solver(self):
        model = ReusableConic(2)
        result = model.solve([F(0), F(0)], [F(2, 13), F(3, 13)])
        self.assertEqual(result["status"], "analytic_zero_d")
        self.assertEqual(result["solver_calls"], 0)
        self.assertEqual(model.solver_calls, 0)
        self.assertAlmostEqual(result["risk"], float(F(5, 52)), places=14)

    def test_invalid_inputs_and_dimension(self):
        for dimension in [0, -1, True, 2.0]:
            with self.assertRaises(ValueError):
                ReusableConic(dimension)
        model = ReusableConic(1)
        with self.assertRaises(ValueError):
            model.solve([F(-1)], [F(0)])
        with self.assertRaises(ValueError):
            model.solve([], [])
        with self.assertRaises(TypeError):
            model.solve([0.3], [F(0)])
        self.assertEqual(model.solver_calls, 0)


if __name__ == "__main__":
    unittest.main()
