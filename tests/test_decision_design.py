"""Independent handwritten controls for sampling-decision design.

No formal generator or held-out fixture is imported or evaluated here.
SPDX-License-Identifier: MIT
"""
import copy
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from decision.design import (coarse_grid, enumerate_candidates, estimator_inputs,
                             exact_choice, validate)


def toy(weights, shrinkage, calendar):
    return {'weights': weights, 'shrinkage': shrinkage,
            'budget': sum(slot['powered'] for slot in calendar),
            'calendar': calendar}


def independent_schedules(scenario):
    """Enumerate whole schedules, without DP or a production helper."""
    width = len(scenario['weights'])
    options = [([-1] + slot['eligible']) if slot['powered'] else [-1]
               for slot in scenario['calendar']]
    representatives = {}
    for schedule in product(*options):
        counts = tuple(schedule.count(channel) for channel in range(width))
        representatives[counts] = min(schedule, representatives.get(counts, schedule))
    return [{'counts': list(counts), 'schedule': list(representatives[counts])}
            for counts in sorted(representatives)]


def independent_grid(d, v):
    """Full signed transformed grid; no absolute-value shortcut."""
    candidates = []
    for x in product((F(-1), F(-1, 2), F(0), F(1, 2), F(1)), repeat=len(d)):
        variance = sum(vi * (1 - xi * xi) for vi, xi in zip(v, x)) / 4
        bias_squared = (sum(di * xi for di, xi in zip(d, x)) / 2) ** 2
        candidates.append(variance + bias_squared)
    return max(candidates)


