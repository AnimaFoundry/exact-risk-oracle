"""Post-freeze handwritten mutation controls for independent saved replay."""
import copy
from fractions import Fraction as F
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from decision.verify_saved import (certificate_check, choice, conic_check,
                                    grid_check, numerical_choice, parse,
                                    scenario_check)


def scalar_certificate():
    return {"x":["1"], "loading":["1/18"], "objective":"1/18", "risk":"1/36"}


def scalar_conic():
    return {"dimension":1, "active_dimension":1, "is_dpp":True,
            "enforce_dpp":True, "warm_start_requested":True,
            "solver_options":{"tol_gap_abs":1e-10,"tol_gap_rel":1e-10,
                              "tol_feas":1e-10,"max_iter":200},
            "residual_tolerance":1e-7, "objective_is_exact_certificate":False,
            "status":"optimal", "solver_calls":1,
            "normalization_scale_exact":"1", "normalization_scale":1.0,
            "lambda_normalized":[1.0], "epigraph":[1.0], "lambda":[1.0],
            "objective":1.0, "risk":0.25, "solver_objective":1.0,
            "numerically_accepted":True,
            "residuals":{"positive_active_denominators":True, "finite":True,
                         "nonnegative_violation_normalized":0.0,
                         "epigraph_nonnegative_violation":0.0,
                         "soc_violation":0.0, "epigraph_sum_violation":0.0,
                         "cone_violation":0.0,"cone_sum":1.0,
                         "objective_disagreement_normalized":0.0,"accepted":True}}


class IndependentDecisionEvidenceTests(unittest.TestCase):
    def test_certificate_valid_and_not_reliant_on_search_metadata(self):
        self.assertEqual(certificate_check([F(1,3)],[F(1,18)],scalar_certificate()),F(1,36))

    def test_certificate_objective_risk_witness_and_bound_mutations(self):
        for field, value in [("risk","1/35"),("objective","1/19"),
                             ("x",["0"]),("loading",["0"]),("x",["2"])]:
            c=scalar_certificate()
            c[field]=value
            with self.subTest(field=field,value=value), self.assertRaises(AssertionError):
                certificate_check([F(1,3)],[F(1,18)],c)

    def test_zero_denominator_and_negative_loading_rejected(self):
        for loading in ("0","-1"):
            c={"x":["0"],"loading":[loading],"objective":"0","risk":"0"}
            with self.assertRaises(AssertionError):
                certificate_check([F(1)],[F(0)],c)

    def test_signed_grid_and_wrong_maximum(self):
        record={"x":["1"],"risk":"1/36","points_evaluated":3}
        self.assertEqual(grid_check([F(1,3)],[F(1,18)],record),F(1,36))
        record["risk"]="1/37"
        with self.assertRaises(AssertionError):
            grid_check([F(1,3)],[F(1,18)],record)

    def test_full_schedule_candidate_reconstruction(self):
        scenario={"weights":["1/4","3/4"],"shrinkage":"0","budget":2,
                  "calendar":[{"powered":True,"eligible":[1]}]*2,
                  "candidates":[{"counts":[0,0],"schedule":[-1,-1]},
                                {"counts":[0,1],"schedule":[-1,1]},
                                {"counts":[0,2],"schedule":[1,1]}]}
        derived=scenario_check(scenario)
        self.assertEqual(derived[0],((F(1,4),F(3,4)),(F(0),F(0))))
        scenario["candidates"].pop(1)
        with self.assertRaises(AssertionError):
            scenario_check(scenario)

    def test_conic_attaining_scalar_point(self):
        self.assertTrue(conic_check([F(1)],[F(0)],scalar_conic()))

    def test_conic_mutated_risk_and_options_rejected(self):
        for field, value in [("risk",0.24),("normalization_scale",2.0),
                             ("lambda",[2.0]),("solver_calls",2),
                             ("warm_start_requested",False)]:
            record=scalar_conic()
            record[field]=value
            with self.subTest(field=field), self.assertRaises(AssertionError):
                conic_check([F(1)],[F(0)],record)

    def test_inaccurate_status_cannot_be_promoted(self):
        record=scalar_conic()
        record["status"]="optimal_inaccurate"
        with self.assertRaises(AssertionError):
            conic_check([F(1)],[F(0)],record)
        record["numerically_accepted"]=False
        self.assertFalse(conic_check([F(1)],[F(0)],record))

    def test_finite_vector_status_cannot_be_contradictory(self):
        record=scalar_conic()
        record["residuals"]["finite"]=False
        with self.assertRaises(AssertionError):
            conic_check([F(1)],[F(0)],record)

    def test_solver_error_retained_as_rejection(self):
        record=scalar_conic()
        record.update(status="solver_error",numerically_accepted=False)
        self.assertFalse(conic_check([F(1)],[F(0)],record))

    def test_nonfinite_evidence_is_not_accepted(self):
        record=scalar_conic()
        record["lambda_normalized"]=[{"nonfinite_float":"nan"}]
        record["numerically_accepted"]=False
        record["residuals"]["finite"]=False
        self.assertFalse(conic_check([F(1)],[F(0)],record))
        record["numerically_accepted"]=True
        with self.assertRaises(AssertionError):
            conic_check([F(1)],[F(0)],record)

    def test_exact_tie_regret_is_not_robust(self):
        result=choice([F(1),F(1)],[F(2),F(1)])
        self.assertEqual(result["selected_regret"],"1")
        self.assertEqual(result["best_tied_regret"],"0")

    def test_numerical_near_set_uses_no_truth_for_choice(self):
        rows=[{"conic":{"numerically_accepted":True,"risk":0.2+1e-8}},
              {"conic":{"numerically_accepted":True,"risk":0.2}}]
        result=numerical_choice(rows,[F(3,10),F(1,5)])
        self.assertEqual(result["chosen"],0)
        self.assertEqual(result["selected_regret"],"1/10")
        rows[0]["conic"]["numerically_accepted"]=False
        self.assertEqual(numerical_choice(rows,[F(3,10),F(1,5)]),
                         {"status":"INCONCLUSIVE_NUMERICAL_FAILURE"})

    def test_duplicate_keys_and_invalid_json_float_rejected(self):
        for text in ('{"status":true,"status":false}', '{"risk":NaN}', '{"risk":Infinity}'):
            with self.subTest(text=text), self.assertRaises((AssertionError,ValueError)):
                parse(text)


if __name__=="__main__":
    unittest.main()
