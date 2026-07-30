#!/usr/bin/env python3
"""Ivan's step 10.1-10.3, verbatim: two-way centering, marginal-preserving nulls, cross-fit. Zero forwards.

His instruction, and it is the whole discipline of this file:

    "绝对不要直接对 raw matrix 做 PCA,然后看到 lambda_1 很大就命名为'共同机制'."

    Delta_{h,i} = mu + alpha_h + beta_i + u_h^T v_i + e_{h,i}

    alpha_h   head main effect
    beta_i    global item susceptibility
    u^T v     low-rank head x item selective interaction
    e         high-rank private residual

The four worlds:
  WA  one shared item field       Delta ~ a_h b_i, near rank 1, item rankings agree across heads
  WB  shared field + private selectivity
  WC  the shared field IS the instrument -- baseline margin, position, answer-token prior
  WD  high-rank, interaction dominated; any low-rank "explanation" is compression, not mechanism

THREE NULLS, none of them iid Gaussian, because an iid null makes ANY heteroscedastic matrix look
low-rank:
  A  permute item labels INDEPENDENTLY WITHIN EACH HEAD -- preserves every head's marginal
     distribution, sparsity, skew, tails and SNR, destroys only cross-head item alignment
  B  fix item norms, random re-sign -- is the low-rank structure only item-wise heteroscedasticity
  C  row/column variance preserving -- preserves head variance AND item variance

CROSS-FIT IS MANDATORY. Split heads in half, estimate the item field on one half, test whether it
predicts the other. Without held-out prediction a PCA is descriptive compression. Also fit on one GQA
group and predict the other, and fit on early layers and predict late.

This file emits variance shares and out-of-sample R2. NO WORLD IS DECLARED.
"""
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
N_NULL = 400


def two_way(D):
    """mu + alpha_h + beta_i + E. Returns the pieces and their variance shares."""
    mu = D.mean()
    alpha = D.mean(1) - mu
    beta = D.mean(0) - mu
    E = D - mu - alpha[:, None] - beta[None, :]
    tot = ((D - mu) ** 2).sum()
    return {'mu': float(mu), 'alpha': alpha, 'beta': beta, 'E': E,
            'share_head_main': float((alpha ** 2).sum() * D.shape[1] / tot),
            'share_item_main': float((beta ** 2).sum() * D.shape[0] / tot),
            'share_interaction': float((E ** 2).sum() / tot)}


def lam1_share(E):
    s = np.linalg.svd(E, compute_uv=False)
    return float(s[0] ** 2 / (s ** 2).sum())


def null_A(D, rng):
    """Permute item labels independently within each head. Marginals exactly preserved."""
    return np.array([row[rng.permutation(D.shape[1])] for row in D])


def null_B(D, rng):
    """Random re-sign per entry: keeps |value| exactly, destroys sign alignment."""
    return D * rng.choice([-1.0, 1.0], size=D.shape)


def null_C(D, rng, rounds=6):
    """Row AND column sd preserving. The one-pass version does NOT do this -- the column rescale
    destroys the row match it just imposed -- so this is iterative proportional fitting, and the
    achieved match is measured and returned by null_C_report() rather than asserted."""
    Z = rng.standard_normal(D.shape)
    rs, cs = D.std(1, ddof=1), D.std(0, ddof=1)
    for _ in range(rounds):
        Z *= (rs[:, None] / Z.std(1, ddof=1)[:, None])
        Z *= (cs[None, :] / Z.std(0, ddof=1)[None, :])
    return Z


def null_C_report(D, rng):
    """Max relative sd mismatch after IPF, on both margins. An unmeasured null is an asserted null."""
    Z = null_C(D, rng)
    return {'max_rel_row_sd_err': float(np.max(np.abs(Z.std(1, ddof=1) / D.std(1, ddof=1) - 1))),
            'max_rel_col_sd_err': float(np.max(np.abs(Z.std(0, ddof=1) / D.std(0, ddof=1) - 1)))}


def crossfit(E, rows_a, rows_b, k=1):
    """Fit the item field on rows_a, score rows_b. Out-of-sample R2, never in-sample.

    Returns BOTH the pooled sum-of-squares R2 (which large-norm heads dominate) and the median
    over held-out heads of each head's own R2. They differ by up to 10x here, and the pooled
    number alone is a claim about variance, not about heads."""
    A, B = E[rows_a], E[rows_b]
    U, S, Vt = np.linalg.svd(A, full_matrices=False)
    V = Vt[:k].T                                    # item directions from the A half only
    P = B @ V @ V.T                                 # project B onto them
    ss = (B ** 2).sum()
    pooled = float(1 - ((B - P) ** 2).sum() / ss) if ss > 0 else float('nan')
    per = [1 - ((B[j] - P[j]) ** 2).sum() / (B[j] ** 2).sum()
           for j in range(B.shape[0]) if (B[j] ** 2).sum() > 0]
    return pooled, (float(np.median(per)) if per else float('nan')), per


