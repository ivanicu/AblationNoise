#!/usr/bin/env python3
"""Do KV-group mates have correlated PER-ITEM patterns? The mechanism R25's eta^2 needs, now testable.

R25 measured that the grouped-query partition explains 4-9 points of within-layer spread in |effect|.
A reviewer named the mechanism as a testable consequence: heads sharing a key/value stream read the same
keys, so their per-item effect patterns should be correlated -- and grouped cancellation would then be
why the partition shows up in MAGNITUDE but not in orientation. Nothing could test it, because the
per-item vectors were not on disk. They are now.

    r_within   mean Pearson correlation between the 120-vectors of two heads in the SAME KV group
    r_between  the same for two heads in DIFFERENT KV groups
    delta_r    r_within - r_between, per layer, dimensionless

THE NULL IS A HEAD-LABEL PERMUTATION WITHIN THE LAYER, which is exactly what the vectors make possible:
the correlation matrix is held fixed and only the group assignment is shuffled, so the layer's own
pattern geometry is preserved perfectly and only the partition is randomised. Nothing is pooled across
layers, so this cannot inherit the mixture trap.

THE STATISTIC IS NOT A FUNCTION OF WHAT IS ALREADY PUBLISHED, and the file checks that rather than
asserting it: delta_r is regressed on per_head, per_head_sem, layer and head, and the residual is
reported. A coordinate with no residual is an identity, which is how Lambda died.

⚠ AND IT NOW HAS A POSITIVE CONTROL, WHICH IT DID NOT WHEN ITS NULL WAS FIRST READ. A null from an
instrument that has never returned non-zero is silence, not an acquittal -- and the first version of this
file reported p = 0.45 / 0.51 / 0.40 as "the mechanism is dead" without ever planting one. The control
plants a shared within-KV-group item direction at a known fraction alpha of each head's own vector scale
and reports where the instrument starts to see it. That fraction is the SCOPE of any null this file emits.

NO VERDICT IS EMITTED.
"""
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
N_PERM = 20000
GQA = {'qwen2.5-1.5b': {'n_heads': 12, 'n_kv': 2}, 'qwen2.5-3b': {'n_heads': 16, 'n_kv': 2}}


def pair_means(C, g):
    """Mean off-diagonal correlation within groups and between groups."""
    n = len(g)
    iu = np.triu_indices(n, 1)
    same = (g[:, None] == g[None, :])[iu]
    v = C[iu]
    return float(v[same].mean()), float(v[~same].mean())


ALPHAS = (0.0, 0.05, 0.10, 0.20, 0.40)
N_PERM_CTRL = 4000


def delta_r_and_p(layers, g, nh, rng, nperm):
    """Summed delta_r over layers against a within-layer head-label permutation null."""
    obs, nulls = 0.0, np.zeros(nperm)
    for X in layers:
        Xc = X - X.mean(1, keepdims=True)
        s = np.sqrt((Xc * Xc).sum(1, keepdims=True))
        s[s == 0] = 1.0
        C = (Xc / s) @ (Xc / s).T
        w, b = pair_means(C, g)
        obs += w - b
        for t in range(nperm):
            ww, bb = pair_means(C, g[rng.permutation(nh)])
            nulls[t] += ww - bb
    return obs, (1 + int((nulls >= obs).sum())) / (1 + nperm)


