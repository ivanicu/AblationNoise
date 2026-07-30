#!/usr/bin/env python3
"""Are KV-group loadings really anti-correlated, or is 0.1468 vs 1/6 nothing? Zero forwards.

R33's gate failure produced a fact nobody was looking for. frac0 -- the fraction of loading energy
removed by subtracting a head's own KV-group mean -- is 0.1468. Removing the mean of m INDEPENDENT
rows removes exactly 1/m = 0.16667 in expectation. Positively correlated rows lose MORE than 1/6;
anti-correlated rows lose LESS.

    0.1468 < 0.16667   =>   loadings inside a KV group are ANTI-correlated

If that is real it kills a whole surrogate family -- every "shared group field + private + noise"
model has positively correlated rows and therefore a hard floor at 1/6, which is exactly why R33's
surrogate could not be matched and why R32's M1 "match" at 0.1585 sat on the wrong side of 1/6 the
entire time.

But 1/6 is an ANALYTIC expectation, and registering against an analytic expectation of a null is the
single defect behind five retractions in this programme. So this file does not compare to 1/6.

═══ THE NULL IS DERIVED FROM THE DATA, NOT FROM A FAMILY ═══
Keep every loading row EXACTLY as measured and permute only WHICH HEADS FORM A GROUP. Two versions,
because they answer different questions:

    within-layer   permute head labels inside each layer -> groups still contain 6 same-layer heads,
                   only the partition into two groups of 6 moves. Isolates the KV boundary.
    global         permute head labels across the whole model -> groups become arbitrary 6-subsets.
                   Isolates "grouping at all" from "this grouping".

Nothing is generated, nothing is assumed about the rows' distribution, and the family-mismatch
problem cannot arise because there is no family.

═══ REGISTERED BEFORE THE RUN ═══
  T1  observed frac0 inside the WITHIN-LAYER null's central 95% band
      ->  the anti-correlation is NOT a property of the KV boundary, and the surrogate-family
          refutation in 8ed16b4 loses its basis
  T2  observed below that band's lower edge in BOTH models
      ->  it IS a property of the KV boundary
  A single model is n=1 and is reported as such; 3b off0 exists and is a free second measurement
  here because this statistic needs only ONE item set, not a replicate pair.
  10000 permutation draws. No analytic expectation is used as a threshold anywhere.
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
RULE = {'n_perm': N_PERM, 'band': [2.5, 97.5], 'rank': RANK,
        'analytic_reference_NOT_a_threshold': 1 / 6}


def two_way_resid(D):
    mu = D.mean()
    return D - mu - (D.mean(1) - mu)[:, None] - (D.mean(0) - mu)[None, :]


def loadings(D, rank=RANK):
    E = two_way_resid(D)
    U, S, Vt = np.linalg.svd(E, full_matrices=False)
    E1 = E - S[0] * np.outer(U[:, 0], Vt[0])
    U2, S2, _ = np.linalg.svd(E1, full_matrices=False)
    return U2[:, :rank] * S2[:rank]


def frac0(A, blk):
    P = A.copy()
    for g in np.unique(blk):
        m = blk == g
        P[m] -= A[m].mean(0)
    return float(1 - (P ** 2).sum() / (A ** 2).sum())


def perm_within_layer(lay, rng):
    p = np.arange(len(lay))
    for L in np.unique(lay):
        i = np.where(lay == L)[0]
        p[i] = i[rng.permutation(len(i))]
    return p


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'question': 'is frac0 < 1/6 a property of the KV boundary, tested against a null built '
                       'by permuting WHICH HEADS FORM A GROUP and generating nothing'}
    res = {}
    for tag, per_group in (('1.5b', 6), ('3b', 8)):
        f = REPO / 'R29_cancellation' / 'results' / f'r29_vectors_qwen2.5-{tag}_I_final_off0.npz'
        if not f.exists():
            continue
        z = np.load(f)
        D = z['delta'].astype(np.float64)
        lay, hd = z['layer'].astype(np.int64), z['head'].astype(np.int64)
        A = loadings(D)
        blk = lay * 2 + hd // per_group
        obs = frac0(A, blk)
        wl = np.array([frac0(A[perm_within_layer(lay, rng)], blk) for _ in range(N_PERM)])
        gl = np.array([frac0(A[rng.permutation(len(blk))], blk) for _ in range(N_PERM)])
        band_w = [float(np.percentile(wl, 2.5)), float(np.percentile(wl, 97.5))]
        band_g = [float(np.percentile(gl, 2.5)), float(np.percentile(gl, 97.5))]
        # per-layer profile: does the anti-correlation vary with depth?
        prof = {}
        for L in sorted(set(lay.tolist())):
            m = lay == L
            prof[int(L)] = frac0(A[m], blk[m])
        ks = sorted(prof)
        r = {'n_heads': int(hd.max()) + 1, 'per_group': per_group,
             'analytic_1_over_m': 1 / per_group, 'observed_frac0': obs,
             'within_layer_null': {'median': float(np.median(wl)), 'band95': band_w,
                                   'sd': float(wl.std(ddof=1)),
                                   'p_below': float((wl <= obs).mean())},
             'global_null': {'median': float(np.median(gl)), 'band95': band_g,
                             'sd': float(gl.std(ddof=1)), 'p_below': float((gl <= obs).mean())},
             'below_within_layer_band': bool(obs < band_w[0]),
             'inside_within_layer_band': bool(band_w[0] <= obs <= band_w[1]),
             'per_layer_frac0': prof,
             'first_quarter_mean': float(np.mean([prof[k] for k in ks[:len(ks) // 4]])),
             'last_quarter_mean': float(np.mean([prof[k] for k in ks[-(len(ks) // 4):]]))}
        res[tag] = r
        print(f'\n  {tag}   {r["n_heads"]} query heads, {per_group} per KV group, '
              f'analytic 1/m = {1 / per_group:.5f}')
        print(f"    observed frac0                 {obs:.5f}")
        print(f"    within-layer permutation null  median {r['within_layer_null']['median']:.5f}  "
              f"95% band [{band_w[0]:.5f}, {band_w[1]:.5f}]  P(null <= obs) "
              f"{r['within_layer_null']['p_below']:.5f}")
        print(f"    global permutation null        median {r['global_null']['median']:.5f}  "
              f"95% band [{band_g[0]:.5f}, {band_g[1]:.5f}]  P(null <= obs) "
              f"{r['global_null']['p_below']:.5f}")
        print(f"    per-layer frac0: first quarter {r['first_quarter_mean']:.5f}   "
              f"last quarter {r['last_quarter_mean']:.5f}")
    out['cells'] = res

    below = [v['below_within_layer_band'] for v in res.values()]
    inside = [v['inside_within_layer_band'] for v in res.values()]
    verdict = ('KV_BOUNDARY_PROPERTY' if below and all(below)
               else 'NOT_A_KV_BOUNDARY_PROPERTY' if inside and all(inside)
               else 'UNVERIFIED_PARTIAL')
    out['verdict'] = verdict
    print(f'\n  VERDICT  {verdict}   (n = {len(res)} model(s))')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r33_anticorrelation.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