def floored(D, rows_a, rows_b, rng, n=40):
    """Every split gets its own null-A floor. An unfloored cross-fit R2 has no scale."""
    v = [crossfit(two_way(null_A(D, rng))['E'], rows_a, rows_b)[0] for _ in range(n)]
    return {'floor_mean': float(np.mean(v)), 'floor_sd': float(np.std(v, ddof=1)),
            'floor_p95': float(np.percentile(v, 95)), 'floor_n': n}


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'n_null': N_NULL,
           'protocol': "Ivan 2026-07-30 steps 10.1-10.3: two-way centering, marginal-preserving "
                       "nulls, cross-fit held-out heads"}
    res = {}
    for f in sorted((REPO / 'R29_cancellation' / 'results').glob('r29_vectors_*.npz')):
        stem = f.name[len('r29_vectors_'):-4]
        z = np.load(f)
        D = z['delta'].astype(np.float64)
        lay, hd = z['layer'], z['head']
        nh = int(hd.max()) + 1
        rep = nh // 2
        tw = two_way(D)
        E = tw['E']
        obs = lam1_share(E)
        nulls = {}
        for name, fn in (('A_item_perm', null_A), ('B_resign', null_B), ('C_rowcol_sd', null_C)):
            v = [lam1_share(two_way(fn(D, rng))['E']) for _ in range(N_NULL)]
            nulls[name] = {'median': float(np.median(v)), 'p95': float(np.percentile(v, 95)),
                           'sd': float(np.std(v, ddof=1)),
                           'z': float((obs - np.median(v)) / np.std(v, ddof=1))}
        # cross-fit: random half of heads, then GQA group, then early vs late layers.
        # EVERY split carries its own null-A floor -- an unfloored R2 has no scale.
        n = D.shape[0]
        idx = rng.permutation(n)
        grp = np.array([h // rep for h in hd])
        med = np.median(lay)
        splits = {'gqa_group': (np.where(grp == 0)[0], np.where(grp == 1)[0]),
                  'early_to_late': (np.where(lay <= med)[0], np.where(lay > med)[0])}
        xf = {}
        for sname, (ra, rb) in splits.items():
            pooled, medr, _ = crossfit(E, ra, rb)
            fl = floored(D, ra, rb, rng)
            xf[sname] = {'r2_pooled': pooled, 'r2_median_head': medr, **fl,
                         'z_over_floor': (pooled - fl['floor_mean']) / fl['floor_sd']}
        # random_half is NOT a single draw. One draw moved 0.6591 -> 0.2396 on an rng-order change
        # alone, because head norms are heavy-tailed and a pooled R2 is dominated by whichever big
        # heads land in the held-out set. 30 splits, mean and sd, or it is not a number.
        rp, rm = [], []
        for _ in range(30):
            j = rng.permutation(n)
            p_, m_, _ = crossfit(E, j[:n // 2], j[n // 2:])
            rp.append(p_)
            rm.append(m_)
        j = rng.permutation(n)
        flr = floored(D, j[:n // 2], j[n // 2:], rng)
        xf['random_half_30draws'] = {
            'r2_pooled': float(np.mean(rp)), 'r2_pooled_sd': float(np.std(rp, ddof=1)),
            'r2_pooled_min': float(min(rp)), 'r2_pooled_max': float(max(rp)),
            'r2_median_head': float(np.mean(rm)), 'r2_median_head_sd': float(np.std(rm, ddof=1)),
            **flr, 'z_over_floor': (float(np.mean(rp)) - flr['floor_mean']) / flr['floor_sd']}
        res[stem] = {
            'n_cells': int(D.shape[0]), 'n_items': int(D.shape[1]),
            'share_head_main': tw['share_head_main'],
            'share_item_main': tw['share_item_main'],
            'share_interaction': tw['share_interaction'],
            'lambda1_share_of_interaction': obs,
            'nulls': nulls,
            'null_C_achieved_margins': null_C_report(D, rng),
            'crossfit': xf}
        r = res[stem]
        print(f'\n  {stem}   {r["n_cells"]} cells x {r["n_items"]} items')
        print(f"    variance shares:  head main {r['share_head_main']:.4f}   "
              f"item main {r['share_item_main']:.4f}   interaction {r['share_interaction']:.4f}")
        print(f"    lambda1 share OF THE INTERACTION (two-way centred): {obs:.4f}")
        for k2, v in nulls.items():
            print(f"      null {k2:<14} median {v['median']:.4f}  p95 {v['p95']:.4f}  "
                  f"z {v['z']:+.2f}")
        cr = r['null_C_achieved_margins']
        print(f"      null C achieved margins after IPF: row err {cr['max_rel_row_sd_err']:.2e}"
              f"  col err {cr['max_rel_col_sd_err']:.2e}")
        print(f"    CROSS-FIT out-of-sample R2 (fit item field on one set, score the other):")
        print(f"      {'split':<16}{'pooled':<10}{'median head':<14}{'null floor':<22}z")
        for sname, v in xf.items():
            print(f"      {sname:<16}{v['r2_pooled']:<+10.4f}{v['r2_median_head']:<+14.4f}"
                  f"{v['floor_mean']:+.4f}+-{v['floor_sd']:.4f} (p95 {v['floor_p95']:+.4f})"
                  f"  {v['z_over_floor']:+.1f}")
    out['cells'] = res
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r30_two_way.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
