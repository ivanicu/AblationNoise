#!/usr/bin/env python3
"""R23 -- the SHAPE of the ablation-effect distribution, and whether there is only one of it.

Registered in R23_shape/PREREGISTRATION.md, committed before this file existed.

Every round before this reported the WIDTH. This reports the shape, and runs the pivot: standardise
each conditional distribution by its own centre and scale, and ask whether they are draws from one
distribution.

  COLLAPSE     -> a scale family. One universal shape, one number per condition.
  NO COLLAPSE  -> the shape carries what the width discards, and shape is a readable channel.

No GPU. Arithmetic on frozen per-head results.
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
N_PERM = 20000
SEED = 20260729
ALPHA = 0.05


# ---------- shape primitives, all robust-first because excess kurtosis is 7.31 ----------
def q(v, p):
    w = sorted(v)
    if len(w) == 1:
        return w[0]
    i = p * (len(w) - 1)
    lo = int(math.floor(i))
    hi = min(lo + 1, len(w) - 1)
    return w[lo] + (i - lo) * (w[hi] - w[lo])


def med(v):
    return q(v, 0.5)


def mad(v):
    m = med(v)
    return med([abs(x - m) for x in v])


def moments(v):
    n = len(v)
    mu = sum(v) / n
    s2 = sum((x - mu) ** 2 for x in v) / (n - 1)
    sd = math.sqrt(s2) if s2 > 0 else 0.0
    if sd == 0:
        return mu, 0.0, float('nan'), float('nan')
    m3 = sum((x - mu) ** 3 for x in v) / n
    m4 = sum((x - mu) ** 4 for x in v) / n
    return mu, sd, m3 / sd ** 3, m4 / sd ** 4 - 3


def hill_tail(v, frac=0.2):
    """Hill estimator of the tail index on |v|. Small n makes this weak; reported as such.
    A LARGER value = a HEAVIER tail (1/alpha convention), so it reads in the same direction
    as kurtosis and does not need a mental flip."""
    a = sorted((abs(x) for x in v), reverse=True)
    k = max(2, int(frac * len(a)))
    if len(a) <= k or a[k] <= 0:
        return float('nan')
    s = sum(math.log(a[i] / a[k]) for i in range(k) if a[i] > 0)
    return s / k                                     # = 1/alpha, bigger = heavier


def shape_vector(v):
    mu, sd, skew, kurt = moments(v)
    m, d = med(v), mad(v)
    q25, q50, q75, q90, q99 = q(v, .25), q(v, .5), q(v, .75), q(v, .90), q(v, .99)
    a = [abs(x) for x in v]
    aq50, aq90, aq99 = q(a, .5), q(a, .90), q(a, .99)
    return {
        'n': len(v), 'mean': mu, 'sd': sd, 'median': m, 'mad': d,
        'iqr': q75 - q25, 'skew': skew, 'excess_kurtosis': kurt,
        # SCALE-FREE, so they compare across conditions without any normalisation choice
        'q90_over_q50_abs': (aq90 / aq50) if aq50 > 0 else float('nan'),
        'q99_over_q50_abs': (aq99 / aq50) if aq50 > 0 else float('nan'),
        'iqr_over_mad': ((q75 - q25) / d) if d > 0 else float('nan'),
        'sd_over_mad': (sd / d) if d > 0 else float('nan'),
        'bowley_skew': (((q75 + q25 - 2 * q50) / (q75 - q25)) if q75 > q25 else float('nan')),
        'hill_tail_index': hill_tail(v)}


def standardise(v):
    m, d = med(v), mad(v)
    if d <= 0:                                        # degenerate cell: fall back to sd
        _, s, _, _ = moments(v)
        d = s if s > 0 else 1.0
    return [(x - m) / d for x in v]

# ---------- the collapse instrument ----------
DESCRIPTORS = ('q90_abs_z', 'q99_abs_z', 'kurt_z', 'sd_over_mad_z', 'bowley_z')


def descriptor(v, key):
    """A SCALE-FREE shape number, computed on values standardised by their own median and MAD."""
    z = standardise(v)
    a = [abs(x) for x in z]
    if key == 'q90_abs_z':
        return q(a, .90)
    if key == 'q99_abs_z':
        return q(a, .99)
    if key == 'kurt_z':
        return moments(z)[3]
    if key == 'sd_over_mad_z':
        _, sd, _, _ = moments(z)
        d = mad(z)
        return sd / d if d > 0 else float('nan')
    if key == 'bowley_z':
        q25, q50, q75 = q(z, .25), q(z, .5), q(z, .75)
        return (q75 + q25 - 2 * q50) / (q75 - q25) if q75 > q25 else float('nan')
    raise KeyError(key)


def var(v):
    m = sum(v) / len(v)
    return sum((x - m) ** 2 for x in v) / (len(v) - 1)


def t_draw(rng, df, n, scale=1.0):
    out = []
    for _ in range(n):
        z = rng.gauss(0, 1)
        w = sum(rng.gauss(0, 1) ** 2 for _ in range(df))
        out.append(scale * z / math.sqrt(w / df))
    return out


DF_GRID = (1, 2, 3, 4, 5, 6, 8, 10, 15, 30, 100)


def collapse(cells, key, rng, nsim=2000):
    """Between-cell variance of the descriptor, against a null that contains EXACTLY ONE SHAPE.

    THE NULL IS NOT THE POOL, and that is the whole design. Under the alternative the pooled data is
    a MIXTURE; a mixture is heavier-tailed than either component, so cells drawn from the pool are
    MORE shape-dispersed than the truth and the test loses power against exactly the alternative it
    is for. Permutation, pooled bootstrap and re-partition all share that defect -- all three were
    built and all three failed control 2 before this one was written. So the null is SIMULATED from
    a single Student-t whose df is fitted by matching the median per-cell descriptor.
    """
    sizes = [len(c) for c in cells]
    d = [descriptor(c, key) for c in cells]
    d = [x for x in d if x == x]
    if len(d) < 3:
        return None
    obs = var(d)
    target = q(d, .5)
    best, best_df = float('inf'), 4
    for df in DF_GRID:
        s = [descriptor(t_draw(rng, df, n), key) for n in sizes]
        s = [x for x in s if x == x]
        if not s:
            continue
        gap = abs(q(s, .5) - target)
        if gap < best:
            best, best_df = gap, df
    null = []
    for _ in range(nsim):
        s = [descriptor(t_draw(rng, best_df, n), key) for n in sizes]
        s = [x for x in s if x == x]
        if len(s) > 2:
            null.append(var(s))
    null.sort()
    p = (1 + sum(1 for x in null if x >= obs)) / (1 + len(null))
    return {'observed_between_cell_var': obs, 'null_median': null[len(null) // 2],
            'null_975': null[int(.975 * len(null))], 'p': p, 'fitted_df': best_df,
            'n_cells_used': len(d), 'n_sim': len(null),
            'm_break': (0.05 / p) if p > 0 else None}


def power_curve(rng, key='q90_abs_z', nsim=1200):
    """The two registered synthetic controls, swept over cell size. Emitted so the page quotes a
    generator: an instrument's power is a measurement, not a claim."""
    rows = []
    for n, ncell in ((12, 128), (24, 64), (48, 32), (96, 16), (168, 12), (336, 8)):
        same = [t_draw(rng, 4, n, 20 ** (i / (ncell - 1))) for i in range(ncell)]
        mixed = [([rng.gauss(0, 1) for _ in range(n)] if i % 2 == 0 else t_draw(rng, 2, n))
                 for i in range(ncell)]
        a = collapse(same, key, rng, nsim)
        b = collapse(mixed, key, rng, nsim)
        rows.append({'n_per_cell': n, 'n_cells': ncell,
                     'ctrl1_same_shape_p': a['p'], 'ctrl1_pass': a['p'] >= ALPHA,
                     'ctrl2_mixed_p': b['p'], 'ctrl2_pass': b['p'] < ALPHA,
                     'ctrl1_fitted_df': a['fitted_df'], 'ctrl2_fitted_df': b['fitted_df']})
    return rows


