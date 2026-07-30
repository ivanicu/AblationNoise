#!/usr/bin/env python3
"""log|I| = G - Lambda, both in nats, from numbers already on disk. No model is run.

The published per-head scalar is log|mean_i Delta_i|. It is the log of a SIGNED item mean, so it mixes two
things that a summary can separate exactly:

    G_c      = log rms_i(Delta)                        the gross per-item magnitude
    Lambda_c = G_c - log|mean_i Delta|   >= 0          how much the per-item effects cancel

rms is recoverable from what R11 stored: sd_i(Delta) = sem * sqrt(n), and rms^2 = mean^2 + sd_i^2. So this
is a pointwise reparameterisation of the published number, not a new measurement -- and R11 kept TWO
disjoint item sets over the same 336 cells, which makes every coordinate's reproducibility measurable.

An independent reviewer computed these first. Reproduced here because a number taken on trust from another
agent is what this repository refuses everywhere else.

NO VERDICT IS EMITTED.
"""
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
N_ITEMS = 120
SNR_SPLIT = 2.0


def corr(a, b):
    p = [(x, y) for x, y in zip(a, b) if x == x and y == y]
    n = len(p)
    ma = sum(x for x, _ in p) / n
    mb = sum(y for _, y in p) / n
    num = sum((x - ma) * (y - mb) for x, y in p)
    da = math.sqrt(sum((x - ma) ** 2 for x, _ in p))
    db = math.sqrt(sum((y - mb) ** 2 for _, y in p))
    return num / (da * db) if da > 0 and db > 0 else float('nan')


def var(v):
    v = [x for x in v if x == x]
    m = sum(v) / len(v)
    return sum((x - m) ** 2 for x in v) / (len(v) - 1)


def r2(y, preds):
    n = len(y)
    X = [[1.0] + [p[i] for p in preds] for i in range(n)]
    k = len(X[0])
    A = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    c = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
    for i in range(k):
        pv = max(range(i, k), key=lambda r: abs(A[r][i]))
        if abs(A[pv][i]) < 1e-12:
            return float('nan')
        A[i], A[pv] = A[pv], A[i]
        c[i], c[pv] = c[pv], c[i]
        for r in range(i + 1, k):
            f = A[r][i] / A[i][i]
            for j in range(i, k):
                A[r][j] -= f * A[i][j]
            c[r] -= f * c[i]
        beta = None
    beta = [0.0] * k
    for i in range(k - 1, -1, -1):
        beta[i] = (c[i] - sum(A[i][j] * beta[j] for j in range(i + 1, k))) / A[i][i]
    my = sum(y) / n
    sst = sum((v - my) ** 2 for v in y)
    if sst <= 0:
        return float('nan')
    ssr = sum((y[i] - sum(beta[a] * X[i][a] for a in range(k))) ** 2 for i in range(n))
    return 1.0 - ssr / sst


def cells(path):
    """(layer, head) -> (mean, sem) for every cell a file records both for."""
    d = json.load(open(path))
    out = {}
    for k, v in d['layers'].items():
        if 'per_head_sem' not in v:
            continue
        ph, ps = v['per_head'], v['per_head_sem']
        for h in range(len(ph)):
            out[(int(k), h)] = (ph[str(h)], ps[str(h)])
    return out, d.get('base_margin')


def coords(mean, sem, n=N_ITEMS):
    sd_i = sem * math.sqrt(n)
    rms = math.sqrt(mean * mean + sd_i * sd_i)
    if rms <= 0 or mean == 0:
        return None
    G = math.log(rms)
    return {'logI': math.log(abs(mean)), 'G': G, 'Lam': G - math.log(abs(mean)),
            'log_sd_i': math.log(sd_i) if sd_i > 0 else float('nan'),
            'snr': abs(mean) / sem if sem > 0 else float('inf')}


