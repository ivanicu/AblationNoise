#!/usr/bin/env python3
"""The two supports are not two replications, and the last layer proves the instrument works.

R26's registration treats (model x support) as 4 non-independent cells and excludes the last layer
from any "both supports" count. Both premises came from an outside reader. Neither had a generator, so
neither was reproducible, so this file computes them from the scans directly.

TWO CLAIMS, both checkable and both load-bearing:

  1. At the last layer, I_all EQUALS I_final exactly. Mechanically necessary -- at layer L-1 only the
     final query position has a path to the final logits, so ablating a head at all positions and
     ablating it at the final position are the same intervention. It is therefore the strongest
     POSITIVE CONTROL in this repository: two independently written runners, on separate days, must
     agree to the bit. Unused for twenty-five rounds.

  2. Their divergence is monotone in depth. If so, the difference between the supports IS the axis
     under study, and any rule that counts them as two replications of one measurement is counting
     the signal as a replicate.
"""
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent


def spearman(a, b):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2.0 + 1
            i = j + 1
        return r
    x, y = rk(a), rk(b)
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    dx = math.sqrt(sum((x[i] - mx) ** 2 for i in range(n)))
    dy = math.sqrt(sum((y[i] - my) ** 2 for i in range(n)))
    return num / (dx * dy) if dx > 0 and dy > 0 else float('nan')


def per_head(path):
    d = json.load(open(path))
    L = {int(k): v for k, v in d['layers'].items()}
    return {lay: [L[lay]['per_head'][str(h)] for h in range(len(L[lay]['per_head']))]
            for lay in sorted(L)}


def main():
    out = {'note': 'numbers only; the exact-identity claim is a positive control, not a verdict'}
    print('  SUPPORT DIVERGENCE, and the exact identity at the last layer')
    res = {}
    for model in ('qwen2.5-1.5b', 'qwen2.5-3b'):
        f1 = REPO / 'R10_exhaustive' / 'results' / f'r10_exhaustive_{model}.json'
        f2 = REPO / 'R18_all_positions' / 'results' / f'r18_allpos_{model}.json'
        if not (f1.exists() and f2.exists()):
            continue
        fin, alp = per_head(f1), per_head(f2)
        lays = sorted(set(fin) & set(alp))
        div, dep, absdiff = [], [], []
        for lay in lays:
            a, b = alp[lay], fin[lay]
            num = sum(abs(x - y) for x, y in zip(a, b))
            den = sum(abs(x) for x in a)
            div.append(num / den if den > 0 else float('nan'))
            absdiff.append(max(abs(x - y) for x, y in zip(a, b)))
            dep.append(lay)
        last = lays[-1]
        res[model] = {
            'n_layers': len(lays), 'last_layer': last,
            'max_abs_diff_at_last_layer': absdiff[-1],
            'exact_at_last_layer': absdiff[-1] == 0.0,
            'rho_divergence_vs_depth': spearman(dep, div),
            'divergence_first_layer': div[0], 'divergence_last_layer': div[-1],
            'n_layers_exactly_equal': sum(1 for x in absdiff if x == 0.0),
            'max_abs_diff_over_all_layers': max(absdiff),
            'per_layer_divergence': {str(l): v for l, v in zip(dep, div)},
        }
        r = res[model]
        print(f'    {model:<14} layers {r["n_layers"]:<4} last L{last}')
        print(f'      max|I_all - I_final| at the last layer  {r["max_abs_diff_at_last_layer"]:.3e}'
              f'   exact: {r["exact_at_last_layer"]}')
        print(f'      layers where the two supports are EXACTLY equal: '
              f'{r["n_layers_exactly_equal"]} of {r["n_layers"]}')
        print(f'      relative divergence  first {r["divergence_first_layer"]:.4f}  '
              f'last {r["divergence_last_layer"]:.4f}')
        print(f'      rho(divergence, depth) = {r["rho_divergence_vs_depth"]:+.4f}')
    out['models'] = res
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r26_support_divergence.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
