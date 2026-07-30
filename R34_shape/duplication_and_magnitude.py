#!/usr/bin/env python3
"""Back to the anchor: what GENERATES the shape of the ablation-effect distribution? Zero forwards.

Ivan's question for the whole loop, verbatim: 那这个分布长什么样子呢, 它为什么会是一个分布呢 ...
为什么不同地方会有不一样呢. The identification line closed at R33 with one certified positive; this
round returns to the distribution itself, and to a candidate generator that fell out of that line's
own failure.

frac0_g -- the fraction of a KV group's loading energy that lies in the group MEAN -- is a
dimensionless energy share, one number per KV group, n = 56 in 1.5b and n = 72 in 3b. It was
discovered as a nuisance parameter while trying to match a surrogate, and its POOLED value turned
out to describe no group at all: across the 56 groups it spans [0.0324, 0.8763] with sd 0.1866.

    frac0_g near 1   the group's six query heads are near-DUPLICATES; almost all their loading
                     energy is in what they share
    frac0_g near 0   the six are near-INDEPENDENT; almost none of it is

That is a real distribution with a unit and a spread, and this file asks whether it predicts WHERE
THE LARGE ABLATION EFFECTS SIT -- i.e. whether duplication is a generator of the magnitude
distribution's shape.

═══ REGISTERED BEFORE THE RUN ═══
  X   Spearman rho between frac0_g and median ||E_h||_2 over the heads of group g
      (units: dimensionless energy share versus margin-nats per head), with a GROUP-LABEL
      permutation p-value, in BOTH models.
  T   |X| < 0.25 in EITHER model, OR permutation p > 0.01
      ->  "within-group query-head duplication explains where large ablation effects sit" is DEAD,
          and the shape's generator must be sought in a LOCATION variable instead.

═══ THE STRONGEST CONFOUND, WRITTEN BEFORE THE RUN, WITH ITS CONTROL IN THE SAME ITERATION ═══
frac0_g and ||E_h||_2 BOTH vary with depth -- R33 measured per-layer frac0 falling 0.25406 ->
0.17251 in 1.5b and 0.29312 -> 0.09023 in 3b, and the effect magnitudes have their own depth
profile. A raw Spearman over all groups could therefore be entirely depth, with duplication
carrying nothing. So the WITHIN-LAYER version runs in the same file: rank both variables inside each
layer first, then correlate. If the raw rho survives and the within-layer rho collapses, the
generator is DEPTH and not duplication, and that is the honest answer rather than a defeat.
Both are reported. The registered threshold reads the raw rho, as instructed; the within-layer rho
is what decides what the number MEANS.

The distribution is reported as its own quantiles, never as a mean. The mean was never the object.
"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
RANK = 5
N_PERM = 10000
RULE = {'T_abs_rho': 0.25, 'max_p': 0.01, 'n_perm': N_PERM, 'rank': RANK}


def two_way_resid(D):
    mu = D.mean()
    return D - mu - (D.mean(1) - mu)[:, None] - (D.mean(0) - mu)[None, :]


def loadings(D, rank=RANK):
    E = two_way_resid(D)
    U, S, Vt = np.linalg.svd(E, full_matrices=False)
    E1 = E - S[0] * np.outer(U[:, 0], Vt[0])
    U2, S2, _ = np.linalg.svd(E1, full_matrices=False)
    return U2[:, :rank] * S2[:rank]


def rankdata(v):
    o = np.argsort(v, kind='mergesort')
    r = np.empty(len(v), float)
    r[o] = np.arange(len(v), dtype=float)
    i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and v[o[j + 1]] == v[o[i]]:
            j += 1
        r[o[i:j + 1]] = (i + j) / 2.0
        i = j + 1
    return r


def spearman(a, b):
    x, y = rankdata(a), rankdata(b)
    x = x - x.mean()
    y = y - y.mean()
    d = np.sqrt((x ** 2).sum() * (y ** 2).sum())
    return float((x * y).sum() / d) if d > 0 else float('nan')


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'question': 'does within-KV-group query-head duplication (frac0_g) predict where the '
                       'large ablation effects sit, or is it depth?'}
    res = {}
    for tag, per_group in (('1.5b', 6), ('3b', 8)):
        f = REPO / 'R29_cancellation' / 'results' / f'r29_vectors_qwen2.5-{tag}_I_final_off0.npz'
        if not f.exists():
            continue
        z = np.load(f)
        D = z['delta'].astype(np.float64)
        lay, hd = z['layer'].astype(np.int64), z['head'].astype(np.int64)
        A, E = loadings(D), two_way_resid(D)
        nrm = np.linalg.norm(E, axis=1)
        gid = lay * 2 + hd // per_group
        gs = np.unique(gid)
        fg = np.zeros(len(gs))
        mg = np.zeros(len(gs))
        gl = np.zeros(len(gs), dtype=int)
        for k, g in enumerate(gs):
            m = gid == g
            P = A[m] - A[m].mean(0)
            fg[k] = 1 - (P ** 2).sum() / (A[m] ** 2).sum()
            mg[k] = np.median(nrm[m])
            gl[k] = lay[m][0]
        rho = spearman(fg, mg)
        nl = np.array([spearman(fg[rng.permutation(len(fg))], mg) for _ in range(N_PERM)])
        p = float((np.abs(nl) >= abs(rho)).mean())
        # within-layer control: rank both inside each layer, then correlate the ranks
        fw, mw = np.zeros(len(gs)), np.zeros(len(gs))
        for L in np.unique(gl):
            m = gl == L
            if m.sum() > 1:
                fw[m] = rankdata(fg[m]) - rankdata(fg[m]).mean()
                mw[m] = rankdata(mg[m]) - rankdata(mg[m]).mean()
        rho_w = spearman(fw, mw)
        nlw = np.array([spearman(fw[rng.permutation(len(fw))], mw) for _ in range(N_PERM)])
        p_w = float((np.abs(nlw) >= abs(rho_w)).mean())
        qs = [float(np.percentile(fg, x)) for x in (0, 10, 25, 50, 75, 90, 100)]
        r = {'n_groups': int(len(gs)), 'per_group': per_group,
             'frac0_g_quantiles_0_10_25_50_75_90_100': qs,
             'frac0_g_sd': float(fg.std(ddof=1)),
             'median_norm_nats_quantiles': [float(np.percentile(mg, x)) for x in (0, 50, 100)],
             'spearman_raw': rho, 'p_perm_raw': p,
             'spearman_within_layer': rho_w, 'p_perm_within_layer': p_w,
             'spearman_frac0_vs_layer': spearman(gl.astype(float), fg),
             'spearman_norm_vs_layer': spearman(gl.astype(float), mg),
             'passes_registered': bool(abs(rho) >= RULE['T_abs_rho'] and p <= RULE['max_p'])}
        res[tag] = r
        print(f'\n  {tag}   {r["n_groups"]} KV groups, {per_group} query heads each')
        print(f"    frac0_g quantiles 0/10/25/50/75/90/100:  "
              + '  '.join(f'{x:.4f}' for x in qs) + f"   sd {r['frac0_g_sd']:.4f}")
        print(f"    median ||E_h||_2 per group, min/med/max (margin-nats):  "
              + '  '.join(f'{x:.4f}' for x in r['median_norm_nats_quantiles']))
        print(f"    RAW           spearman {rho:+.4f}  perm p {p:.5f}")
        print(f"    WITHIN-LAYER  spearman {rho_w:+.4f}  perm p {p_w:.5f}   <- the confound control")
        print(f"    depth: rho(layer, frac0_g) {r['spearman_frac0_vs_layer']:+.4f}   "
              f"rho(layer, median norm) {r['spearman_norm_vs_layer']:+.4f}")
    out['cells'] = res

    ok = [v['passes_registered'] for v in res.values()]
    verdict = ('DUPLICATION_PREDICTS_MAGNITUDE' if ok and all(ok) else 'DUPLICATION_DEAD')
    out['verdict'] = verdict
    if verdict == 'DUPLICATION_PREDICTS_MAGNITUDE':
        wl = [abs(v['spearman_within_layer']) for v in res.values()]
        out['survives_depth_control'] = bool(all(x >= RULE['T_abs_rho'] for x in wl))
    print(f'\n  REGISTERED T (|rho| >= {RULE["T_abs_rho"]} and p <= {RULE["max_p"]}, both models)'
          f'  ->  {verdict}')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r34_duplication_and_magnitude.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
