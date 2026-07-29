#!/usr/bin/env python3
"""Does the SHAPE change with depth? Registered in R23_shape/DEPTH_PREREGISTRATION.md.

Amendment 1 records why this is the third instrument: Spearman over 28 noisy cells failed a planted
df 30->2 gradient, and so did a binned two-group comparison of pooled standardised values. Per-cell
standardisation at n=12 is itself noisy enough to erase much of what it exists to preserve.

This one works in the pivot's own currency -- the median per-cell descriptor, the quantity the
single-shape fit reads a df off -- and compares shallow against deep with a CELL-LEVEL permutation.
A difference between two groups does not hit the mixture trap that killed the pivot's first three
nulls: permuting makes BOTH groups mixtures and SHRINKS the difference, the conservative direction.

IT MEASURES ITS OWN DETECTION WINDOW and emits it, because the descriptor saturates at extreme tail
weight and a negative result is only as strong as the window it was taken in.
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run as R                                                          # noqa: E402

ALPHA = 0.05
N_PERM = 4000
SEED = 20260729
SHALLOW, DEEP = 1 / 3, 2 / 3


def med_desc(cells, key):
    v = [x for x in (R.descriptor(c, key) for c in cells) if x == x]
    return R.q(v, .5) if v else float('nan')


def group_test(cells, depth, key, rng, nperm=N_PERM):
    lo = [c for c, d in zip(cells, depth) if d < SHALLOW]
    hi = [c for c, d in zip(cells, depth) if d >= DEEP]
    if len(lo) < 6 or len(hi) < 6:
        return None
    obs = med_desc(hi, key) - med_desc(lo, key)
    lab = [0] * len(lo) + [1] * len(hi)
    pool = lo + hi
    null = []
    for _ in range(nperm):
        rng.shuffle(lab)
        a = [c for c, l in zip(pool, lab) if l == 0]
        b = [c for c, l in zip(pool, lab) if l == 1]
        null.append(med_desc(b, key) - med_desc(a, key))
    null.sort()
    p = (1 + sum(1 for x in null if abs(x) >= abs(obs))) / (1 + nperm)
    return {'delta': obs, 'shallow': med_desc(lo, key), 'deep': med_desc(hi, key),
            'p': p, 'n_shallow_cells': len(lo), 'n_deep_cells': len(hi),
            'm_break': (ALPHA / p) if p > 0 else None, 'n_perm': nperm}


def synth(rng, depth, sizes, kind):
    if kind == 'flat':
        return [R.t_draw(rng, 4, n) for n in sizes]
    if kind == 'scale_gradient':
        return [[x * (1 + 4 * d) for x in R.t_draw(rng, 4, n)] for d, n in zip(depth, sizes)]
    a, b = kind                                        # a df gradient from a down to b
    return [R.t_draw(rng, max(b, int(round(a - (a - b) * d))), n)
            for d, n in zip(depth, sizes)]


def main():
    rng = random.Random(SEED)
    cells, meta = R.load_cells()
    depth = [c['depth_frac'] for c in meta]
    sizes = [len(c) for c in cells]
    print(f'  cells {len(cells)}   sizes {sorted(set(sizes))}')

    # ---- the detection WINDOW, measured and emitted
    print('\n  DETECTION WINDOW (planted df gradients, q90_abs_z)')
    win = []
    for a, b in ((30, 2), (20, 2), (10, 3), (8, 3), (6, 3), (6, 4)):
        r = group_test(synth(rng, depth, sizes, (a, b)), depth, 'q90_abs_z', rng, 1500)
        win.append({'from_df': a, 'to_df': b, 'delta': r['delta'], 'p': r['p'],
                    'fires': r['p'] < ALPHA})
        print(f"    df {a:>3} -> {b:<3}   delta {r['delta']:+.4f}   p {r['p']:.4f}   "
              f"{'fires' if r['p'] < ALPHA else 'BLIND'}")

    print('\n  CONTROLS')
    ctrl = {}
    for name, kind, want_fire in (('planted_10_to_3', (10, 3), True),
                                  ('flat', 'flat', False),
                                  ('scale_gradient', 'scale_gradient', False)):
        r = group_test(synth(rng, depth, sizes, kind), depth, 'q90_abs_z', rng, 1500)
        ok = (r['p'] < ALPHA) if want_fire else (r['p'] >= ALPHA)
        ctrl[name] = {**r, 'pass': ok, 'must_fire': want_fire}
        print(f"    {name:<18} delta {r['delta']:+.4f}  p {r['p']:.4f}  -> "
              f"{'PASS' if ok else 'FAIL'} ({'MUST fire' if want_fire else 'must NOT fire'})")

    out = {'seed': SEED, 'n_cells': len(cells), 'detection_window': win, 'controls': ctrl}
    if not all(c['pass'] for c in ctrl.values()):
        out['verdict'] = 'UNVERIFIED_CONTROL_FAILED'
        print('\n  -> UNVERIFIED: a control failed. Not an acquittal.')
        (HERE / 'results').mkdir(exist_ok=True)
        json.dump(out, open(HERE / 'results' / 'r23_depth.json', 'w'), indent=1)
        return 3

    print('\n  SHALLOW vs DEEP, one test per descriptor')
    res, rej = {}, []
    for key in R.DESCRIPTORS:
        r = group_test(cells, depth, key, rng)
        res[key] = r
        if r['p'] < ALPHA:
            rej.append(key)
        print(f"    {key:<16} shallow {r['shallow']:+.4f}  deep {r['deep']:+.4f}  "
              f"delta {r['delta']:+.4f}  p {r['p']:.6f}  m_break "
              f"{(r['m_break'] if r['m_break'] else float('inf')):.2f}")
    strong = [k for k in rej if res[k]['m_break'] and res[k]['m_break'] >= len(R.DESCRIPTORS)]
    verdict = ('DEPTH-READS-SHAPE' if len(strong) >= 3 else
               'NO-DEPTH-TREND-IN-WINDOW' if not rej else 'MIXED')

    sc = group_test([[x] * 1 for x in range(0)] or cells, depth, 'q90_abs_z', rng, 2)  # placeholder
    scales = [c['mad'] if c['mad'] > 0 else c['sd'] for c in meta]
    lo = [s for s, d in zip(scales, depth) if d < SHALLOW]
    hi = [s for s, d in zip(scales, depth) if d >= DEEP]
    out['scale_shallow_vs_deep'] = {'shallow_median_mad': R.q(lo, .5),
                                    'deep_median_mad': R.q(hi, .5),
                                    'ratio': R.q(hi, .5) / R.q(lo, .5) if R.q(lo, .5) else None}
    print(f"\n  THE SCALE, for the comparison the confound control demands: "
          f"shallow MAD {out['scale_shallow_vs_deep']['shallow_median_mad']:.6f}  "
          f"deep {out['scale_shallow_vs_deep']['deep_median_mad']:.6f}  "
          f"ratio {out['scale_shallow_vs_deep']['ratio']:.4f}x")

    # the ratios the page quotes: a shape change expressed against the SCALE change, so a reader
    # sees the two side by side instead of taking "larger than the scale" on trust
    out['deep_over_shallow_ratio'] = {k: (res[k]['deep'] / res[k]['shallow'])
                                      for k in R.DESCRIPTORS if res[k]['shallow'] not in (0,)}
    out.update({'shallow_vs_deep': res, 'descriptors_rejecting': rej,
                'descriptors_surviving_family': strong, 'verdict': verdict})
    print(f'\n  REGISTERED VERDICT: {verdict}')
    (HERE / 'results').mkdir(exist_ok=True)
    op = HERE / 'results' / 'r23_depth.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
