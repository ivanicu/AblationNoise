#!/usr/bin/env python3
"""Is the shared item field the INSTRUMENT? Ivan's world WC. Zero forwards.

R30's two-way decomposition found a shared item direction that predicts HELD-OUT heads at
cross-fit R2 0.49-0.66 against a marginal-preserving null floor of 0.005-0.017. That number is
worthless until WC is separated from a mechanism:

    WC   the leading item direction IS baseline margin / an observable item property, so the
         "shared field" is a property of the EVALUATION SET, not of the network

Observable item properties available on disk without a forward pass: base margin per item, its
absolute value, its square, and its within-set rank. All live in the same 120-dim item space as v1,
so the comparison is direct.

═══ REGISTERED BEFORE THE RUN. Thresholds fixed here, in this file, and not amended. ═══

  R2_field   cross-fit held-out R2 using v1 estimated on the FIT HALF ONLY
  R2_obs     cross-fit held-out R2 using the 4-dim observable basis {1, base, |base|, rank(base)}
  R2_perp    cross-fit held-out R2 using v1 RESIDUALISED against that observable basis

  ratio = R2_perp / R2_field

  ratio <  0.50 in >=2 of 3 cells   ->  WC SURVIVES: half or more of the field's predictive power
                                        is observable-item-property content
  ratio >= 0.80 in ALL 3 cells      ->  WC DEAD as an explanation of the field
  otherwise                          ->  UNVERIFIED, partial

═══ POSITIVE CONTROL, MANDATORY, RUNS FIRST ═══
A high ratio from an instrument that has never returned a low one is silence, not an acquittal. So
the same pipeline is run on a SYNTHETIC matrix built as outer(u_h, base_i) + noise -- a matrix where
the field IS the instrument by construction. The instrument must return a LOW ratio there. If the
control does not return ratio < 0.50, the observed ratio is UNVERIFIED whatever it is.

═══ TWO DEFECTS OF THE PREVIOUS FILE, FIXED HERE ═══
1. two_way_decomposition.py centred on the FULL matrix and then split, so mu and beta_i were
   estimated using the held-out rows -- a leak on exactly the axis being predicted. Here the
   centering is estimated on the fit half and APPLIED to the held-out half. The leak's size is also
   measured, not argued: both variants are reported.
2. Cross-fit R2 was sum-of-squares weighted, so large-norm heads dominated. An unweighted median
   over held-out heads is reported alongside.

NO WORLD IS DECLARED BY THIS FILE. It emits ratios; the registered rule above reads them.
"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
RULE = {'wc_survives_if_ratio_below': 0.50, 'wc_dead_if_ratio_atleast': 0.80,
        'cells_required_survive': 2, 'cells_required_dead': 3,
        'control_must_return_ratio_below': 0.50}


def obs_basis(base):
    """Observable item properties, orthonormalised. Deliberately generous to WC: 4 dims against v1's 1."""
    r = np.argsort(np.argsort(base)).astype(np.float64) / len(base)
    M = np.stack([np.ones_like(base), base, np.abs(base), r], 1)
    Q, _ = np.linalg.qr(M)
    return Q


def fit_center(A):
    """mu, beta from the FIT half only. alpha is per-row so it is re-estimated on each half."""
    mu = A.mean()
    beta = A.mean(0) - mu
    return mu, beta


def resid(X, mu, beta):
    Y = X - mu - beta[None, :]
    return Y - Y.mean(1)[:, None]


def score(B, V):
    """Held-out R2 on direction(s) V. Returns ss-weighted and unweighted-median-over-heads."""
    P = B @ V @ V.T
    ss = (B ** 2).sum()
    w = float(1 - ((B - P) ** 2).sum() / ss) if ss > 0 else float('nan')
    per = []
    for j in range(B.shape[0]):
        s = (B[j] ** 2).sum()
        if s > 0:
            per.append(1 - ((B[j] - P[j]) ** 2).sum() / s)
    return w, float(np.median(per)) if per else float('nan')


