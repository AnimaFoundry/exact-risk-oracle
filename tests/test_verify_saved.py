"""Post-run checker unit tests; no optimizer, enumeration or benchmark replay.

These exposed synthetic mutations were written after the finite experiment.
They are not part of the original frozen solver validation or a new holdout.
"""

from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_saved import AuditFailure, audit_certificate, audit_conic, decode


def certificate_toy():
    case = {"id": "post-run-toy", "group": "development", "w": ["1"],
            "a": ["1/2"], "n": [1]}
    row = {"id": case["id"], "group": case["group"], "k": 1,
           "certificate": {"x": ["0"], "loading": ["0"], "t": "0",
                           "objective": "0", "risk": "1/16", "intervals": 0},
           "certificate_valid": True, "max_bits": 5,
           "exact_seconds": 1.0, "check_seconds": 1.0}
    return case, row


def zero_bias_conic_toy():
    return {"id": "post-run-conic-toy", "conic_risk_error": 0.0,
            "conic": {"dimension": 1, "active_dimension": 0, "solver": "CLARABEL",
                      "solver_options": {"max_iter": 200, "tol_feas": 1e-10,
                                         "tol_gap_abs": 1e-10, "tol_gap_rel": 1e-10},
                      "objective_is_exact_certificate": False, "time_seconds": 0.0,
                      "solver_calls": 0, "residual_tolerance": 1e-7, "risk": 0.25,
                      "lambda": [0.0], "objective": 0.0, "status": "analytic_zero_d",
                      "numerically_accepted": True}}


class IndependentReplayMutationTests(unittest.TestCase):
    def test_original_toy_is_valid(self):
        case, row = certificate_toy()
        d, v, risk, bits = audit_certificate(case, row)
        self.assertEqual((d, v, risk, bits), ((F(1, 2),), (F(1, 4),), F(1, 16), 5))

    def test_infeasible_witness_is_rejected(self):
        case, row = certificate_toy()
        row["certificate"]["x"] = ["2"]
        with self.assertRaises(AuditFailure):
            audit_certificate(case, row)

    def test_nonattaining_witness_is_rejected(self):
        case, row = certificate_toy()
        row["certificate"]["loading"] = ["1"]
        row["certificate"]["objective"] = "1"
        row["certificate"]["risk"] = "5/16"
        with self.assertRaises(AuditFailure):
            audit_certificate(case, row)

    def test_negative_loading_is_rejected(self):
        case, row = certificate_toy()
        row["certificate"]["loading"] = ["-1"]
        with self.assertRaises(AuditFailure):
            audit_certificate(case, row)

    def test_risk_and_summary_flag_tampering_is_rejected(self):
        case, original = certificate_toy()
        row = deepcopy(original)
        row["certificate"]["risk"] = "0"
        with self.assertRaises(AuditFailure):
            audit_certificate(case, row)
        row = deepcopy(original)
        row["certificate_valid"] = False
        with self.assertRaises(AuditFailure):
            audit_certificate(case, row)

    def test_unobserved_nonzero_coefficient_is_rejected(self):
        case, row = certificate_toy()
        case["n"] = [0]
        with self.assertRaises(AuditFailure):
            audit_certificate(case, row)

    def test_zero_denominator_with_nonzero_bias_is_rejected(self):
        case, row = certificate_toy()
        case["a"] = ["0"]
        row["certificate"]["risk"] = "0"
        with self.assertRaises(AuditFailure):
            audit_certificate(case, row)

    def test_duplicate_json_keys_and_nonfinite_numbers_are_rejected(self):
        for text in ('{"x": 0, "x": 1}', '{"x": NaN}', '{"x": Infinity}'):
            with self.assertRaises(AuditFailure):
                decode(text)

    def test_zero_bias_conic_record_and_acceptance_tampering(self):
        row = zero_bias_conic_toy()
        result = audit_conic(row, (F(0),), (F(1),), F(1, 4))
        self.assertTrue(result["accepted"])
        row["conic"]["numerically_accepted"] = False
        with self.assertRaises(AuditFailure):
            audit_conic(row, (F(0),), (F(1),), F(1, 4))

    def test_missing_risk_cannot_be_accepted(self):
        row = zero_bias_conic_toy()
        row["conic"]["risk"] = None
        row["conic_risk_error"] = None
        with self.assertRaises(AuditFailure):
            audit_conic(row, (F(0),), (F(1),), F(1, 4))


if __name__ == "__main__":
    unittest.main()