def load_cells():
    srcs = [('qwen2.5-1.5b', 'I_final', REPO / 'R10_exhaustive' / 'results'
             / 'r10_exhaustive_qwen2.5-1.5b.json'),
            ('qwen2.5-3b', 'I_final', REPO / 'R10_exhaustive' / 'results'
             / 'r10_exhaustive_qwen2.5-3b.json'),
            ('qwen2.5-1.5b', 'I_all', REPO / 'R18_all_positions' / 'results'
             / 'r18_allpos_qwen2.5-1.5b.json'),
            ('qwen2.5-3b', 'I_all', REPO / 'R18_all_positions' / 'results'
             / 'r18_allpos_qwen2.5-3b.json')]
    cells, meta = [], []
    for model, support, f in srcs:
        if not f.exists():
            continue
        d = json.load(open(f))
        L = {int(k): v for k, v in d['layers'].items()}
        for lay in sorted(L):
            ph = L[lay]['per_head']
            v = [ph[str(h)] for h in range(len(ph))]
            if len(v) < 4:
                continue
            if mad(v) <= 0 and moments(v)[1] <= 0:
                continue
            cells.append(v)
            meta.append({'model': model, 'support': support, 'layer': lay,
                         'depth_frac': lay / (len(L) - 1), **shape_vector(v)})
    return cells, meta


