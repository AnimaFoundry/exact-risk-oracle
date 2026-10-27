"""One original synthetic cohort, no risk-based selection. SPDX-License-Identifier: MIT."""
from pathlib import Path
import json
import random
from fractions import Fraction as F
from decision.design import enumerate_candidates

SEED = 271027117


def generate():
    rng = random.Random(SEED)
    scenarios = []
    for k in (2, 3, 4):
        for shrinkage in ('0', '1/2', '1', '2'):
            for replica, budget in enumerate((2, 3, 4, 4)):
                raw = [rng.randint(1, 9) for _ in range(k)]
                weights = [str(F(z, sum(raw))) for z in raw]
                horizon = budget + 2
                powered = set(rng.sample(range(horizon), budget))
                fixed = rng.randrange(k)
                slots = []
                for slot in range(horizon):
                    if replica == 0:
                        eligible = list(range(k))
                    elif replica == 1:
                        eligible = sorted(rng.sample(range(k), rng.randint(1, k)))
                    elif replica == 2:
                        eligible = sorted(rng.sample(range(k), k - 1))
                    else:
                        eligible = [fixed]
                    slots.append({'powered': slot in powered, 'eligible': eligible})
                s = {'id': f'decision-{len(scenarios)+1:03d}', 'weights': weights,
                     'shrinkage': shrinkage, 'replica': replica,
                     'budget': budget, 'calendar': slots}
                s['candidates'] = enumerate_candidates(s)
                scenarios.append(s)
    return {'schema_version': 1, 'seed': SEED, 'source': 'original synthetic, no risk screening',
            'scenarios': scenarios}


if __name__ == '__main__':
    p = Path(__file__).with_name('inputs.json')
    if p.exists():
        raise SystemExit('Existing evaluation inputs will not be replaced')
    p.write_text(json.dumps(generate(), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print('Generated original inputs without any risk evaluation')