def positive_control(d, lay, hd, g, nh, n, rng):
    """Plant a shared within-group direction at a known fraction of each head's own scale."""
    out = {}
    order = sorted(set(lay.tolist()))
    for a in ALPHAS:
        planted = []
        for L in order:
            X = d[lay == L][np.argsort(hd[lay == L])].copy()
            u = rng.standard_normal((int(g.max()) + 1, n))
            u /= np.linalg.norm(u, axis=1, keepdims=True)
            planted.append(X + a * np.linalg.norm(X, axis=1, keepdims=True) * u[g])
        o, p = delta_r_and_p(planted, g, nh, rng, N_PERM_CTRL)
        out[str(a)] = {'alpha': a, 'delta_r': o / len(order), 'p': p, 'fires_at_0.05': p < 0.05}
    fired = [v['alpha'] for v in out.values() if v['fires_at_0.05']]
    blind = [v['alpha'] for v in out.values() if not v['fires_at_0.05'] and v['alpha'] > 0]
    return {'per_alpha': out,
            'largest_alpha_MISSED': max(blind) if blind else None,
            'smallest_alpha_DETECTED': min(fired) if fired else None,
            'note': 'any null this instrument emits is scoped to shared directions at or above '
                    'the smallest DETECTED alpha; below the largest MISSED alpha it is blind'}


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'n_perm': N_PERM, 'statistic': 'delta_r = r_within - r_between'}
    files = sorted((HERE / 'results').glob('r29_vectors_*.npz'))
    if not files:
        print('  no per-item tensors on disk')
        return 3
    print(f'  {len(files)} tensor file(s)')
    res = {}
    for f in files:
        stem = f.name[len('r29_vectors_'):-4]
        z = np.load(f)
        d, lay, hd = z['delta'], z['layer'], z['head']
        tag = 'qwen2.5-3b' if '3b' in f.name else 'qwen2.5-1.5b'
        nh, nkv = GQA[tag]['n_heads'], GQA[tag]['n_kv']
        rep = nh // nkv
        per_layer, obs_sum, hits = {}, 0.0, 0
        null_sums = np.zeros(N_PERM)
        for L in sorted(set(lay.tolist())):
            m = lay == L
            X = d[m][np.argsort(hd[m])]
            if X.shape[0] != nh:
                continue
            Xc = X - X.mean(1, keepdims=True)
            s = np.sqrt((Xc * Xc).sum(1, keepdims=True))
            s[s == 0] = 1.0
            C = (Xc / s) @ (Xc / s).T
            g = np.array([h // rep for h in range(nh)])
            w, b = pair_means(C, g)
            per_layer[str(L)] = {'r_within': w, 'r_between': b, 'delta_r': w - b}
            obs_sum += (w - b)
            for t in range(N_PERM):
                gp = g[rng.permutation(nh)]
                ww, bb = pair_means(C, gp)
                null_sums[t] += (ww - bb)
        nl = len(per_layer)
        p = (1 + int((null_sums >= obs_sum).sum())) / (1 + N_PERM)
        dr = [v['delta_r'] for v in per_layer.values()]
        res[stem] = {
            'n_layers': nl, 'sum_delta_r': obs_sum, 'mean_delta_r': obs_sum / nl,
            'p_label_permutation': p,
            'null_mean': float(null_sums.mean() / nl), 'null_sd': float(null_sums.std() / nl),
            'mean_r_within': float(np.mean([v['r_within'] for v in per_layer.values()])),
            'mean_r_between': float(np.mean([v['r_between'] for v in per_layer.values()])),
            'n_layers_positive': int(sum(1 for x in dr if x > 0)),
            'per_layer': per_layer}
        r = res[stem]
        print(f'    {stem:<28} r_within {r["mean_r_within"]:+.4f}  r_between '
              f'{r["mean_r_between"]:+.4f}  delta_r {r["mean_delta_r"]:+.4f}  '
              f'p {p:.5f}  positive in {r["n_layers_positive"]}/{nl} layers', flush=True)
    out['cells'] = res

    # ---- the positive control, on the cell whose null was read as a kill ----
    f0 = HERE / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off0.npz'
    if f0.exists():
        z = np.load(f0)
        nh = GQA['qwen2.5-1.5b']['n_heads']
        g = np.array([h // (nh // GQA['qwen2.5-1.5b']['n_kv']) for h in range(nh)])
        pc = positive_control(z['delta'], z['layer'], z['head'], g, nh,
                              z['delta'].shape[1], rng)
        out['positive_control'] = pc
        print(f'\n  POSITIVE CONTROL: a shared within-KV-group direction planted at a fraction '
              f'alpha of each head\'s own scale')
        print(f"    {'alpha':<10}{'delta_r':<12}{'p':<11}fires at 0.05")
        for v in pc['per_alpha'].values():
            print(f"    {v['alpha']:<10.2f}{v['delta_r']:<12.4f}{v['p']:<11.5f}"
                  f"{v['fires_at_0.05']}")
        print(f"    -> blind at alpha <= {pc['largest_alpha_MISSED']}, detects at alpha >= "
              f"{pc['smallest_alpha_DETECTED']}")
        print('    ANY NULL THIS FILE EMITS IS SCOPED TO THAT FLOOR.')

    # ---- is delta_r a function of what is already published? report the RESIDUAL ----
    f0 = HERE / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off0.npz'
    ref = REPO / 'R11_instrument_noise' / 'results' / 'r11_itemsA_qwen2.5-1.5b.json'
    if f0.exists() and ref.exists():
        key = 'qwen2.5-1.5b_I_final_off0'
        pl = res[key]['per_layer']
        L = {int(k): v for k, v in json.load(open(ref))['layers'].items()}
        rows = []
        for lk, v in pl.items():
            li = int(lk)
            if li not in L or 'per_head_sem' not in L[li]:
                continue
            ph, ps = L[li]['per_head'], L[li]['per_head_sem']
            mags = [abs(ph[str(h)]) for h in range(len(ph))]
            sems = [ps[str(h)] for h in range(len(ps))]
            rows.append([v['delta_r'], li,
                         math.log(sum(mags) / len(mags)),
                         math.log(sum(sems) / len(sems)),
                         math.log(sum(mags) / len(mags)) - math.log(sum(sems) / len(sems))])
        A = np.array(rows)
        y, X = A[:, 0], np.column_stack([np.ones(len(A)), A[:, 1:]])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        r2 = 1 - resid.var(ddof=0) / y.var(ddof=0) if y.var() > 0 else float('nan')
        out['identity_check'] = {
            'note': 'delta_r regressed on layer index, log mean |per_head|, log mean per_head_sem, '
                    'and their difference (a log SNR)',
            'r2_explained_by_published': float(r2),
            'residual_sd': float(resid.std(ddof=1)),
            'target_sd': float(y.std(ddof=1)), 'n_layers': len(A)}
        print(f'\n  IDENTITY CHECK: delta_r regressed on layer, log|per_head|, log sem and log snr'
              f' -> R2 {r2:.4f}   residual sd {resid.std(ddof=1):.4f} of a target sd '
              f'{y.std(ddof=1):.4f}')
        print('  (a coordinate with no residual is an identity -- that is how Lambda died)')

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r29_kv_item_patterns.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
