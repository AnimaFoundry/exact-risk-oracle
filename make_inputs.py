"""Original deterministic synthetic validation inputs, SPDX-License-Identifier: MIT."""
from fractions import Fraction as F
from pathlib import Path
import json
import random

ROOT = Path(__file__).resolve().parent


def generate():
    rng = random.Random(271027031)
    cases = []
    for j in range(128):
        k = 1 + j % (5 if j < 64 else 6)
        raw = [rng.randint(1, 13) for _ in range(k)]
        w = [F(z, sum(raw)) for z in raw]
        n = [rng.choice([0, 1, 2, 3] if j < 16 else [0, 1, 2, 5, 13]) for _ in w]
        a = [wi * F(rng.randrange(5), 4) if ni else F(0) for wi, ni in zip(w, n)]
        cases.append({'id': f'small-{j:03}', 'group':'small', 'w':list(map(str,w)),
                      'n':n, 'a':list(map(str,a)), 'grid':j<64, 'expectation':j<16,
                      'conic':j<48, 'reference':True})
    for group, sizes in [('shared', [16, 32, 64, 256]),
                         ('exact-scale', [16, 64, 256, 1024, 4096, 16384])]:
        for k in sizes:
            for replicate in range(2):
                w = [F(1,k)] * k
                n = [rng.choice([0, 1, 2, 5, 13]) for _ in w]
                a = [wi*F(rng.randrange(5),4) if ni else F(0) for wi,ni in zip(w,n)]
                cases.append({'id':f'{group}-{k}-{replicate}', 'group':group,
                              'w':list(map(str,w)), 'n':n, 'a':list(map(str,a)),
                              'grid':False, 'expectation':False,
                              'conic':group=='shared', 'reference':False})
    return {'seed':271027031, 'description':'Original fixed synthetic software validation; no private records',
            'cases':cases}


if __name__ == '__main__':
    path = ROOT / 'synthetic_inputs.json'
    if path.exists():
        raise SystemExit('Refusing to overwrite existing validation inputs')
    path.write_text(json.dumps(generate(), sort_keys=True, indent=2)+'\n', encoding='utf-8')
    print('Wrote 148 synthetic inputs without evaluating outcomes')
