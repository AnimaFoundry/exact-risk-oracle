"""Development-only hand-derived toys for the exact face reference.

These examples are exposed development inputs, not a frozen validation matrix.
They deliberately do not import the production oracle or any old audit data.
"""

from fractions import Fraction as F
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reference import maximize_reference


class ExactReferenceDevelopmentTests(unittest.TestCase):
    def test_empty_problem(self):
        result = maximize_reference([], [])
        self.assertEqual((result.four_risk, result.risk, result.x), (0, 0, ()))
        self.assertEqual(result.faces_examined, 1)

    def test_one_dimensional_concave(self):
        result = maximize_reference([0], [4])
        self.assertEqual((result.four_risk, result.x), (4, (0,)))

    def test_one_dimensional_convex(self):
        result = maximize_reference([2], [1])
        self.assertEqual((result.four_risk, result.x), (4, (1,)))

    def test_one_dimensional_flat(self):
        result = maximize_reference([1], [1])
        self.assertEqual((result.four_risk, result.x), (1, (0,)))
        self.assertEqual(result.rank_deficient_faces, 1)

    def test_zero_variance(self):
        result = maximize_reference([2], [0])
        self.assertEqual((result.four_risk, result.x), (4, (1,)))

    def test_zero_everything(self):
        result = maximize_reference([0, 0], [0, 0])
        self.assertEqual((result.four_risk, result.x), (0, (0, 0)))
        self.assertGreater(result.rank_deficient_faces, 0)

    def test_nonvertex_maximizer_on_edge(self):
        # 4 R = 5 - 3 x^2 + 2 x y; y=1 and x=1/3 maximize it.
        result = maximize_reference([1, 1], [4, 1])
        self.assertEqual(result.four_risk, F(16, 3))
        self.assertEqual(result.risk, F(4, 3))
        self.assertEqual(result.x, (F(1, 3), F(1)))
        self.assertEqual(result.faces_examined, 9)

    def test_singular_stationary_face_reaches_vertex(self):
        # 4 R = 4 - (x-y)^2.  The entire diagonal is optimal.
        result = maximize_reference([1, 1], [2, 2])
        self.assertEqual((result.four_risk, result.x), (4, (0, 0)))
        self.assertGreater(result.rank_deficient_faces, 0)

    def test_singular_inconsistent_face_does_not_need_solution(self):
        # Fixing z=1 gives a singular x,y stationary system with no solution.
        # Directly: 4 R = 4 - (x-y)^2 + 2 z (x+y) + z^2 <= 9.
        result = maximize_reference([1, 1, 1], [2, 2, 0])
        self.assertEqual((result.four_risk, result.x), (9, (1, 1, 1)))
        self.assertGreater(result.rank_deficient_faces, 0)

    def test_mixed_zero_coordinates(self):
        # 4 R = 8 - 3 x^2 + y^2 + 4 y z - z^2; (0,1,1) is optimal.
        result = maximize_reference([0, 1, 2], [3, 0, 5])
        self.assertEqual((result.four_risk, result.x), (12, (0, 1, 1)))

    def test_fraction_coefficients(self):
        # 4 R = 10/9 - 3 x^2/4 + x y/3; x=2/9, y=1.
        result = maximize_reference([F(1, 2), F(1, 3)], [1, F(1, 9)])
        self.assertEqual(result.four_risk, F(31, 27))
        self.assertEqual(result.risk, F(31, 108))
        self.assertEqual(result.x, (F(2, 9), F(1)))

    def test_permuted_edge_toy(self):
        result = maximize_reference([1, 1], [1, 4])
        self.assertEqual(result.four_risk, F(16, 3))
        self.assertEqual(result.x, (F(1), F(1, 3)))

    def test_scaled_edge_toy(self):
        # d -> 3 d and v -> 9 v multiply the complete objective by 9.
        result = maximize_reference([3, 3], [36, 9])
        self.assertEqual(result.four_risk, 48)
        self.assertEqual(result.x, (F(1, 3), F(1)))

    def test_invalid_inputs_fail_explicitly(self):
        with self.assertRaises(ValueError):
            maximize_reference([1], [])
        with self.assertRaises(ValueError):
            maximize_reference([-1], [0])
        with self.assertRaises(ValueError):
            maximize_reference([1], [-1])
        with self.assertRaises(TypeError):
            maximize_reference([0.5], [1])
        with self.assertRaises(TypeError):
            maximize_reference([True], [1])
        with self.assertRaises(ValueError):
            maximize_reference([1, 1], [1, 1], max_dimension=1)
        with self.assertRaises(ValueError):
            maximize_reference([], [], max_dimension=-1)
        with self.assertRaises(TypeError):
            maximize_reference([], [], max_dimension=True)


if __name__ == "__main__":
    unittest.main()
