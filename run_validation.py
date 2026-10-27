"""Frozen finite original validation; never calls a model. SPDX-License-Identifier: MIT."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent
if (ROOT / '.deps').is_dir():
    sys.path.insert(0, str(ROOT / '.deps'))
import argparse
from fractions import Fraction as F
from itertools import product
from math import comb
import hashlib
import importlib.metadata
import json
import platform
import statistics
from datetime import datetime, timezone
from time import perf_counter
import warnings
from oracle import from_estimator
from reference import maximize_reference
from check_certificate import verify
from socp_baseline import solve as conic_solve


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8')


def frozen_paths():
    return sorted(['PROTOCOL.md','synthetic_inputs.json','make_inputs.py','oracle.py',
                   'check_certificate.py','reference.py','socp_baseline.py',
                   'run_validation.py','requirements-benchmark.txt'] +
                  [p.relative_to(ROOT).as_posix() for p in (ROOT/'tests').glob('test_*.py')])


def freeze():
    target = ROOT/'freeze.json'
    if target.exists():
        raise SystemExit('Existing freeze will not be replaced')
    versions = {n:importlib.metadata.version(n) for n in
                ('cvxpy','clarabel','numpy','scipy','scs','osqp','cffi')}
    dump(target, {'created_utc':now(), 'files':{p:digest(ROOT/p) for p in frozen_paths()},
                  'runtime':sys.version, 'dependencies':versions, 'model_budget':0,
                  'external_inference_usd':0,'between_case_wall_budget_seconds':600})
    print('Frozen', len(frozen_paths()), 'files')


def check_freeze():
    frozen = json.loads((ROOT/'freeze.json').read_text(encoding='utf-8'))
    if any(digest(ROOT/p) != h for p,h in frozen['files'].items()):
        raise RuntimeError('Frozen file changed')
    return frozen


def direct_expectation(w, n, a, x):
    p = [(1+xi)/2 for xi in x]
    theta = sum(wi*pi for wi,pi in zip(w,p))
    pmfs = [[(ki, F(comb(ni,ki))*pi**ki*(1-pi)**(ni-ki)) for ki in range(ni+1)]
            for ni,pi in zip(n,p)]
    total = F(0)
    for outcome in product(*pmfs):
        prob, estimate = F(1), F(1,2)
        for (ki,pk),ni,ai in zip(outcome,n,a):
            prob *= pk
            if ni:
                estimate += ai*(F(ki,ni)-F(1,2))
        total += prob*(estimate-theta)**2
    return total


def grid_risk(d,v):
    best = F(-1)
    points = (F(-1),F(-1,2),F(0),F(1,2),F(1))
    for x in product(points,repeat=len(d)):
        risk = (sum(v)+sum(di*xi for di,xi in zip(d,x))**2
                -sum(vi*xi*xi for vi,xi in zip(v,x)))/4
        best = max(best,risk)
    return best


def summarize(rows, status):
    small = [r for r in rows if r['group']=='small']
    shared = [r for r in rows if r['group']=='shared']
    grids = [r for r in rows if 'grid_risk' in r]
    conics = [r for r in rows if 'conic' in r]
    ratios = [r['conic']['time_seconds']/(r['exact_seconds']+r['check_seconds'])
              for r in shared if r['conic']['numerically_accepted']]
    correctness = (status=='complete' and len(rows)==148 and len(small)==128 and
                   sum(r.get('reference_match',False) for r in rows)==128 and
                   sum(r.get('expectation_match',False) for r in rows)==16 and
                   all(r.get('certificate_valid') and r.get('reference_match',True)
                       and r.get('expectation_match',True) for r in rows))
    grid_under = sum(F(r['grid_risk']) < F(r['certificate']['risk']) for r in grids)
    return {'status':status, 'completed_cases':len(rows),
            'certificates_valid':sum(r.get('certificate_valid',False) for r in rows),
            'reference_matches':sum(r.get('reference_match',False) for r in rows),
            'expectation_matches':sum(r.get('expectation_match',False) for r in rows),
            'grid_cases':len(grids),'grid_understatements':grid_under,
            'conic_cases':len(conics),
            'conic_actual_calls':sum(r['conic']['solver_calls'] for r in conics),
            'conic_numerically_accepted':sum(r['conic']['numerically_accepted'] for r in conics),
            'conic_risk_agreements_1e_7':bool(conics) and all(r.get('conic_risk_error') is not None
                                            and r['conic_risk_error']<=1e-7 for r in conics),
            'conic_max_abs_risk_error':max((r['conic_risk_error'] for r in conics
                                           if r.get('conic_risk_error') is not None),default=None),
            'shared_time_ratios':ratios,
            'shared_median_time_ratio':statistics.median(ratios) if ratios else None,
            'correctness_gate':correctness,
            'operational_value_gate':bool(correctness and grid_under>0 and len(ratios)==8
                                          and statistics.median(ratios)>=2),
            'maximum_certificate_rational_bits':max((r.get('max_bits',0) for r in rows),default=0),
            'interpretation':'One deterministic software-validation suite; no statistical or patent-novelty claim'}


def run():
    frozen = check_freeze()
    import cvxpy, numpy  # Import cost explicitly excluded from timing.
    target = ROOT/'results'
    target.mkdir(exist_ok=True)
    guard = target/'RUN_GUARD.json'
    with guard.open('x',encoding='utf-8') as stream:
        json.dump({'started_utc':now(),'freeze_sha256':digest(ROOT/'freeze.json')},stream)
    started_utc, started = now(), perf_counter()
    rows, status = [], 'complete'
    current_id, row = None, None
    try:
        cases = json.loads((ROOT/'synthetic_inputs.json').read_text(encoding='utf-8'))['cases']
        with (target/'rows.jsonl').open('x',encoding='utf-8') as stream:
            for case in cases:
                if perf_counter()-started > 600:
                    status='budget_stop'; break
                current_id, row = case['id'], None
                w,a,n=list(map(F,case['w'])),list(map(F,case['a'])),case['n']
                tick=perf_counter()
                d,v,c=from_estimator(w,n,a)
                row={'id':case['id'],'group':case['group'],'k':len(w),
                     'exact_seconds':perf_counter()-tick, 'certificate':c.to_dict()}
                tick=perf_counter()
                row['certificate_valid']=verify(d,v,row['certificate'])
                row['check_seconds']=perf_counter()-tick
                rationals=list(c.x)+list(c.loading)+[c.t,c.objective,c.risk]
                row['max_bits']=max(max(z.numerator.bit_length(),z.denominator.bit_length()) for z in rationals)
                if case['reference']:
                    tick=perf_counter(); ref=maximize_reference(d,v)
                    row.update(reference_seconds=perf_counter()-tick,
                               reference_risk=str(ref.risk), reference_match=ref.risk==c.risk,
                               reference_faces=ref.faces_examined)
                if case['grid']:
                    tick=perf_counter(); grid=grid_risk(d,v)
                    row.update(grid_risk=str(grid),grid_seconds=perf_counter()-tick)
                if case['expectation']:
                    tick=perf_counter(); expected=direct_expectation(w,n,a,c.x)
                    row.update(expectation_risk=str(expected),expectation_match=expected==c.risk,
                               expectation_seconds=perf_counter()-tick)
                if case['conic']:
                    with warnings.catch_warnings(record=True) as seen:
                        warnings.simplefilter('always')
                        row['conic']=conic_solve(d,v)
                    row['conic_warnings']=[str(item.message) for item in seen]
                    r=row['conic']['risk']
                    row['conic_risk_error']=abs(r-float(c.risk)) if r is not None else None
                rows.append(row)
                stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n'); stream.flush()
                if not row['certificate_valid'] or not row.get('reference_match',True) or not row.get('expectation_match',True):
                    status='correctness_failure'; break
    except Exception as error:
        status='execution_error'
        dump(target/'error.json',{'type':type(error).__name__,'message':str(error),
                                 'case_id':current_id,'partial_case':row})
        raise
    finally:
        try:
            check_freeze()
        except Exception as error:
            status='freeze_drift'
            dump(target/'freeze_error.json',{'type':type(error).__name__,'message':str(error)})
        summary=summarize(rows,status)
        dump(target/'summary.json',summary)
        dump(target/'receipt.json',{'started_utc':started_utc,'finished_utc':now(),
             'wall_seconds':perf_counter()-started,'status':status,'platform':platform.platform(),
             'python':sys.version,'freeze_sha256':digest(ROOT/'freeze.json'),
             'fixture_sha256':digest(ROOT/'synthetic_inputs.json'),
             'raw_rows_sha256':digest(target/'rows.jsonl') if (target/'rows.jsonl').exists() else None,
             'model_calls':0,'external_inference_usd':0,'dependencies':frozen['dependencies']})
        print(json.dumps(summary,sort_keys=True))


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['freeze','run'])
    args=p.parse_args()
    freeze() if args.action=='freeze' else run()