def main():
    out = {'n_items': N_ITEMS, 'snr_split': SNR_SPLIT,
           'note': 'pointwise reparameterisation of the published scalar; no model run'}
    A, bmA = cells(REPO / 'R11_instrument_noise' / 'results' / 'r11_itemsA_qwen2.5-1.5b.json')
    B, bmB = cells(REPO / 'R11_instrument_noise' / 'results' / 'r11_itemsB_qwen2.5-1.5b.json')
    keys = sorted(set(A) & set(B))
    print(f'  cells with mean AND sem in both item sets: {len(keys)}')
    print(f'  base_margin  A {bmA!r}   B {bmB!r}   (disjoint items, so these differ)')

    ca = {k: coords(*A[k]) for k in keys}
    cb = {k: coords(*B[k]) for k in keys}
    keys = [k for k in keys if ca[k] and cb[k]]

    print('\n  REPLICATION ACROSS DISJOINT ITEM SETS, same 336 heads')
    print(f'    {"coordinate":<12}{"corr(A,B)":<13}{"sd(A-B) nats":<15}{"Var(A) nats2":<14}')
    rep = {}
    for name in ('logI', 'G', 'Lam'):
        xa = [ca[k][name] for k in keys]
        xb = [cb[k][name] for k in keys]
        dif = [x - y for x, y in zip(xa, xb)]
        sd = math.sqrt(sum(d * d for d in dif) / (len(dif) - 1))
        rep[name] = {'corr': corr(xa, xb), 'sd_diff_nats': sd, 'var_A_nats2': var(xa),
                     'mean_A': sum(xa) / len(xa)}
        print(f'    {name:<12}{rep[name]["corr"]:<13.4f}{sd:<15.4f}{rep[name]["var_A_nats2"]:<14.4f}')
    out['replication'] = rep
    out['reproducibility_ratio_logI_over_G'] = rep['logI']['sd_diff_nats'] / rep['G']['sd_diff_nats']
    print(f'    -> log|I| is {out["reproducibility_ratio_logI_over_G"]:.2f}x less reproducible than G,'
          f' and Lambda carries that excess')

    print('\n  THE VARIANCE OF EACH COORDINATE, and Lambda\'s share')
    vl, vg, vlam = var([ca[k]['logI'] for k in keys]), var([ca[k]['G'] for k in keys]), \
        var([ca[k]['Lam'] for k in keys])
    out['variances'] = {'var_logI': vl, 'var_G': vg, 'var_Lambda': vlam,
                        'lambda_share_of_var_logI': vlam / vl,
                        'mean_Lambda_nats': sum(ca[k]['Lam'] for k in keys) / len(keys)}
    print(f'    Var(log|I|) {vl:.4f}   Var(G) {vg:.4f}   Var(Lambda) {vlam:.4f}   '
          f'Lambda share {vlam / vl:.4f}   mean Lambda {out["variances"]["mean_Lambda_nats"]:.4f} nats')

    print('\n  WITHIN-LAYER R2 OF log|I| ON PREDICTORS ALREADY ON DISK')
    lays = sorted({k[0] for k in keys})

    def within(pred_from, target_from, pnames):
        acc = []
        for lay in lays:
            ks = [k for k in keys if k[0] == lay]
            if len(ks) < 5:
                continue
            y = [target_from[k]['logI'] for k in ks]
            ps = [[pred_from[k][nm] for k in ks] for nm in pnames]
            v = r2(y, ps)
            if v == v:
                acc.append(v)
        return sum(acc) / len(acc) if acc else float('nan')

    tests = {
        'log_sd_i_same_set': within(ca, ca, ['log_sd_i']),
        'log_sd_i_cross_set': within(cb, ca, ['log_sd_i']),
        'G_and_Lam_cross_set': within(cb, ca, ['G', 'Lam']),
        'target_replicate_ceiling': None}
    acc = []
    for lay in lays:
        ks = [k for k in keys if k[0] == lay]
        if len(ks) < 5:
            continue
        v = r2([ca[k]['logI'] for k in ks], [[cb[k]['logI'] for k in ks]])
        if v == v:
            acc.append(v)
    tests['target_replicate_ceiling'] = sum(acc) / len(acc)
    n_per = 12
    tests['null_1_predictor'] = 1.0 / (n_per - 1)
    tests['null_2_predictor'] = 2.0 / (n_per - 1)
    out['within_layer_r2'] = tests
    for k, v in tests.items():
        print(f'    {k:<28}{v:.4f}')

    print('\n  THE ERROR IS A MIXTURE, split at |I|/sem = 2')
    lo = [k for k in keys if ca[k]['snr'] < SNR_SPLIT]
    hi = [k for k in keys if ca[k]['snr'] >= SNR_SPLIT]
    mix = {}
    for nm, grp in (('low_snr', lo), ('high_snr', hi)):
        if len(grp) < 3:
            continue
        d = [ca[k]['logI'] - cb[k]['logI'] for k in grp]
        ve = sum(x * x for x in d) / (2 * len(d))
        mix[nm] = {'n': len(grp), 'var_err_nats2': ve, 'sd_err_nats': math.sqrt(ve),
                   'corr': corr([ca[k]['logI'] for k in grp], [cb[k]['logI'] for k in grp])}
        print(f'    {nm:<10} n {mix[nm]["n"]:<5} sd(err) {mix[nm]["sd_err_nats"]:.4f} nats   '
              f'reliability {mix[nm]["corr"]:.4f}')
    flip = sum(1 for k in keys if (A[k][0] > 0) != (B[k][0] > 0))
    mix['n_sign_flips_between_item_sets'] = flip
    mix['frac_sign_flips'] = flip / len(keys)
    print(f'    cells whose EFFECT SIGN flips between the two item sets: {flip} of {len(keys)} '
          f'= {flip / len(keys):.4f}')
    out['error_mixture'] = mix

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r29_on_disk.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
