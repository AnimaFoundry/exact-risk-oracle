"""One guarded authorized decision cohort, never model inference. MIT license."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if (ROOT / '.deps').is_dir():
    sys.path.insert(0, str(ROOT / '.deps'))
import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import importlib.metadata
import json
import math
import platform
from time import perf_counter
from oracle import solve
from check_certificate import verify
from reference import maximize_reference
from decision.design import estimator_inputs
from decision.design import coarse_grid
from decision.reusable_conic import ReusableConic
from decision.scoring import summarize

D = ROOT / 'decision'


def now():
    return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p, obj):
    p.write_text(json.dumps(saved_safe(obj), indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


def saved_safe(obj):
    """Preserve non-finite rejected evidence without emitting invalid JSON."""
    if isinstance(obj, float) and not math.isfinite(obj):
        return {'nonfinite_float': str(obj)}
    if isinstance(obj, dict):
        return {key: saved_safe(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [saved_safe(value) for value in obj]
    return obj


def frozen_paths():
    return ['oracle.py','check_certificate.py','reference.py','requirements-benchmark.txt',
            'decision/__init__.py','decision/design.py','decision/make_inputs.py','decision/inputs.json',
            'decision/PROTOCOL.md','decision/scoring.py','decision/reusable_conic.py','decision/run.py',
            'tests/test_decision_design.py','tests/test_decision_conic.py','tests/test_decision_scoring.py']


def versions():
    return {n: importlib.metadata.version(n) for n in ('cvxpy','clarabel','numpy','scipy','scs','osqp','cffi')}


def freeze():
    p = D / 'freeze.json'
    if p.exists():
        raise SystemExit('Existing freeze will not be replaced')
    inputs = json.loads((D / 'inputs.json').read_text(encoding='utf-8'))
    count = sum(len(s['candidates']) for s in inputs['scenarios'])
    if len(inputs['scenarios']) != 48 or count > 1344:
        raise ValueError('input budget exceeded')
    dump(p, {'created_utc': now(), 'files': {q: digest(ROOT/q) for q in frozen_paths()},
             'python': sys.version, 'dependencies': versions(), 'scenarios':48,
             'unique_allocations':count, 'calls_per_method':count*3,'max_calls_per_method':4032,
             'max_reference_calls':1344,'between_call_wall_seconds':900,
             'model_calls':0, 'external_api_usd':0})
    print('Frozen', count, 'unique allocations;', count*3, 'calls per method')


def check_freeze():
    f = json.loads((D/'freeze.json').read_text(encoding='utf-8'))
    if any(digest(ROOT/q) != h for q,h in f['files'].items()):
        raise RuntimeError('Frozen file changed')
    if f['dependencies'] != versions():
        raise RuntimeError('Dependencies changed')
    return f


def run():
    f = check_freeze()
    import cvxpy, numpy  # exclude optional import startup from all method timers
    out = D / 'results'
    out.mkdir(exist_ok=True)
    guard = out / 'RUN_GUARD.json'
    with guard.open('x', encoding='utf-8') as g:
        json.dump({'started_utc':now(),'freeze_sha256':digest(D/'freeze.json'),
                   'purpose':'one frozen decision queue; never delete to retry'},g,indent=2)
    started_utc, start = now(), perf_counter()
    inputs = json.loads((D/'inputs.json').read_text(encoding='utf-8'))
    rows, setups, status, failure = [], {}, 'complete', None
    def budget():
        if perf_counter() - start >= 900:
            raise TimeoutError('900-second between-call budget exhausted')
    current = None
    with (out/'rows.jsonl').open('x', encoding='utf-8') as raw:
        try:
            for s in inputs['scenarios']:
                budget()
                conic = ReusableConic(len(s['weights']))
                setups[s['id']] = {'build_seconds':conic.build_seconds,'is_dpp':conic.is_dpp}
                for rep in range(3):
                    order = (('grid','exact','conic'),('exact','conic','grid'),('conic','grid','exact'))[rep]
                    for index, candidate in enumerate(s['candidates']):
                        budget()
                        w,a,d,v = estimator_inputs(s, candidate['counts'])
                        current = {'scenario':s['id'],'pass':rep,'candidate':index,
                                   'counts':candidate['counts'], 'method_order':list(order),
                                   'd':list(map(str,d)), 'v':list(map(str,v))}
                        for method in order:
                            budget()
                            tick = perf_counter()
                            if method == 'grid':
                                current['grid'] = coarse_grid(d,v)
                            elif method == 'exact':
                                cert = solve(d,v).to_dict()
                                current['exact'] = cert
                                current['certificate_valid'] = verify(d,v,cert)
                            else:
                                current['conic'] = conic.solve(d,v)
                            current[method+'_seconds'] = perf_counter() - tick
                        if rep == 0:
                            budget()
                            tick = perf_counter()
                            ref = maximize_reference(d,v)
                            current['reference_seconds'] = perf_counter()-tick
                            current['reference_risk'] = str(ref.risk)
                            current['reference_x'] = list(map(str,ref.x))
                            current['reference_match'] = ref.risk == F(current['exact']['risk'])
                        current = saved_safe(current)
                        rows.append(current)
                        raw.write(json.dumps(current,sort_keys=True,allow_nan=False)+'\n')
                        raw.flush()
                        if (not current['certificate_valid'] or current.get('reference_match') is False
                                or F(current['grid']['risk']) > F(current['exact']['risk'])):
                            current = None
                            raise ArithmeticError('Correctness gate failure; row retained')
                        current = None
                print(s['id'], len(s['candidates']), 'allocations completed', flush=True)
        except Exception as error:
            status = 'stopped'
            failure = {'type':type(error).__name__,'message':str(error),'partial_row':current}
            dump(out/'failure.json',failure)
    wall = perf_counter()-start
    check_freeze()
    dump(out/'setups.json', setups)
    summary = summarize(inputs, rows, setups, status)
    dump(out/'summary.json',summary)
    dump(out/'receipt.json',{'started_utc':started_utc,'finished_utc':now(),'status':status,
                             'wall_seconds':wall,'platform':platform.platform(),'python':sys.version,
                             'dependencies':versions(),'freeze_sha256':digest(D/'freeze.json'),
                             'fixture_sha256':digest(D/'inputs.json'),
                             'rows_sha256':digest(out/'rows.jsonl'),'setups_sha256':digest(out/'setups.json'),
                             'model_calls':0,'external_api_usd':0,'failure':failure})
    print(json.dumps({k:v for k,v in summary.items() if k!='decisions'},indent=2))
    if status != 'complete':
        raise SystemExit(1)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--freeze',action='store_true')
    args=parser.parse_args()
    freeze() if args.freeze else run()
