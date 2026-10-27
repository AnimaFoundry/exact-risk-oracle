"""Handwritten scoring controls; no evaluation inputs. MIT license."""
from fractions import Fraction as F
from pathlib import Path
import sys
import json
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from decision.scoring import conic_choice, summarize
from decision.design import exact_choice
from decision.design import validate


class ScoringControls(unittest.TestCase):
    def test_floating_contract_is_rejected(self):
        for weights,c in [([0.5,0.5],'0'), (['1/2','1/2'],True)]:
            with self.assertRaises(TypeError):
                validate({'weights':weights,'shrinkage':c})
    def test_grid_tie_not_robust(self):
        c=exact_choice(['1','1'],['2','1'])
        self.assertEqual(c['chosen'],0)
        self.assertEqual(c['selected_regret'],'1')
        self.assertEqual(c['best_tied_regret'],'0')

    def test_robust_grid_regret(self):
        c=exact_choice(['0','0','1'],['3','2','1'])
        self.assertEqual(c['best_tied_regret'],'1')

    def test_conic_failure_not_subset_selection(self):
        r=[{'conic':{'numerically_accepted':True,'risk':0.0}},
           {'conic':{'numerically_accepted':False,'risk':1.0}}]
        self.assertEqual(conic_choice(r,[F(0),F(1)])['status'],'INCONCLUSIVE_NUMERICAL_FAILURE')

    def test_conic_near_tie_uses_no_exact_answer(self):
        r=[{'conic':{'numerically_accepted':True,'risk':0.1+1e-8}},
           {'conic':{'numerically_accepted':True,'risk':0.1}}]
        c=conic_choice(r,[F(11,100),F(1,10)])
        self.assertEqual(c['chosen'],0)
        self.assertTrue(c['includes_exact_optimum'])
        self.assertEqual(c['selected_regret'],'1/100')

    def test_incomplete_never_passes(self):
        s=summarize({'scenarios':[]},[],{},'complete')
        self.assertFalse(s['correctness_gate'])
        self.assertEqual(s['decision_result'],'INCONCLUSIVE')

    def test_nonfinite_failure_is_durable_json(self):
        from decision.run import saved_safe
        data={'accepted':False,'vector':[float('nan'),float('inf'),float('-inf')], 'risk':None}
        saved=json.loads(json.dumps(saved_safe(data),allow_nan=False))
        self.assertFalse(saved['accepted'])
        self.assertEqual(saved['vector'],[{'nonfinite_float':'nan'}, {'nonfinite_float':'inf'},
                                           {'nonfinite_float':'-inf'}])
        self.assertIsNone(saved['risk'])


if __name__=='__main__': unittest.main()