class DecisionDesignControls(unittest.TestCase):
    def test_dp_matches_independent_full_schedules(self):
        calendars = [
            [],
            [{'powered': False, 'eligible': [0, 1]}],
            [{'powered': True, 'eligible': [0, 1]}] * 3,
            [{'powered': True, 'eligible': [0]},
             {'powered': False, 'eligible': [0, 1]},
             {'powered': True, 'eligible': [1]}],
            [{'powered': True, 'eligible': [0, 1]},
             {'powered': True, 'eligible': [1]},
             {'powered': True, 'eligible': [0, 1]}],
        ]
        for calendar in calendars:
            with self.subTest(calendar=calendar):
                scenario = toy(['2/7', '5/7'], '1/2', calendar)
                self.assertEqual(enumerate_candidates(scenario),
                                 independent_schedules(scenario))

    def test_count_vectors_are_unique_not_schedule_multiplicity(self):
        scenario = toy(['1/2', '1/2'], '1',
                       [{'powered': True, 'eligible': [0, 1]}] * 2)
        candidates = enumerate_candidates(scenario)
        self.assertEqual(len(candidates), 6)
        mixed = next(row for row in candidates if row['counts'] == [1, 1])
        self.assertEqual(mixed['schedule'], [0, 1])
        one = next(row for row in candidates if row['counts'] == [1, 0])
        self.assertEqual(one['schedule'], [-1, 0])

    def test_idle_is_available_and_energy_does_not_carry(self):
        scenario = toy(['1/3', '2/3'], '2',
                       [{'powered': True, 'eligible': [0]},
                        {'powered': False, 'eligible': [1]}])
        self.assertEqual(enumerate_candidates(scenario),
                         [{'counts': [0, 0], 'schedule': [-1, -1]},
                          {'counts': [1, 0], 'schedule': [0, -1]}])

    def test_restricted_coverage_still_allows_less_than_budget(self):
        scenario = toy(['1/4', '3/4'], '0',
                       [{'powered': True, 'eligible': [1]}] * 3)
        self.assertEqual([row['counts'] for row in enumerate_candidates(scenario)],
                         [[0, 0], [0, 1], [0, 2], [0, 3]])

    def test_empty_power_calendar_keeps_one_zero_candidate(self):
        scenario = toy(['1'], '0', [])
        self.assertEqual(enumerate_candidates(scenario),
                         [{'counts': [0], 'schedule': []}])

    def test_zero_count_is_uncertainty_not_zero_probability(self):
        scenario = toy(['2/5', '3/5'], '0', [])
        weights, coefficients, d, v = estimator_inputs(scenario, [0, 0])
        self.assertEqual(weights, (F(2, 5), F(3, 5)))
        self.assertEqual(coefficients, (F(0), F(0)))
        self.assertEqual(d, weights)
        self.assertEqual(v, (F(0), F(0)))
        self.assertEqual(F(coarse_grid(d, v)['risk']), F(1, 4))

    def test_no_shrinkage_observed_stratum(self):
        scenario = toy(['2/5', '3/5'], '0', [])
        _, a, d, v = estimator_inputs(scenario, [2, 0])
        self.assertEqual(a, (F(2, 5), F(0)))
        self.assertEqual(d, (F(0), F(3, 5)))
        self.assertEqual(v, (F(2, 25), F(0)))

    def test_fractional_shrinkage_formula(self):
        scenario = toy(['2/5', '3/5'], '1/2', [])
        _, a, d, v = estimator_inputs(scenario, [2, 1])
        self.assertEqual(a, (F(8, 25), F(2, 5)))
        self.assertEqual(d, (F(2, 25), F(1, 5)))
        self.assertEqual(v, (F(32, 625), F(4, 25)))

    def test_grid_reduction_matches_full_signed_grid(self):
        controls = [([F(0)], [F(0)]),
                    ([F(0)], [F(3, 7)]),
                    ([F(1, 3), F(2, 3)], [F(0), F(0)]),
                    ([F(1, 5), F(1, 4)], [F(1, 7), F(1, 9)]),
                    ([F(1, 2), F(1, 5), F(0)],
                     [F(1, 4), F(2, 3), F(1, 7)]),
                    ([F(1, 7), F(1, 8), F(1, 9), F(1, 10)],
                     [F(1, 21), F(1, 22), F(1, 23), F(1, 24)])]
        for d, v in controls:
            with self.subTest(d=d, v=v):
                row = coarse_grid(d, v)
                self.assertEqual(F(row['risk']), independent_grid(d, v))
                self.assertEqual(row['points_evaluated'], 3 ** len(d))
                x = list(map(F, row['x']))
                attained = (sum(v) + sum(di * xi for di, xi in zip(d, x)) ** 2
                            - sum(vi * xi * xi for vi, xi in zip(v, x))) / 4
                self.assertEqual(attained, F(row['risk']))

    def test_grid_rejects_invalid_dimension_and_negative_coefficients(self):
        for d, v in [([], []), ([0], []), ([-1], [1]), ([1], [-1])]:
            with self.subTest(d=d, v=v), self.assertRaises(ValueError):
                coarse_grid(d, v)

    def test_tie_dependent_gain_is_exposed(self):
        row = exact_choice(['1/10', '1/10', '1/5'], ['3/20', '1/10', '1/5'])
        self.assertEqual(row['chosen'], 0)
        self.assertEqual(row['minimizers'], [0, 1])
        self.assertEqual(F(row['selected_regret']), F(1, 20))
        self.assertEqual(F(row['best_tied_regret']), 0)
        self.assertEqual(F(row['worst_tied_regret']), F(1, 20))

    def test_tie_robust_gain_requires_every_grid_minimizer_bad(self):
        row = exact_choice(['1/10', '1/10', '11/100'],
                           ['3/20', '1/5', '11/100'])
        self.assertEqual(row['minimizers'], [0, 1])
        self.assertEqual(F(row['best_tied_regret']), F(1, 25))
        self.assertEqual(F(row['worst_tied_regret']), F(9, 100))

    def test_correct_different_tied_choices_have_no_regret(self):
        row = exact_choice(['1/8', '1/8', '1/4'], ['1/8', '1/8', '1/4'])
        self.assertEqual(row['chosen'], 0)
        self.assertEqual(F(row['best_tied_regret']), 0)
        self.assertEqual(F(row['worst_tied_regret']), 0)

    def test_choice_rejects_incomplete_arrays(self):
        for values, truth in [([], []), (['1/4'], []), ([], ['1/4'])]:
            with self.subTest(values=values, truth=truth), self.assertRaises(ValueError):
                exact_choice(values, truth)

    def test_invalid_scenario_controls(self):
        base = toy(['1/3', '2/3'], '1',
                   [{'powered': True, 'eligible': [0, 1]}])
        mutations = [
            ('weights', ['1/3', '1/3']),
            ('weights', ['-1', '2']),
            ('weights', ['0', '1']),
            ('shrinkage', '-1'),
            ('budget', 0),
            ('budget', True),
            ('calendar', [{'powered': 1, 'eligible': [0, 1]}]),
            ('calendar', [{'powered': True, 'eligible': []}]),
            ('calendar', [{'powered': True, 'eligible': [1, 0]}]),
            ('calendar', [{'powered': True, 'eligible': [0, 0]}]),
            ('calendar', [{'powered': True, 'eligible': [2]}]),
            ('calendar', [{'powered': True, 'eligible': [-1]}]),
            ('calendar', [{'powered': True, 'eligible': [False]}]),
        ]
        for field, value in mutations:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                scenario = copy.deepcopy(base)
                scenario[field] = value
                validate(scenario)

    def test_invalid_count_controls(self):
        scenario = toy(['1/3', '2/3'], '1', [])
        for counts in [[], [1], [0, -1], [0, 1.0], [False, 1]]:
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                estimator_inputs(scenario, counts)


if __name__ == '__main__':
    unittest.main()
