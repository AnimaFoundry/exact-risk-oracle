"""Frozen decision scoring from all saved rows. SPDX-License-Identifier: MIT."""
from collections import Counter
from fractions import Fraction as F
import statistics
from decision.design import exact_choice


def conic_choice(rows, truth):
    if not all(r['conic']['numerically_accepted'] and r['conic']['risk'] is not None for r in rows):
        return {'status': 'INCONCLUSIVE_NUMERICAL_FAILURE'}
    vals = [r['conic']['risk'] for r in rows]
    minimum = min(vals)
    near = [i for i, value in enumerate(vals) if value <= minimum + 1e-7]
    optimum = min(truth)
    return {'status': 'accepted', 'chosen': near[0], 'numerical_near_set': near,
            'selected_risk': str(truth[near[0]]), 'selected_regret': str(truth[near[0]] - optimum),
            'best_near_regret': str(min(truth[i] for i in near) - optimum),
            'worst_near_regret': str(max(truth[i] for i in near) - optimum),
            'includes_exact_optimum': any(truth[i] == optimum for i in near)}


def summarize(inputs, rows, setups, status):
    decisions, complete_ids = [], []
    for s in inputs['scenarios']:
        batches = [[r for r in rows if r['scenario'] == s['id'] and r['pass'] == rep]
                   for rep in range(3)]
        if any(len(b) != len(s['candidates']) or any('conic' not in r or 'grid' not in r or 'exact' not in r for r in b)
               for b in batches):
            continue
        for b in batches:
            b.sort(key=lambda r: r['candidate'])
        truth = [F(r['exact']['risk']) for r in batches[0]]
        per_pass = []
        for rep, b in enumerate(batches):
            times = {m: sum(r[m + '_seconds'] for r in b) for m in ('grid', 'exact', 'conic')}
            times['conic_with_build_seconds'] = times['conic'] + (setups[s['id']]['build_seconds'] if rep == 0 else 0)
            per_pass.append({'pass': rep, 'exact': exact_choice([r['exact']['risk'] for r in b], truth),
                             'grid': exact_choice([r['grid']['risk'] for r in b], truth),
                             'conic': conic_choice(b, truth), 'times': times,
                             'conic_to_exact_ratio': times['conic_with_build_seconds'] / times['exact']})
        first = per_pass[0]
        decisions.append({'scenario': s['id'], 'candidates': len(truth),
                          'optimal_risk': str(min(truth)), 'passes': per_pass,
                          'tie_robust_gain': F(first['grid']['best_tied_regret']) > 0,
                          'any_grid_tie_regret': F(first['grid']['worst_tied_regret']) > 0,
                          'selected_grid_regret': first['grid']['selected_regret'],
                          'grid_choice_stable': len({p['grid']['chosen'] for p in per_pass}) == 1,
                          'conic_choice_stable': (all(p['conic']['status'] == 'accepted' for p in per_pass)
                                                   and len({p['conic']['chosen'] for p in per_pass}) == 1)})
        complete_ids.append(s['id'])
    full_rows = [r for r in rows if all(m in r for m in ('exact','grid','conic'))]
    first_rows = [r for r in full_rows if r['pass'] == 0]
    expected = sum(len(s['candidates']) for s in inputs['scenarios'])
    correct = (status == 'complete' and len(complete_ids) == 48 and len(full_rows) == expected * 3
               and all(r.get('certificate_valid') and F(r['grid']['risk']) <= F(r['exact']['risk']) for r in full_rows)
               and len(first_rows) == expected and all(r.get('reference_match') for r in first_rows))
    accepted = [r for r in full_rows if r['conic']['numerically_accepted']]
    errors = [abs(r['conic']['risk'] - float(F(r['exact']['risk']))) for r in full_rows if r['conic']['risk'] is not None]
    conic_ok = (correct and len(accepted) == len(full_rows) and all(e <= 1e-7 for e in errors))
    robust = sum(d['tie_robust_gain'] for d in decisions)
    any_tie = sum(d['any_grid_tie_regret'] for d in decisions)
    label = ('INCONCLUSIVE' if not correct else 'TIE_ROBUST_GAIN_OBSERVED' if robust else
             'TIE_DEPENDENT_ONLY' if any_tie else 'NO_DECISION_GAIN_OBSERVED')
    cold = [d['passes'][0]['conic_to_exact_ratio'] for d in decisions]
    warm = [statistics.median(p['conic_to_exact_ratio'] for p in d['passes'][1:]) for d in decisions]
    def stats(x):
        return {'median': statistics.median(x), 'min': min(x), 'max': max(x)} if x else None
    return {'status': status, 'scenarios_completed': len(complete_ids), 'unique_allocations_expected': expected,
            'rows_completed': len(full_rows), 'certificate_valid': sum(r.get('certificate_valid',False) for r in full_rows),
            'reference_matches': sum(r.get('reference_match',False) for r in first_rows),
            'grid_understatements_first_pass': sum(F(r['grid']['risk']) < F(r['exact']['risk']) for r in first_rows),
            'conic_accepted': len(accepted), 'conic_actual_solves': sum(r['conic']['solver_calls'] for r in full_rows),
            'conic_status_counts': dict(Counter(r['conic']['status'] for r in full_rows)),
            'conic_max_absolute_risk_error': max(errors) if errors else None,
            'conic_warning_records': sum(bool(r['conic']['warnings']) for r in full_rows),
            'correctness_gate': correct, 'conic_comparison_gate': conic_ok,
            'decision_result': label, 'tie_robust_gain_scenarios': robust,
            'any_grid_tie_regret_scenarios': any_tie,
            'selected_grid_regret_scenarios': sum(F(d['selected_grid_regret']) > 0 for d in decisions),
            'cold_ratio_descriptive_all': stats(cold), 'warm_ratio_descriptive_all': stats(warm),
            'speed_claim_eligible': conic_ok,
            'speed_2x_gate': bool(conic_ok and warm and statistics.median(warm) >= 2),
            'decisions': decisions}
