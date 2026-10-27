"""Exogenous sampling calendars and exact decision scoring. SPDX-License-Identifier: MIT.

No risk oracle or optimizer is imported. Candidate generation sees no outcomes.
"""
from fractions import Fraction as F
from itertools import product


def validate(scenario):
    if any(isinstance(z, bool) or not isinstance(z, (str, int, F))
           for z in list(scenario['weights']) + [scenario['shrinkage']]):
        raise TypeError('exact rational strings, integers or Fractions required')
    w = tuple(F(z) for z in scenario['weights'])
    k = len(w)
    if not 1 <= k <= 4 or any(z <= 0 for z in w) or sum(w) != 1:
        raise ValueError('positive normalized weights, dimension 1..4 required')
    c = F(scenario['shrinkage'])
    if c < 0:
        raise ValueError('nonnegative shrinkage required')
    slots = scenario['calendar']
    for slot in slots:
        if type(slot['powered']) is not bool:
            raise ValueError('powered must be boolean')
        e = slot['eligible']
        if not isinstance(e, list) or not e or e != sorted(set(e)):
            raise ValueError('nonempty sorted distinct eligible list required')
        if any(type(i) is not int or i < 0 or i >= k for i in e):
            raise ValueError('invalid eligible stratum')
    if type(scenario['budget']) is not int or scenario['budget'] != sum(s['powered'] for s in slots):
        raise ValueError('budget must equal powered opportunities')
    return w, c


def enumerate_candidates(scenario):
    """All feasible count vectors; retain one lexicographic schedule per vector.

    -1 is idle. Energy is exogenous, unit cost, and cannot carry between slots.
    This is a finite offline design, not an outcome-adaptive sampling policy.
    """
    w, _ = validate(scenario)
    reachable = {(0,) * len(w): ()}
    for slot in scenario['calendar']:
        choices = [-1] + slot['eligible'] if slot['powered'] else [-1]
        updated = {}
        for counts, schedule in reachable.items():
            for action in choices:
                nxt = list(counts)
                if action >= 0:
                    nxt[action] += 1
                nxt = tuple(nxt)
                path = schedule + (action,)
                if nxt not in updated or path < updated[nxt]:
                    updated[nxt] = path
        reachable = updated
    return [{'counts': list(n), 'schedule': list(reachable[n])} for n in sorted(reachable)]


def estimator_inputs(scenario, counts):
    w, c = validate(scenario)
    if len(counts) != len(w) or any(type(n) is not int or n < 0 for n in counts):
        raise ValueError('invalid counts')
    a = tuple(wi * ni / (ni + c) if ni else F(0) for wi, ni in zip(w, counts))
    d = tuple(wi - ai for wi, ai in zip(w, a))
    v = tuple(ai * ai / ni if ni else F(0) for ai, ni in zip(a, counts))
    return w, a, d, v


def coarse_grid(d, v):
    """Exact maximum on p={0,1/4,1/2,3/4,1}^k.

    d>=0 permits absolute-value symmetry reduction to x={0,1/2,1}^k,
    exactly equivalent to the full signed grid. No adaptive refinement.
    """
    d, v = tuple(map(F, d)), tuple(map(F, v))
    if len(d) != len(v) or not d or any(z < 0 for z in d + v):
        raise ValueError('equal nonnegative vectors required')
    best, witness = F(-1), None
    for x in product((F(0), F(1, 2), F(1)), repeat=len(d)):
        risk = (sum(v) + sum(di * xi for di, xi in zip(d, x)) ** 2
                - sum(vi * xi * xi for vi, xi in zip(v, x))) / 4
        if risk > best:
            best, witness = risk, x
    return {'risk': str(best), 'x': list(map(str, witness)), 'points_evaluated': 3 ** len(d)}


def exact_choice(values, truth):
    """Shared lexicographic-first tie rule; also expose every tied decision."""
    values, truth = list(map(F, values)), list(map(F, truth))
    if not values or len(values) != len(truth):
        raise ValueError('equal nonempty values and truths required')
    winners = [i for i, value in enumerate(values) if value == min(values)]
    optimum = min(truth)
    regrets = [truth[i] - optimum for i in winners]
    return {'chosen': winners[0], 'minimizers': winners,
            'reported_minimum': str(min(values)), 'selected_risk': str(truth[winners[0]]),
            'selected_regret': str(regrets[0]), 'best_tied_regret': str(min(regrets)),
            'worst_tied_regret': str(max(regrets))}
