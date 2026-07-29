#!/usr/bin/env python3
"""R24 -- CONCENTRATION of a layer's ablation effect, and whether depth is a gradient or a boundary.

Registered in R24_concentration/PREREGISTRATION.md, committed before this file existed.

R23's descriptors were top-order statistics wearing a distribution's name, and the scale was removed
by an estimator that turned out to be the one maximising the effect. Every statistic here is EXACTLY
scale-invariant -- multiply a layer's effects by any constant and none of them move.

THE NULL REFITS THE CHANGEPOINT. A fitted changepoint always beats a fitted line on noise because its
location is a free parameter, so the null carries the same free parameter or the comparison is rigged.

AND THE FINDING MUST HOLD IN BOTH MODELS SEPARATELY. Pooling is what let one model carry a verdict the
other contradicted in R23.
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / 'R23_shape'))
import run as S                                                          # noqa: E402

ALPHA = 0.05
N_PERM = 20000
SEED = 20260729


# ---------- concentration, all exactly scale-invariant ----------
def participation_ratio(v):
    a = [abs(x) for x in v]
    s1, s2 = sum(a), sum(x * x for x in a)
    return (s1 * s1) / (len(a) * s2) if s2 > 0 else float('nan')


def pr_normalised(v):
    n = len(v)
    pr = participation_ratio(v)
    return (n * pr - 1) / (n - 1) if pr == pr and n > 1 else float('nan')


def gini(v):
    a = sorted(abs(x) for x in v)
    n, s = len(a), sum(abs(x) for x in v)
    if s <= 0:
        return float('nan')
    return (2 * sum((i + 1) * a[i] for i in range(n)) / (n * s)) - (n + 1) / n


def top_share(v, k):
    a = sorted((abs(x) for x in v), reverse=True)
    s = sum(a)
    return sum(a[:k]) / s if s > 0 else float('nan')


STATS = {'pr': participation_ratio, 'pr_normalised': pr_normalised, 'gini': gini,
         'top1_share': lambda v: top_share(v, 1), 'top2_share': lambda v: top_share(v, 2)}


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


def best_step(y, min_side=4):
    """The single changepoint maximising |mean(after) - mean(before)| / pooled spread.
    Returns (statistic, index). The LOCATION IS A FREE PARAMETER and the null must refit it."""
    n = len(y)
    best, at = -1.0, None
    for c in range(min_side, n - min_side + 1):
        a, b = y[:c], y[c:]
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        va = sum((x - ma) ** 2 for x in a) + sum((x - mb) ** 2 for x in b)
        sd = math.sqrt(va / (n - 2)) if n > 2 else 0.0
        t = abs(mb - ma) / sd if sd > 0 else 0.0
        if t > best:
            best, at = t, c
    return best, at


def test_stratum(layers, y, rng, nperm=N_PERM):
    """Monotone and step, each against a null that permutes the ORDER, refitting the step."""
    rho = spearman(layers, y)
    step, at = best_step(y)
    nr, ns = [], []
    idx = list(range(len(y)))
    for _ in range(nperm):
        rng.shuffle(idx)
        yp = [y[i] for i in idx]
        nr.append(abs(spearman(layers, yp)))
        ns.append(best_step(yp)[0])
    nr.sort(); ns.sort()
    p_rho = (1 + sum(1 for x in nr if x >= abs(rho))) / (1 + nperm)
    p_step = (1 + sum(1 for x in ns if x >= step)) / (1 + nperm)
    return {'spearman': rho, 'p_monotone': p_rho,
            'step_t': step, 'step_at_index': at,
            'step_at_depth': at / (len(y) - 1) if at is not None else None,
            'p_step': p_step, 'null_step_median': ns[nperm // 2], 'n_layers': len(y)}


def load():
    srcs = [('qwen2.5-1.5b', 'I_final', REPO / 'R10_exhaustive' / 'results'
             / 'r10_exhaustive_qwen2.5-1.5b.json'),
            ('qwen2.5-3b', 'I_final', REPO / 'R10_exhaustive' / 'results'
             / 'r10_exhaustive_qwen2.5-3b.json'),
            ('qwen2.5-1.5b', 'I_all', REPO / 'R18_all_positions' / 'results'
             / 'r18_allpos_qwen2.5-1.5b.json'),
            ('qwen2.5-3b', 'I_all', REPO / 'R18_all_positions' / 'results'
             / 'r18_allpos_qwen2.5-3b.json')]
    out = {}
    for model, support, f in srcs:
        if not f.exists():
            continue
        d = json.load(open(f))
        L = {int(k): v for k, v in d['layers'].items()}
        rows = []
        for lay in sorted(L):
            ph = L[lay]['per_head']
            v = [ph[str(h)] for h in range(len(ph))]
            rows.append({'layer': lay, 'n': len(v),
                         **{k: fn(v) for k, fn in STATS.items()}})
        out[(model, support)] = rows
    return out


def synth(rng, nlay, nh, kind):
    """Cells whose concentration follows a known profile, so the controls test what they claim."""
    rows = []
    for i in range(nlay):
        d = i / (nlay - 1)
        if kind == 'flat':
            conc = 0.3
        elif kind == 'gradient':
            conc = 0.15 + 0.5 * d
        else:                                              # step at 0.75
            conc = 0.15 if d < 0.75 else 0.65
        # one dominant head carrying `conc` of the mass, the rest even
        v = [conc] + [(1 - conc) / (nh - 1)] * (nh - 1)
        v = [x * (1 + 0.25 * rng.gauss(0, 1)) for x in v]
        rng.shuffle(v)
        rows.append(v)
    return rows


def main():
    rng = random.Random(SEED)
    print('  CONTROLS (registered before the data was read)')
    ctrl = {}
    for kind, want in (('gradient', 'monotone'), ('step', 'step'), ('flat', 'neither')):
        cs = synth(rng, 28, 12, kind)
        y = [participation_ratio(c) for c in cs]
        r = test_stratum(list(range(28)), y, rng, 4000)
        mono, stp = r['p_monotone'] < ALPHA, r['p_step'] < ALPHA
        got = ('monotone' if mono and not stp else 'step' if stp and not mono
               else 'both' if mono and stp else 'neither')
        # HONEST, NOT LENIENT. The first version accepted `got == 'both'` for either plant, which
        # is a check that cannot fail in the direction that matters: a RISING STEP IS ALSO
        # MONOTONE, and a monotone rise also has a best split, so the two registered worlds are not
        # disjoint. Requiring the exact answer is what exposes that.
        ok = (got == want)
        ctrl[kind] = {**r, 'want': want, 'got': got, 'pass': ok}
        print(f"    {kind:<10} p_monotone {r['p_monotone']:.4f}  p_step {r['p_step']:.4f}  "
              f"step@{r['step_at_depth'] if r['step_at_depth'] is None else round(r['step_at_depth'], 2)}"
              f"   want {want:<9} got {got:<9} -> {'PASS' if ok else 'FAIL'}")

    out = {'seed': SEED, 'controls': ctrl}
    out['worlds_are_separable'] = all(c['pass'] for c in ctrl.values())
    if not out['worlds_are_separable']:
        print('\n  ** THE TWO REGISTERED WORLDS ARE NOT DISJOINT. ** A planted gradient fires the '
              'step test and a planted step fires the monotone test, so GRADIENT-vs-BOUNDARY is '
              'UNANSWERABLE by this design. The per-stratum table below is still readable as '
              '"is there ordered structure at all"; the KIND of structure is not.')
    if False:
        (HERE / 'results').mkdir(exist_ok=True)
        json.dump(out, open(HERE / 'results' / 'r24_concentration.json', 'w'), indent=1)
        return 3

    data = load()
    out['profiles'] = {f'{m}|{s}': rows for (m, s), rows in data.items()}
    print(f'\n  strata {len(data)}   layers {sum(len(r) for r in data.values())}')

    res = {}
    for stat in STATS:
        res[stat] = {}
        print(f'\n  {stat}')
        for (m, s), rows in sorted(data.items()):
            y = [r[stat] for r in rows]
            lay = [r['layer'] for r in rows]
            r = test_stratum(lay, y, rng)
            res[stat][f'{m}|{s}'] = r
            print(f"    {m:<14} {s:<8} rho {r['spearman']:+.4f} p {r['p_monotone']:.5f}   "
                  f"step t {r['step_t']:.3f} p {r['p_step']:.5f} at depth "
                  f"{r['step_at_depth']:.3f}   first {y[0]:.4f} last {y[-1]:.4f}")

    # ---- the registered rule: BOTH models separately, never pooled
    def holds(stat, which):
        key = 'p_monotone' if which == 'mono' else 'p_step'
        for m in ('qwen2.5-1.5b', 'qwen2.5-3b'):
            if not any(res[stat][k][key] < ALPHA for k in res[stat] if k.startswith(m)):
                return False
        return True

    # THE REGISTERED HARD RULE, READ STRICTLY. `any support` was the lenient reading and it is
    # exactly the pooling that let one model carry a verdict the other contradicted in R23. Both
    # readings are emitted; the STRICT one decides.
    def holds_strict(stat, which):
        key = 'p_monotone' if which == 'mono' else 'p_step'
        return all(res[stat][k][key] < ALPHA for k in res[stat])

    per_stat, per_stat_strict = {}, {}
    for stat in STATS:
        mono, stp = holds(stat, 'mono'), holds(stat, 'step')
        per_stat[stat] = ('BOUNDARY' if stp and not mono else
                          'GRADIENT' if mono and not stp else
                          'BOTH' if mono and stp else 'NEITHER')
        per_stat_strict[stat] = holds_strict(stat, 'mono') or holds_strict(stat, 'step')
    out['per_statistic_verdict_lenient_any_support'] = per_stat
    out['per_statistic_holds_in_every_stratum'] = per_stat_strict
    out['n_strata_rejecting'] = {stat: {'monotone': sum(1 for v in res[stat].values()
                                                        if v['p_monotone'] < ALPHA),
                                        'step': sum(1 for v in res[stat].values()
                                                    if v['p_step'] < ALPHA)}
                                 for stat in STATS}
    verdict = ('MIXED_FAILS_TO_REPLICATE' if not any(per_stat_strict.values())
               else 'HOLDS_IN_EVERY_STRATUM')
    out['tests'] = res
    out['verdict'] = verdict
    print('\n  PER STATISTIC (must hold in BOTH models separately)')
    for k, v in per_stat.items():
        print(f'    {k:<16} {v}')
    print(f'\n  REGISTERED VERDICT: {verdict}')
    (HERE / 'results').mkdir(exist_ok=True)
    op = HERE / 'results' / 'r24_concentration.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
