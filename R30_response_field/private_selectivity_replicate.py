#!/usr/bin/env python3
"""WA vs WB vs WD, plus the two calibrations that currently gate live verdicts. Zero forwards.

The navigator's binding instruction, executed -- with ONE leg corrected, and the correction is the
first thing in this file because it invalidates the threshold as issued.

═══ THE CORRECTION ═══
The instruction reads: "Same model, same 336 head-cells, same 120 items, different prompt offset =
an independent measurement of the same cell. Statistic: rho_h = corr_i(R_h^off0, R_h^off400) over
120 items."

THE TWO CELLS DO NOT SHARE ITEMS. Measured, not assumed:
    exact same order   False
    same multiset      False
    overlap of values  0 of 120
and R10_exhaustive/run.py:113 says so in its own words -- "the SAME heads on a DIFFERENT item set.
--seed-offset shifts the seed". So corr_i(R_h^off0, R_h^off400) has no item correspondence to
correlate over and cannot be computed. The threshold "median rho >= 0.20" is void as issued.

What replaces it is Ivan's own step 10.6, disjoint-item-set RULE testing. If head-private
selectivity is a real property of a HEAD, then the pattern of which heads resemble which must
survive a change of item set, even though no item is shared:

    C^{(s)}_{h,h'} = corr_i( R^{(s)}_h , R^{(s)}_{h'} )     computed WITHIN item set s
    replicate statistic = corr over off-diagonal (h,h') of  C^{(off0)} vs C^{(off400)}

Both matrices are built inside their own item set, so no cross-set item correspondence is needed.
The statistic is direction-based and is NOT invariant to permuting the item index within a head, so
it is outside the banned Lambda/G family.

═══ REGISTERED BEFORE THE RUN. Not amended after any number is seen. ═══
  L1  WB:  replicate statistic < 0.10, OR inside the head-identity null's p95
           ->  WB DEAD. Head-private selectivity is not a reproducible property of heads.
  L2  WA:  [R2_med(k=5) - floor(5)] / [R2_med(k=1) - floor(1)] >= 3.0
           ->  WA DEAD. The rank-1 field is compression of a high-rank object (WD).
           <= 1.5  ->  one direction carries it.
  L3  GATE: if the replicate positive control does not recover injected reliability MONOTONICALLY,
           the whole file returns UNVERIFIED and no world moves.
  L4  GATE: if the WC mixture control's returned ratio does not track (1 - true observable share)
           to within 0.10 at every swept share, then WC_DEAD and POSITION_DEAD stay UNVERIFIED
           AT THE THRESHOLD -- which is their current status, and this is what would clear it.

═══ WHY L4 EXISTS ═══
Both ratio instruments shipped with a positive control that was an IDENTITY, not a detection:
S = outer(u, basis_dir) forces v1 = basis_dir and the basis contains it by construction, so
ratio -> 0 is algebra. Returned 0.0000-0.0085 is round-off. The thresholds sit at 0.50 and 0.80 and
the instrument had never been run near either. The mixture family fixes exactly that.
"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
N_NULL = 400
RULE = {'L1_wb_dead_if_replicate_below': 0.10, 'L2_wa_dead_if_rank_ratio_atleast': 3.0,
        'L2_one_direction_if_rank_ratio_atmost': 1.5, 'L4_mixture_tol': 0.10, 'n_null': N_NULL}


# ───────────────────────────── shared machinery ─────────────────────────────
def two_way_resid(D):
    mu = D.mean()
    E = D - mu - (D.mean(1) - mu)[:, None] - (D.mean(0) - mu)[None, :]
    return E


def strip_rank1(E):
    U, S, Vt = np.linalg.svd(E, full_matrices=False)
    return E - S[0] * np.outer(U[:, 0], Vt[0])


def rowcorr(R):
    Z = R - R.mean(1, keepdims=True)
    Z /= np.linalg.norm(Z, axis=1, keepdims=True) + 1e-300
    return Z @ Z.T


def offdiag(C):
    n = C.shape[0]
    m = ~np.eye(n, dtype=bool)
    return C[m]


def within_layer_perm(lay, rng):
    p = np.arange(len(lay))
    for L in np.unique(lay):
        i = np.where(lay == L)[0]
        p[i] = i[rng.permutation(len(i))]
    return p


def null_A(D, rng):
    return np.array([row[rng.permutation(D.shape[1])] for row in D])


def crossfit_k(E, ra, rb, k):
    A, B = E[ra], E[rb]
    _, _, Vt = np.linalg.svd(A, full_matrices=False)
    V = Vt[:k].T
    P = B @ V @ V.T
    per = [1 - ((B[j] - P[j]) ** 2).sum() / (B[j] ** 2).sum()
           for j in range(B.shape[0]) if (B[j] ** 2).sum() > 0]
    nrm = [np.linalg.norm(B[j]) for j in range(B.shape[0]) if (B[j] ** 2).sum() > 0]
    ss = (B ** 2).sum()
    pooled = float(1 - ((B - P) ** 2).sum() / ss) if ss > 0 else float('nan')
    return pooled, float(np.median(per)), np.array(per), np.array(nrm)


# ───────────────────────────── leg 3: replicate positive control ─────────────────────────────
def replicate_control(rng):
    """Two disjoint 'item sets' sharing a per-head PRIVATE PROFILE at known reliability.

    A head's private selectivity is modelled as a low-dim loading w_h that is REUSED across both
    item sets, mixed with per-set private noise at strength (1-rel). rel=0 means the two sets share
    nothing, rel=0.9 means the head's rule is nearly identical. The statistic must recover this."""
    nh, ni, r = 336, 120, 6
    out = {}
    for rel in (0.0, 0.3, 0.6, 0.9):
        W = rng.standard_normal((nh, r))
        Cs = []
        for _ in range(2):
            Wp = rel * W + np.sqrt(max(1 - rel ** 2, 0.0)) * rng.standard_normal((nh, r))
            V = rng.standard_normal((r, ni))                 # item basis DIFFERS per set, as it must
            X = Wp @ V + 1.0 * rng.standard_normal((nh, ni))
            Cs.append(rowcorr(strip_rank1(two_way_resid(X))))
        out[f'rel_{rel}'] = float(np.corrcoef(offdiag(Cs[0]), offdiag(Cs[1]))[0, 1])
    vals = [out[f'rel_{r_}'] for r_ in (0.0, 0.3, 0.6, 0.9)]
    out['monotone'] = bool(all(vals[i] < vals[i + 1] for i in range(3)))
    return out


