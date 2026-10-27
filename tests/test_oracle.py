import copy
from fractions import Fraction as F
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from oracle import solve, from_estimator
from check_certificate import verify


class DevelopmentTests(unittest.TestCase):
    def check(self, d, v, expected=None):
        c = solve(d, v)
        self.assertTrue(verify(d, v, c.to_dict()))
        if expected is not None:
            self.assertEqual(c.objective, F(expected))
        return c

    def test_zero_bias(self):
        self.check([0, 0], [2, 3], 0)

    def test_zero_variance(self):
        self.check([2, 3], [0, 0], 25)

    def test_flat(self):
        self.check([1, 0], [1, 0], 0)

    def test_ties(self):
        self.check([1, 1, 1], [1, 1, 1], 6)

    def test_interior(self):
        d, v, c = from_estimator([F(1, 2)] * 2, [1, 1], [F(1, 3), F(1, 6)])
        self.assertEqual(c.risk, F(7, 108))
        self.assertEqual(c.x, (F(2, 3), F(1)))
        self.assertTrue(verify(d, v, c.to_dict()))

    def test_missing(self):
        d, v, c = from_estimator([F(1, 10), F(9, 10)], [0, 100], [0, F(15, 17)])
        self.assertTrue(verify(d, v, c.to_dict()))

    def test_root_at_tied_threshold(self):
        c = self.check([F(1,4), F(1,8), F(1,8)], [0, F(1,16), F(1,16)], F(1,8))
        self.assertEqual(c.t, F(1,2))

    def test_unattained_and_infeasible_certificates(self):
        d, v = [F(1,6), F(1,3)], [F(1,9), F(1,36)]
        c = solve(d,v).to_dict()
        bad = copy.deepcopy(c)
        bad['x'] = ['0','0']
        self.assertFalse(verify(d,v,bad))
        bad['loading'] = ['0','0']
        bad['objective'] = '0'
        bad['risk'] = str(sum(v)/4)
        self.assertFalse(verify(d,v,bad))
        del c['t']
        del c['intervals']
        self.assertTrue(verify(d,v,c))

    def test_dimension_one(self):
        for d, v in [(0, 0), (1, 2), (2, 1), (1, 1)]:
            self.check([d], [v], max(0, d*d-v))

    def test_certificate_tampering(self):
        d, v = [1, 2], [2, 3]
        c = self.check(d, v).to_dict()
        for key in ('objective', 'risk'):
            bad = copy.deepcopy(c)
            bad[key] = str(F(bad[key]) + 1)
            self.assertFalse(verify(d, v, bad))
        for key in ('x', 'loading'):
            bad = copy.deepcopy(c)
            bad[key][0] = '-2'
            self.assertFalse(verify(d, v, bad))
        self.assertFalse(verify(d, v, {}))
        self.assertFalse(verify([1], [0], {'x':['0'], 'loading':['0'], 'objective':'0', 'risk':'0'}))

    def test_invalid_inputs(self):
        for d, v in [([], []), ([1], []), ([-1], [1]), ([1], [-1])]:
            with self.assertRaises(ValueError): solve(d, v)
        with self.assertRaises(TypeError): solve([0.1], [1])
        with self.assertRaises(TypeError): solve([True], [1])
        with self.assertRaises(ValueError): from_estimator([1], [0], [1])
        with self.assertRaises(ValueError): from_estimator([1], [True], [0])
        with self.assertRaises(ValueError): from_estimator([1], [1], [2])


if __name__ == '__main__':
    unittest.main()
