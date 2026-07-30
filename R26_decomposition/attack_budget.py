#!/usr/bin/env python3
"""The variance budget I committed has ZERO discriminating power, and this file proves it.

An independent code review found it. The proof is short enough that there is no excuse for having
missed it:

    share_size = Var(size) / Var(log|I|)

does not reference the PAIRING between size and log|I| at all. Permute which head has which size and
the number does not move. So a term can "carry 14% of the variance" while having no association
whatsoever with the target -- and that is exactly what happened: rho_bar_align came in at +0.0304 and
-0.0071 in the two 3b cells, i.e. nothing, while share_align read 0.1385 and 0.1680.

SECOND, THE BUDGET IS NOT AN IDENTITY. Var(log|I|) = Var(size) + Var(align) + 2Cov(size, align) holds
only if log|I| = size + align + c POINTWISE. It does not, so `residual_share` is not a residual -- it
is one minus a ratio of the variances of two different variables, and it is unbounded in both
directions.

THIRD, THE HONEST REPLACEMENT. A statistic that does depend on the pairing: the within-layer R^2 of
log|I| on the head's own write, against its own permutation null, whose mean is exactly k/(n-1) for k
free predictors. And the target's own measurement error, bounded from R11's disjoint item sets, so the
unexplained part is separated from noise rather than assumed to exceed it.

NO VERDICT IS EMITTED. Numbers, and the base rates they must be read against.
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

SEED = 20260729
N_PERM = 10000
N_R2_PERM = 4000
CELLS = (('qwen2.5-1.5b', 'I_final'), ('qwen2.5-1.5b', 'I_all'),
         ('qwen2.5-3b', 'I_final'), ('qwen2.5-3b', 'I_all'))
SRC = {('qwen2.5-1.5b', 'I_final'): 'R10_exhaustive/results/r10_exhaustive_qwen2.5-1.5b.json',
       ('qwen2.5-1.5b', 'I_all'): 'R18_all_positions/results/r18_allpos_qwen2.5-1.5b.json',
       ('qwen2.5-3b', 'I_final'): 'R10_exhaustive/results/r10_exhaustive_qwen2.5-3b.json',
       ('qwen2.5-3b', 'I_all'): 'R18_all_positions/results/r18_allpos_qwen2.5-3b.json'}


def var(v):
    v = [x for x in v if x == x]
    if len(v) < 2:
        return float('nan')
    m = sum(v) / len(v)
    return sum((x - m) ** 2 for x in v) / (len(v) - 1)


def cov(a, b):
    p = [(x, y) for x, y in zip(a, b) if x == x and y == y]
    if len(p) < 2:
        return float('nan')
    ma = sum(x for x, _ in p) / len(p)
    mb = sum(y for _, y in p) / len(p)
    return sum((x - ma) * (y - mb) for x, y in p) / (len(p) - 1)


def r2(y, preds):
    """Ordinary least squares R^2 with an intercept, via normal equations. Few predictors."""
    n = len(y)
    X = [[1.0] + [p[i] for p in preds] for i in range(n)]
    k = len(X[0])
    A = [[sum(X[i][a] * X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    c = [sum(X[i][a] * y[i] for i in range(n)) for a in range(k)]
    for i in range(k):                                   # Gaussian elimination with partial pivot
        p = max(range(i, k), key=lambda r: abs(A[r][i]))
        if abs(A[p][i]) < 1e-12:
            return float('nan')
        A[i], A[p] = A[p], A[i]
        c[i], c[p] = c[p], c[i]
        for r in range(i + 1, k):
            f = A[r][i] / A[i][i]
            for j in range(i, k):
                A[r][j] -= f * A[i][j]
            c[r] -= f * c[i]
    beta = [0.0] * k
    for i in range(k - 1, -1, -1):
        beta[i] = (c[i] - sum(A[i][j] * beta[j] for j in range(i + 1, k))) / A[i][i]
    my = sum(y) / n
    sst = sum((v - my) ** 2 for v in y)
    if sst <= 0:
        return float('nan')
    ssr = sum((y[i] - sum(beta[a] * X[i][a] for a in range(k))) ** 2 for i in range(n))
    return 1.0 - ssr / sst


def load_target(model, support):
    d = json.load(open(REPO / SRC[(model, support)]))
    L = {int(k): v for k, v in d['layers'].items()}
    out = {}
    for lay in sorted(L):
        ph = L[lay]['per_head']
        out[lay] = [abs(ph[str(h)]) for h in range(len(ph))]
    return out


def main():
    rng = random.Random(SEED)
    dec = json.load(open(HERE / 'results' / 'r26_decompose.json'))
    out = {'seed': SEED, 'n_perm': N_PERM, 'n_r2_perm': N_R2_PERM}

    # ---------- 1. the committed statistics are permutation-invariant ----------
    print('  PERMUTATION INVARIANCE of the committed budget statistics')
    print(f'    {"cell":<26}{"share_size":<13}{"max|delta|":<13}{"P(null>=obs)":<14}')
    inv = {}
    for model, support in CELLS:
        rec = dec['models'][model]
        per = rec['per_head']
        tgt = load_target(model, support)
        NL, NH = per['n_layers'], per['n_heads']
        sz, al, yy = [], [], []
        for lay in range(NL):
            for h in range(NH):
                e = tgt[lay][h]
                if e <= 0:
                    continue
                s, a = per['size'][lay][h], per['align'][lay][h]
                if s != s or a != a:
                    continue
                sz.append(s); al.append(a); yy.append(math.log(e))
        vt = var(yy)
        obs = var(sz) / vt
        mx, ge = 0.0, 0
        idx = list(range(len(sz)))
        for _ in range(N_PERM):
            rng.shuffle(idx)                             # permute the PAIRING only
            v = var([sz[i] for i in idx]) / vt
            mx = max(mx, abs(v - obs))
            ge += (v >= obs - 1e-15)
        inv[f'{model}|{support}'] = {
            'share_size_observed': obs, 'max_abs_delta_under_permutation': mx,
            'p_null_ge_observed': ge / N_PERM, 'n_cells': len(sz)}
        print(f'    {model + "|" + support:<26}{obs:<13.4f}{mx:<13.3e}{ge / N_PERM:<14.4f}')
    out['permutation_invariance'] = inv

    # ---------- 2. the budget is not an identity ----------
    print('\n  IS THE BUDGET AN IDENTITY? Var(log|I| - (size+align)) / Var(log|I|)')
    print('    (would be 0 if log|I| = size + align + c pointwise; above 1 is possible and appears)')
    ident = {}
    for model, support in CELLS:
        per = dec['models'][model]['per_head']
        tgt = load_target(model, support)
        NL, NH = per['n_layers'], per['n_heads']
        d, yy = [], []
        for lay in range(NL):
            for h in range(NH):
                e = tgt[lay][h]
                s, a = per['size'][lay][h], per['align'][lay][h]
                if e <= 0 or s != s or a != a:
                    continue
                yy.append(math.log(e)); d.append(math.log(e) - (s + a))
        r = var(d) / var(yy)
        ident[f'{model}|{support}'] = {'var_of_pointwise_residual_over_var_target': r,
                                       'committed_residual_share':
                                       dec['models'][model]['supports'][support]['budget']
                                       ['residual_share']}
        print(f'    {model + "|" + support:<26}{r:.4f}   '
              f'(committed residual_share was '
              f'{ident[f"{model}|{support}"]["committed_residual_share"]:.4f})')
    out['identity_check'] = ident

    # ---------- 3. the target's own measurement error, from R11's disjoint item sets ----------
    print('\n  TARGET MEASUREMENT ERROR from R11 A/B (disjoint item sets, same heads)')
    a = REPO / 'R11_instrument_noise' / 'results' / 'r11_itemsA_qwen2.5-1.5b.json'
    b = REPO / 'R11_instrument_noise' / 'results' / 'r11_itemsB_qwen2.5-1.5b.json'
    rel = None
    if a.exists() and b.exists():
        da, db = json.load(open(a)), json.load(open(b))
        LA = {int(k): v for k, v in da['layers'].items()}
        LB = {int(k): v for k, v in db['layers'].items()}
        xa, xb = [], []
        for lay in sorted(set(LA) & set(LB)):
            pa, pb = LA[lay]['per_head'], LB[lay]['per_head']
            for h in range(len(pa)):
                va, vb = abs(pa[str(h)]), abs(pb[str(h)])
                if va > 0 and vb > 0:
                    xa.append(math.log(va)); xb.append(math.log(vb))
        err = sum((x - y) ** 2 for x, y in zip(xa, xb)) / (2 * len(xa))
        vt = var(xa)
        rel = {'n_cells': len(xa), 'var_error_nats2': err, 'sd_error_nats': math.sqrt(err),
               'var_target_nats2': vt, 'error_share_of_var': err / vt,
               'reliability': cov(xa, xb) / math.sqrt(var(xa) * var(xb)),
               'base_margin_A': da.get('base_margin'), 'base_margin_B': db.get('base_margin')}
        print(f'    n {rel["n_cells"]}   sd(error) {rel["sd_error_nats"]:.4f} nats   '
              f'Var(error) {rel["var_error_nats2"]:.4f} nats^2')
        print(f'    error share of Var(log|I|) = {rel["error_share_of_var"]:.4f}   '
              f'reliability {rel["reliability"]:.4f}')
        print(f'    base_margin A {rel["base_margin_A"]!r}  B {rel["base_margin_B"]!r} '
              f'(disjoint items, so these SHOULD differ)')
    else:
        print('    R11 A/B not both present -> UNMEASURED, not zero')
    out['target_measurement_error'] = rel

    # ---------- 4. a statistic that DOES depend on the pairing ----------
    print('\n  WITHIN-LAYER R^2 against its own permutation null (mean = k/(n-1) exactly)')
    print(f'    {"cell":<26}{"R2(size)":<11}{"R2(s,a)":<11}{"floor1":<9}{"floor2":<9}'
          f'{"align net":<11}p(null>=)')
    r2s = {}
    for model, support in CELLS:
        per = dec['models'][model]['per_head']
        tgt = load_target(model, support)
        NL, NH = per['n_layers'], per['n_heads']
        v1, v2, nl1, nl2, hits = [], [], [], [], 0
        for lay in range(NL):
            y, s, al = [], [], []
            for h in range(NH):
                e = tgt[lay][h]
                a_, b_ = per['size'][lay][h], per['align'][lay][h]
                if e <= 0 or a_ != a_ or b_ != b_:
                    continue
                y.append(math.log(e)); s.append(a_); al.append(b_)
            if len(y) < 5:
                continue
            o1, o2 = r2(y, [s]), r2(y, [s, al])
            v1.append(o1); v2.append(o2)
            idx = list(range(len(y)))
            n1 = []
            for _ in range(N_R2_PERM // 10):
                rng.shuffle(idx)
                n1.append(r2(y, [[s[i] for i in idx]]))
            nl1.append(sum(n1) / len(n1))
            nl2.append(2.0 / (len(y) - 1))
        def mean(v):
            v = [x for x in v if x == x]
            return sum(v) / len(v) if v else float('nan')
        m1, m2 = mean(v1), mean(v2)
        f1, f2 = mean(nl1), mean(nl2)
        # one joint permutation test on the layer-mean R2(size)
        obs = m1
        for _ in range(N_R2_PERM):
            acc = []
            for lay in range(NL):
                y, s = [], []
                for h in range(NH):
                    e = tgt[lay][h]
                    a_ = per['size'][lay][h]
                    if e <= 0 or a_ != a_:
                        continue
                    y.append(math.log(e)); s.append(a_)
                if len(y) < 5:
                    continue
                idx = list(range(len(y)))
                rng.shuffle(idx)
                acc.append(r2(y, [[s[i] for i in idx]]))
            hits += (sum(acc) / len(acc) >= obs)
        r2s[f'{model}|{support}'] = {
            'mean_within_layer_r2_size': m1, 'mean_within_layer_r2_size_align': m2,
            'permutation_null_mean_1pred': f1, 'analytic_floor_2pred': f2,
            'excess_size_over_floor': m1 - f1, 'align_net_gain_over_its_own_cost': m2 - m1 - (f2 - f1),
            'p_null_ge_observed': (1 + hits) / (1 + N_R2_PERM)}
        z = r2s[f'{model}|{support}']
        print(f'    {model + "|" + support:<26}{m1:<11.4f}{m2:<11.4f}{f1:<9.4f}{f2:<9.4f}'
              f'{z["align_net_gain_over_its_own_cost"]:<+11.4f}{z["p_null_ge_observed"]:.4f}')
    out['within_layer_r2'] = r2s

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r26_attack_budget.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