# ───────────────────────────── leg 5: WC mixture calibration ─────────────────────────────
def obs_basis(base):
    r = np.argsort(np.argsort(base)).astype(np.float64) / len(base)
    Q, _ = np.linalg.qr(np.stack([np.ones_like(base), base, np.abs(base), r], 1))
    return Q


def mixture_control(base, rng):
    """v_true = sqrt(s)*base_dir + sqrt(1-s)*mech_dir. The ratio MUST come back near 1-s."""
    Q = obs_basis(base)
    b = base - base.mean()
    b /= np.linalg.norm(b)
    m = rng.standard_normal(len(base))
    m -= Q @ (Q.T @ m)
    m /= np.linalg.norm(m)
    out = {}
    for s in (0.0, 0.25, 0.5, 0.75, 1.0):
        v = np.sqrt(s) * b + np.sqrt(1 - s) * m
        v /= np.linalg.norm(v)
        u = rng.standard_normal(336)
        D = np.outer(u, v) + 0.3 * rng.standard_normal((336, len(base)))
        E = two_way_resid(D)
        n = D.shape[0]
        j = rng.permutation(n)
        ra, rb = j[:n // 2], j[n // 2:]
        A, B = E[ra], E[rb]
        _, _, Vt = np.linalg.svd(A, full_matrices=False)
        v1 = Vt[0][:, None]
        p = v1 - Q @ (Q.T @ v1)
        vp = p / (np.linalg.norm(p) + 1e-300)

        def sc(V):
            P = B @ V @ V.T
            return float(1 - ((B - P) ** 2).sum() / (B ** 2).sum())

        f, pr = sc(v1), sc(vp)
        ratio = pr / f if f > 0 else float('nan')
        out[f'share_{s}'] = {'ratio': ratio, 'expected_1_minus_share': 1 - s,
                             'abs_err': abs(ratio - (1 - s))}
    out['max_abs_err'] = max(v['abs_err'] for v in out.values() if isinstance(v, dict))
    out['tracks'] = bool(out['max_abs_err'] < RULE['L4_mixture_tol'])
    return out


# ───────────────────────────── main ─────────────────────────────
def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'correction': "navigator's leg 1 assumed shared items; off0 and off400 have 0 of 120 "
                         "values in common (R10_exhaustive/run.py:113). Replaced by disjoint-"
                         "item-set rule testing on the head x head residual correlation matrix."}

    print('  GATE L3 — REPLICATE POSITIVE CONTROL (injected per-head private-profile reliability)')
    rc = replicate_control(rng)
    for k in ('rel_0.0', 'rel_0.3', 'rel_0.6', 'rel_0.9'):
        print(f'    injected {k[4:]:<5} -> replicate statistic {rc[k]:+.4f}')
    print(f"    monotone in injected reliability: {rc['monotone']}")
    out['L3_replicate_control'] = rc

    print('\n  GATE L4 — WC MIXTURE CALIBRATION (ratio must track 1 - true observable share)')
    zb = np.load(REPO / 'R29_cancellation' / 'results' /
                 'r29_vectors_qwen2.5-1.5b_I_final_off0.npz')['base'].astype(np.float64)
    mc = mixture_control(zb, rng)
    for s in (0.0, 0.25, 0.5, 0.75, 1.0):
        v = mc[f'share_{s}']
        print(f"    true share {s:<5} -> ratio {v['ratio']:.4f}   expected {v['expected_1_minus_share']:.2f}"
              f"   err {v['abs_err']:.4f}")
    print(f"    max abs err {mc['max_abs_err']:.4f}  tracks: {mc['tracks']}")
    out['L4_mixture_control'] = mc

    # ---- load the two 1.5b cells; they are the only disjoint-item-set replicate on disk ----
    cells = {}
    for tag in ('off0', 'off400'):
        z = np.load(REPO / 'R29_cancellation' / 'results' /
                    f'r29_vectors_qwen2.5-1.5b_I_final_{tag}.npz')
        cells[tag] = (z['delta'].astype(np.float64), z['layer'], z['head'])

    print('\n  L1 — DISJOINT-ITEM-SET RULE REPLICATE (head x head residual correlation)')
    Cs, lay = {}, cells['off0'][1]
    for tag, (D, _, _) in cells.items():
        Cs[tag] = rowcorr(strip_rank1(two_way_resid(D)))
    obs = float(np.corrcoef(offdiag(Cs['off0']), offdiag(Cs['off400']))[0, 1])
    nulls = []
    for _ in range(N_NULL):
        p = within_layer_perm(lay, rng)
        nulls.append(float(np.corrcoef(offdiag(Cs['off0']), offdiag(Cs['off400'][np.ix_(p, p)]))[0, 1]))
    nulls = np.array(nulls)
    perhead = [float(np.corrcoef(np.delete(Cs['off0'][h], h),
                                 np.delete(Cs['off400'][h], h))[0, 1]) for h in range(len(lay))]
    L1 = {'replicate_statistic': obs, 'null_median': float(np.median(nulls)),
          'null_p95': float(np.percentile(nulls, 95)), 'null_sd': float(np.std(nulls, ddof=1)),
          'z': float((obs - np.median(nulls)) / np.std(nulls, ddof=1)),
          'inside_null_p95': bool(obs <= np.percentile(nulls, 95)),
          'per_head_median': float(np.median(perhead)),
          'per_head_iqr': [float(np.percentile(perhead, 25)), float(np.percentile(perhead, 75))]}
    L1['wb_dead'] = bool(obs < RULE['L1_wb_dead_if_replicate_below'] or L1['inside_null_p95'])
    print(f"    replicate statistic {obs:+.4f}   null median {L1['null_median']:+.4f}  "
          f"p95 {L1['null_p95']:+.4f}  z {L1['z']:+.1f}")
    print(f"    per-head median {L1['per_head_median']:+.4f}  IQR {L1['per_head_iqr'][0]:+.4f} "
          f"to {L1['per_head_iqr'][1]:+.4f}")
    out['L1_replicate'] = L1

    print('\n  L2 — RANK SWEEP, held-out median-head R2 minus its own per-k null floor')
    L2 = {}
    for tag, (D, _, hd) in cells.items():
        E = two_way_resid(D)
        n = D.shape[0]
        j = rng.permutation(n)
        ra, rb = j[:n // 2], j[n // 2:]
        row = {}
        for k in (1, 2, 3, 4, 5):
            _, med, per, nrm = crossfit_k(E, ra, rb, k)
            fl = [crossfit_k(two_way_resid(null_A(D, rng)), ra, rb, k)[1] for _ in range(30)]
            row[f'k{k}'] = {'r2_median_head': med, 'floor': float(np.mean(fl)),
                            'excess': med - float(np.mean(fl))}
            if k == 1:
                row['corr_norm_vs_r2'] = float(np.corrcoef(nrm, per)[0, 1])
        rr = row['k5']['excess'] / row['k1']['excess'] if row['k1']['excess'] > 0 else float('nan')
        row['rank5_over_rank1_excess'] = rr
        L2[tag] = row
        print(f'    {tag}')
        for k in (1, 2, 3, 4, 5):
            v = row[f'k{k}']
            print(f"      k={k}  median-head R2 {v['r2_median_head']:+.4f}  floor {v['floor']:+.4f}"
                  f"  excess {v['excess']:+.4f}")
        print(f"      excess(5)/excess(1) = {rr:.3f}      "
              f"corr(||B_j||, R2_j) at k=1 = {row['corr_norm_vs_r2']:+.4f}")
    out['L2_rank_sweep'] = L2

    # ---- read the registered rules ----
    if not rc['monotone']:
        verdict = 'UNVERIFIED_REPLICATE_CONTROL_FAILED'
    else:
        wb = 'WB_DEAD' if L1['wb_dead'] else 'WB_LIVES'
        rrs = [L2[t]['rank5_over_rank1_excess'] for t in L2]
        wa = ('WA_DEAD_COMPRESSION' if all(x >= RULE['L2_wa_dead_if_rank_ratio_atleast'] for x in rrs)
              else 'ONE_DIRECTION_CARRIES_IT'
              if all(x <= RULE['L2_one_direction_if_rank_ratio_atmost'] for x in rrs)
              else 'UNVERIFIED_PARTIAL')
        verdict = f'{wb} | {wa}'
    out['verdict'] = verdict
    out['L4_clears_wc_threshold'] = bool(mc['tracks'])
    print(f"\n  VERDICT  {verdict}")
    print(f"  L4 gate: WC_DEAD and POSITION_DEAD "
          f"{'ARE NOW CALIBRATED' if mc['tracks'] else 'REMAIN UNVERIFIED AT THE THRESHOLD'}")

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r30_private_selectivity.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