def run(D, base, rng, leak=False):
    n = D.shape[0]
    idx = rng.permutation(n)
    a, b = idx[:n // 2], idx[n // 2:]
    if leak:                                    # the previous file's behaviour, for size comparison
        mu, beta = fit_center(D)
    else:
        mu, beta = fit_center(D[a])
    A, B = resid(D[a], mu, beta), resid(D[b], mu, beta)
    _, _, Vt = np.linalg.svd(A, full_matrices=False)
    v1 = Vt[0][:, None]
    Q = obs_basis(base)
    p = v1 - Q @ (Q.T @ v1)
    nrm = np.linalg.norm(p)
    vperp = p / nrm if nrm > 1e-12 else v1 * 0.0
    f_w, f_m = score(B, v1)
    o_w, o_m = score(B, Q)
    p_w, p_m = score(B, vperp)
    return {'R2_field': f_w, 'R2_field_median_head': f_m,
            'R2_obs_4dim': o_w, 'R2_obs_4dim_median_head': o_m,
            'R2_perp': p_w, 'R2_perp_median_head': p_m,
            'ratio': p_w / f_w if f_w > 0 else float('nan'),
            'ratio_median_head': p_m / f_m if f_m > 0 else float('nan'),
            'cos_v1_obs_span': float(np.linalg.norm(Q.T @ v1)),
            'corr_v1_base': float(np.corrcoef(v1[:, 0], base)[0, 1]),
            'corr_v1_absbase': float(np.corrcoef(v1[:, 0], np.abs(base))[0, 1])}


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'question': "Ivan world WC: is the shared item field an observable property of the "
                       "evaluation set rather than a network mechanism?"}

    # ---- POSITIVE CONTROL FIRST. The field IS the instrument by construction. ----
    print('  POSITIVE CONTROL  (synthetic: delta = outer(u_h, base) + noise; field IS the instrument)')
    ctrl = {}
    zc = np.load(sorted((REPO / 'R29_cancellation' / 'results').glob('r29_vectors_*.npz'))[0])
    bc = zc['base'].astype(np.float64)
    for sn in (0.0, 0.5, 1.0):
        u = rng.standard_normal(336)
        S = np.outer(u, bc - bc.mean())
        S = S + sn * S.std() * rng.standard_normal(S.shape)
        r = run(S, bc, np.random.default_rng(SEED))
        ctrl[f'noise_{sn}'] = r
        print(f"    noise {sn:<4} R2_field {r['R2_field']:+.4f}  R2_obs {r['R2_obs_4dim']:+.4f}  "
              f"R2_perp {r['R2_perp']:+.4f}  ratio {r['ratio']:+.4f}")
    out['positive_control'] = ctrl
    cmax = max(v['ratio'] for v in ctrl.values())
    ctrl_ok = cmax < RULE['control_must_return_ratio_below']
    print(f"    control max ratio {cmax:.4f}  <  {RULE['control_must_return_ratio_below']}  "
          f"-> {'INSTRUMENT CAN DETECT WC' if ctrl_ok else 'INSTRUMENT BLIND, EVERYTHING BELOW IS UNVERIFIED'}")
    out['control_passed'] = bool(ctrl_ok)

    # ---- the real cells ----
    print('\n  OBSERVED')
    res = {}
    for f in sorted((REPO / 'R29_cancellation' / 'results').glob('r29_vectors_*.npz')):
        stem = f.name[len('r29_vectors_'):-4]
        z = np.load(f)
        D, base = z['delta'].astype(np.float64), z['base'].astype(np.float64)
        r = run(D, base, np.random.default_rng(SEED))
        r['leak_variant_R2_field'] = run(D, base, np.random.default_rng(SEED), leak=True)['R2_field']
        r['leak_size'] = r['leak_variant_R2_field'] - r['R2_field']
        # A pooled R2 on ONE head split swings 3.4x here (measured next door in
        # two_way_decomposition.py). The RATIO shares its split so most of that cancels -- but
        # "most" is not a measurement. 30 draws, and the registered rule reads the MEAN.
        rg = np.random.default_rng(SEED + 1)
        d30 = [run(D, base, rg) for _ in range(30)]
        r['ratio_30draws_mean'] = float(np.mean([x['ratio'] for x in d30]))
        r['ratio_30draws_sd'] = float(np.std([x['ratio'] for x in d30], ddof=1))
        r['ratio_30draws_min'] = float(min(x['ratio'] for x in d30))
        r['ratio_30draws_max'] = float(max(x['ratio'] for x in d30))
        r['R2_field_30draws_sd'] = float(np.std([x['R2_field'] for x in d30], ddof=1))
        r['ratio'] = r['ratio_30draws_mean']          # the rule reads the mean, not one draw
        res[stem] = r
        print(f'\n    {stem}')
        print(f"      R2_field  {r['R2_field']:+.4f} (median head {r['R2_field_median_head']:+.4f})"
              f"   leak-variant {r['leak_variant_R2_field']:+.4f}  leak {r['leak_size']:+.4f}")
        print(f"      R2_obs    {r['R2_obs_4dim']:+.4f} (median head {r['R2_obs_4dim_median_head']:+.4f})"
              f"   <- 4 dims, generous to WC")
        print(f"      R2_perp   {r['R2_perp']:+.4f} (median head {r['R2_perp_median_head']:+.4f})")
        print(f"      ratio     {r['ratio']:.4f} +-{r['ratio_30draws_sd']:.4f} over 30 draws "
              f"[{r['ratio_30draws_min']:.4f},{r['ratio_30draws_max']:.4f}]  (single-draw median-head {r['ratio_median_head']:.4f})")
        print(f"      |proj v1 onto obs span| {r['cos_v1_obs_span']:.4f}   "
              f"corr(v1,base) {r['corr_v1_base']:+.4f}   corr(v1,|base|) {r['corr_v1_absbase']:+.4f}")
    out['cells'] = res

    ratios = [v['ratio'] for v in res.values()]
    n_surv = sum(1 for x in ratios if x < RULE['wc_survives_if_ratio_below'])
    n_dead = sum(1 for x in ratios if x >= RULE['wc_dead_if_ratio_atleast'])
    if not ctrl_ok:
        verdict = 'UNVERIFIED_CONTROL_FAILED'
    elif n_surv >= RULE['cells_required_survive']:
        verdict = 'WC_SURVIVES'
    elif n_dead >= RULE['cells_required_dead']:
        verdict = 'WC_DEAD'
    else:
        verdict = 'UNVERIFIED_PARTIAL'
    out['n_cells_below_0p50'] = n_surv
    out['n_cells_atleast_0p80'] = n_dead
    out['verdict'] = verdict
    print(f"\n  registered rule: {n_surv}/3 below 0.50, {n_dead}/3 at or above 0.80  ->  {verdict}")

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r30_wc_field_is_instrument.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