def main():
    rng = random.Random(SEED)
    out = {'seed': SEED, 'alpha': ALPHA}

    cells, meta = load_cells()
    sizes = [len(c) for c in cells]
    print(f'  cells {len(cells)}   values {sum(sizes)}   '
          f'sizes {sorted(set(sizes))}')

    print('\n  SYNTHETIC CONTROLS at the real sweep\'s cell sizes (registered before the data)')
    same = [t_draw(rng, 4, n, 20 ** (i / (len(sizes) - 1))) for i, n in enumerate(sizes)]
    mixed = [([rng.gauss(0, 1) for _ in range(n)] if i % 2 == 0 else t_draw(rng, 2, n))
             for i, n in enumerate(sizes)]
    c1 = collapse(same, 'q90_abs_z', rng)
    c2 = collapse(mixed, 'q90_abs_z', rng)
    ok1, ok2 = c1['p'] >= ALPHA, c2['p'] < ALPHA
    print(f"    one t(4), 20x scale spread   p {c1['p']:.4f}  -> "
          f"{'PASS' if ok1 else 'FAIL'} (must NOT reject)")
    print(f"    half gaussian / half t(2)    p {c2['p']:.4f}  -> "
          f"{'PASS' if ok2 else 'FAIL'} (MUST reject)")
    out['gate_controls'] = {'same_shape': c1, 'mixed': c2,
                            'ctrl1_pass': ok1, 'ctrl2_pass': ok2}
    out['n_cells'] = len(cells)
    out['n_values'] = sum(sizes)
    out['cells'] = meta

    if not (ok1 and ok2):
        out['verdict'] = 'UNVERIFIED_GATE_CONTROL_FAILED'
        print('\n  -> UNVERIFIED: the instrument cannot separate one shape from two at these '
              'sizes. Nothing below is readable, and that is not an acquittal.')
        (HERE / 'results').mkdir(exist_ok=True)
        json.dump(out, open(HERE / 'results' / 'r23_shape.json', 'w'), indent=1)
        return 3

    print('\n  POWER CURVE over cell size (emitted, not asserted)')
    pc = power_curve(rng)
    out['power_curve'] = pc
    for r in pc:
        print(f"    n {r['n_per_cell']:>4} x {r['n_cells']:>4} cells   "
              f"ctrl1 p {r['ctrl1_same_shape_p']:.4f} {'PASS' if r['ctrl1_pass'] else 'FAIL'}   "
              f"ctrl2 p {r['ctrl2_mixed_p']:.4f} {'PASS' if r['ctrl2_pass'] else 'FAIL'}")

    print('\n  THE PIVOT, one test per descriptor')
    piv, rejects = {}, []
    for key in DESCRIPTORS:
        r = collapse(cells, key, rng)
        piv[key] = r
        if r['p'] < ALPHA:
            rejects.append(key)
        print(f"    {key:<16} observed var {r['observed_between_cell_var']:.6g}   "
              f"null median {r['null_median']:.6g}   p {r['p']:.6f}   "
              f"fitted df {r['fitted_df']:>3}   m_break "
              f"{(r['m_break'] if r['m_break'] else float('inf')):.2f}")
    out['pivot'] = piv
    out['descriptors_rejecting'] = rejects
    verdict = 'NO-COLLAPSE' if rejects else 'COLLAPSE'
    out['verdict'] = verdict

    print('\n  SHAPE VECTOR over the cells (min / median / max)  -- Q1, reported regardless')
    for k in ('excess_kurtosis', 'skew', 'bowley_skew', 'q90_over_q50_abs',
              'q99_over_q50_abs', 'sd_over_mad', 'iqr_over_mad', 'hill_tail_index'):
        v = [c[k] for c in meta if c[k] == c[k]]
        lo, m, hi = min(v), q(v, .5), max(v)
        out.setdefault('shape_spread', {})[k] = {'min': lo, 'median': m, 'max': hi}
        print(f'    {k:<22} {lo:>10.4f} {m:>10.4f} {hi:>10.4f}')

    print('\n  WHICH AXIS CARRIES THE SHAPE (medians)  -- Q3')
    axes = {}
    for sk in ('excess_kurtosis', 'q99_over_q50_abs', 'sd_over_mad', 'hill_tail_index'):
        def sub(f):
            v = [c[sk] for c in meta if f(c) and c[sk] == c[sk]]
            return q(v, .5) if v else float('nan')
        axes[sk] = {'model_1.5b': sub(lambda c: c['model'] == 'qwen2.5-1.5b'),
                    'model_3b': sub(lambda c: c['model'] == 'qwen2.5-3b'),
                    'I_final': sub(lambda c: c['support'] == 'I_final'),
                    'I_all': sub(lambda c: c['support'] == 'I_all'),
                    'shallow': sub(lambda c: c['depth_frac'] < 0.5),
                    'deep': sub(lambda c: c['depth_frac'] >= 0.5)}
        a = axes[sk]
        print(f"    {sk:<22} model {a['model_1.5b']:>8.4f}/{a['model_3b']:<8.4f} "
              f"support {a['I_final']:>8.4f}/{a['I_all']:<8.4f} "
              f"depth {a['shallow']:>8.4f}/{a['deep']:<8.4f}")
    out['axis_medians'] = axes

    print(f'\n  REGISTERED VERDICT: {verdict}'
          + (f'   (rejecting: {", ".join(rejects)})' if rejects else ''))
    (HERE / 'results').mkdir(exist_ok=True)
    op = HERE / 'results' / 'r23_shape.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
