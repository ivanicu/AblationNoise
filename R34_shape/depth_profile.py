#!/usr/bin/env python3
"""Depth is the named generator. What SHAPE does it generate, and is my control for it any good?

Two things are owed after R34, and neither depends on the model-versus-measurement ruling.

DEBT 1 — THE CONFOUND CONTROL WAS NEARLY DEGENERATE AND I SAID SO IN THE COMMIT.
R34 controlled for depth by ranking both variables INSIDE each layer. But there are exactly 2 KV
groups per layer in BOTH models (12 query heads / 2 KV, 16 / 2), so each stratum has n = 2 and a
within-stratum rank correlation can only ever take two values. That is not a control, it is a coin.
Replaced here by a PARTIAL rank correlation on all 56 / 72 groups: residualise rank(frac0_g) and
rank(median ||E_h||_2) on rank(layer), then correlate the residuals. Every group contributes.

DEBT 2 — THE ANCHOR. Ivan asked 这个分布长什么样子, 为什么不同地方会有不一样. R34 answered WHERE
(depth, rho +0.7321 and +0.7264) and never answered WHAT SHAPE. The question that separates a real
answer from a restatement:

    is the depth effect a SHIFT, or a SCALE?

If deeper layers merely multiply every head's effect by a common factor, then the distribution has
ONE shape and depth sets only its size -- the coefficient of variation is flat in depth, and
"different places are different" reduces to a single scalar per layer. If the shape itself changes
with depth -- heavier tails, more heads at zero -- then depth is not one number and the distribution
is a family, not a curve.

That is a statement with units on both sides and it is falsifiable in one measurement.

═══ REGISTERED BEFORE THE RUN ═══
  P   PARTIAL rank correlation of frac0_g and median ||E_h||_2 given layer, permutation null on the
      residuals, 10000 draws. This REPLACES R34's within-layer control; R34's registered verdict
      (DUPLICATION_DEAD, from the RAW rho) is not reopened -- only its control is.
      IF |partial rho| >= 0.25 with p <= 0.01 in BOTH models, duplication returns as a candidate
      and R34's control was the thing that was broken. Otherwise DUPLICATION stays dead.

  S   SHAPE. Per layer, over that layer's heads: median ||E_h||_2 (margin-nats), IQR, and
      cv = IQR / median (dimensionless).
      IF sd(cv across layers) / mean(cv) < 0.25 in BOTH models
      ->  DEPTH_IS_PURE_SCALE: one shape, resized by depth. The distribution's shape is
          depth-invariant and the whole depth story is a single scalar per layer.
      IF >= 0.25 in either -> DEPTH_CHANGES_THE_SHAPE, and the shape must be described per depth.

  F   FUNCTIONAL FORM, reported not gated: OLS of log(median ||E_h||_2) on layer index, giving a
      per-layer multiplicative rate and its R^2. A high R^2 means the depth profile is exponential,
      which is a stronger statement than a rank correlation and carries a unit (nats per layer).

No threshold is amended after any number is seen. n = 2 models, both from off0 which is all this
statistic needs.
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
RULE = {'P_abs_rho': 0.25, 'P_max_p': 0.01, 'S_cv_stability': 0.25, 'n_perm': N_PERM}


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


def pearson(a, b):
    a = a - a.mean()
    b = b - b.mean()
    d = np.sqrt((a ** 2).sum() * (b ** 2).sum())
    return float((a * b).sum() / d) if d > 0 else float('nan')


def resid_on(y, x):
    x = x - x.mean()
    return y - y.mean() - x * ((x * (y - y.mean())).sum() / (x ** 2).sum())


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'debt1': 'R34 stratified by layer with n=2 KV groups per stratum in both models; '
                    'replaced by a partial rank correlation using all groups',
           'debt2': 'is the depth effect a SHIFT or a SCALE — does the shape change with depth?'}
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

        # ── P: partial rank correlation, all groups ──
        gid = lay * 2 + hd // per_group
        gs = np.unique(gid)
        fg, mg, gl = np.zeros(len(gs)), np.zeros(len(gs)), np.zeros(len(gs))
        for k, g in enumerate(gs):
            m = gid == g
            P = A[m] - A[m].mean(0)
            fg[k] = 1 - (P ** 2).sum() / (A[m] ** 2).sum()
            mg[k] = np.median(nrm[m])
            gl[k] = lay[m][0]
        rf = resid_on(rankdata(fg), rankdata(gl))
        rm = resid_on(rankdata(mg), rankdata(gl))
        pr = pearson(rf, rm)
        nl = np.array([pearson(rf[rng.permutation(len(rf))], rm) for _ in range(N_PERM)])
        pp = float((np.abs(nl) >= abs(pr)).mean())

        # ── S: shape per layer ──
        Ls = sorted(set(lay.tolist()))
        med = np.array([np.median(nrm[lay == L]) for L in Ls])
        iqr = np.array([np.percentile(nrm[lay == L], 75) - np.percentile(nrm[lay == L], 25)
                        for L in Ls])
        cv = iqr / med
        cvstab = float(cv.std(ddof=1) / cv.mean())

        # ── F: functional form ──
        x = np.array(Ls, float)
        y = np.log(med)
        b = ((x - x.mean()) * (y - y.mean())).sum() / ((x - x.mean()) ** 2).sum()
        yhat = y.mean() + b * (x - x.mean())
        r2 = float(1 - ((y - yhat) ** 2).sum() / ((y - y.mean()) ** 2).sum())

        r = {'n_groups': int(len(gs)), 'n_layers': len(Ls), 'per_group': per_group,
             'partial_rho_given_layer': pr, 'partial_perm_p': pp,
             'partial_passes': bool(abs(pr) >= RULE['P_abs_rho'] and pp <= RULE['P_max_p']),
             'median_nats_first': float(med[0]), 'median_nats_last': float(med[-1]),
             'median_nats_min': float(med.min()), 'median_nats_max': float(med.max()),
             'cv_mean': float(cv.mean()), 'cv_sd': float(cv.std(ddof=1)),
             'cv_stability': cvstab, 'cv_min': float(cv.min()), 'cv_max': float(cv.max()),
             'depth_is_pure_scale': bool(cvstab < RULE['S_cv_stability']),
             'log_slope_nats_per_layer': float(b), 'log_fit_r2': r2,
             'fold_change_per_layer': float(np.exp(b)),
             'fold_change_first_to_last': float(med[-1] / med[0]),
             'per_layer_median_nats': {int(L): float(v) for L, v in zip(Ls, med)},
             'per_layer_cv': {int(L): float(v) for L, v in zip(Ls, cv)}}
        res[tag] = r
        print(f'\n  {tag}   {r["n_layers"]} layers, {r["n_groups"]} KV groups')
        print(f"    P  partial rho(frac0_g, median||E||  |  layer) {pr:+.4f}   perm p {pp:.5f}"
              f"   passes {r['partial_passes']}   (R34's within-layer control had n=2 per stratum)")
        print(f"    S  median ||E_h||_2 by layer: first {med[0]:.4f}  last {med[-1]:.4f}  "
              f"min {med.min():.4f}  max {med.max():.4f}  margin-nats")
        print(f"       cv = IQR/median: mean {cv.mean():.4f}  sd {cv.std(ddof=1):.4f}  "
              f"stability {cvstab:.4f}  range [{cv.min():.4f}, {cv.max():.4f}]")
        print(f"       -> {'PURE SCALE' if r['depth_is_pure_scale'] else 'SHAPE CHANGES WITH DEPTH'}"
              f"  (threshold {RULE['S_cv_stability']})")
        print(f"    F  log(median) on layer: slope {b:+.5f} nats/layer  "
              f"fold/layer {np.exp(b):.4f}x  R^2 {r2:.4f}  "
              f"first->last {med[-1] / med[0]:.2f}x")
    out['cells'] = res

    pp_ = [v['partial_passes'] for v in res.values()]
    sc = [v['depth_is_pure_scale'] for v in res.values()]
    out['P_verdict'] = ('DUPLICATION_RETURNS' if pp_ and all(pp_) else 'DUPLICATION_STAYS_DEAD')
    out['S_verdict'] = ('DEPTH_IS_PURE_SCALE' if sc and all(sc) else 'DEPTH_CHANGES_THE_SHAPE')
    print(f"\n  P -> {out['P_verdict']}     S -> {out['S_verdict']}")
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r34_depth_profile.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
