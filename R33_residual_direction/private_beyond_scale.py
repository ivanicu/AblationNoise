#!/usr/bin/env python3
"""THE TERMINAL MEASUREMENT of the identification line. Magnitude-free by construction. Zero forwards.

The navigator's ruling: this framing closes after this file, whatever it returns. Three consecutive
rounds produced 0.9107 RETRACTED, WB_LIVES WITHDRAWN, and DOWNGRADED_TO_PER_HEAD_SCALE; top1 is
unitless and has drifted off the anchor, which is the SHAPE of the ablation-effect distribution.
This measurement is justified only because it is magnitude-free, costs no forward pass, and settles
the one thing the downgrade left open.

═══ THE QUESTION, AND WHY IT IS IDENTIFIABLE ═══
"Heads have stable magnitudes and the rest is shared" says P_h ~ c_h * s_g + eps_h with c_h stable
across item sets. Under that world the ROW-NORMALISED within-group rows collapse onto +-s_g, so after
projecting out the group's leading normalised axis the remainder is pure noise and its cross-item-set
cosine has mean 0. Under private DIRECTIONAL rules the remainder replicates. Scale cannot enter: the
rank-1 scale component is exactly what is removed, and both sides are unit-normalised after removal.

  u_g   top principal direction of the 6 x 5 matrix of ROW-NORMALISED P0 rows of group g,
        computed from off0 ONLY (leakage of head h into u_g removes signal, never creates it)
  r_h   normalise( (I - u_g u_g^T) P0_h )
  q_h   normalise( (I - u_g u_g^T) R_h )     R = P4 . Omega, Omega from the FIT HALF only
  c_h   r_h . q_h                             held-out heads only

═══ THE DEFECT THIS FILE FIXES, FOUND ON THE SIXTH OCCURRENCE ═══
Every number in R32 sits on ONE split: block_split was called with default_rng(SEED) for the observed
value AND for all 1000 null draws, so the null's spread is over surrogate draws only and split
variance appears in no error bar anywhere. Here the split is SWEPT, 200 draws on the observed and a
fresh split inside every null draw.

═══ REGISTERED BEFORE THE RUN ═══
  T   IF mean(c_hold) < the matched null's 99.9th percentile
      ->  "heads have private DIRECTIONAL rules beyond per-head scale" is DEAD, the privacy line
          closes, and only the ||E_h||_2 distribution is carried forward.
  GATE  the positive control (priv_amp = 1.0) must return mean(c) >= 2 x the null mean, or the
        instrument is UNVERIFIED and no null is admissible.
  Null: the M1 matched surrogate, priv_amp = 0 at the noise that matches the data's frac0, 1000
  draws, fresh split each draw.

═══ REPORTED, NOT GATED — the four controls the navigator says are owed ═══
  M2'   nearest-||E_h|| scalar baseline on M4's CONDITIONAL subproblem, the same heads, stated
        beside 0.8693 which currently has no baseline at all
  M3'   random-position cross-group candidates. R32's M3 used SAME-position cross-group candidates
        and fired at 0.9286 against a 0.40 threshold, but that threshold was calibrated for the
        within-group task. If |M3 - M3'| < 0.05 the contamination flag is withdrawn as UNVERIFIED:
        the number measured task difficulty, not position.
  M4'   a matched-surrogate null for the LAYER-conditional task, replacing R32's comparison of
        0.8693 against a 6-way group-mate null -- a cross-task threshold transfer, and a
        proxy-ledger violation as it stands.
  A/B   Route A (sum-zero converts a magnitude disparity into a directional signature; predicts hits
        concentrated on the group's DOMINANT head) versus Route B (norm gates measurability; predicts
        accuracy MONOTONE in norm rank). They predict opposite things and are separable on disk.

═══ SCOPE, UNCHANGED AND NOT NEGOTIABLE ═══
No 3b off400 exists, so there is no second-model replicate. n = 1 MODEL. Nothing here is a property
of Qwen2.5 or of GQA.
"""
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
RANK = 5
N_SPLIT = 200
N_NULL = 1000
RULE = {'n_splits': N_SPLIT, 'n_null_draws': N_NULL, 'percentile': 99.9,
        'gate_poscontrol_over_null_mean': 2.0, 'target_frac0': 0.1468, 'frac0_tol': 0.02,
        'M3_withdraw_flag_if_absdiff_below': 0.05, 'M3_observed': 0.9286, 'rank': RANK}


def two_way_resid(D):
    mu = D.mean()
    return D - mu - (D.mean(1) - mu)[:, None] - (D.mean(0) - mu)[None, :]


def loadings(D, rank=RANK):
    E = two_way_resid(D)
    U, S, Vt = np.linalg.svd(E, full_matrices=False)
    E1 = E - S[0] * np.outer(U[:, 0], Vt[0])
    U2, S2, _ = np.linalg.svd(E1, full_matrices=False)
    return U2[:, :rank] * S2[:rank]


def privatise(A, blk):
    P = A.copy()
    for g in np.unique(blk):
        m = blk == g
        P[m] -= A[m].mean(0)
    return P, float(1 - (P ** 2).sum() / (A ** 2).sum())


def unit(X):
    return X / (np.linalg.norm(X, axis=-1, keepdims=True) + 1e-300)


def procrustes(X, Y):
    U, _, Vt = np.linalg.svd(Y.T @ X)
    return U @ Vt


def block_split(blk, rng):
    gs = np.unique(blk)
    gp = gs[rng.permutation(len(gs))]
    fg = set(gp[:len(gp) // 2].tolist())
    fit = np.array([i for i in range(len(blk)) if blk[i] in fg])
    hold = np.array([i for i in range(len(blk)) if blk[i] not in fg])
    return fit, hold


def residual_cosines(A0, A4, blk, rng):
    """The magnitude-free statistic. Returns c per held-out head, and the held-out indices."""
    P0, _ = privatise(A0, blk)
    P4, _ = privatise(A4, blk)
    fit, hold = block_split(blk, rng)
    R = P4 @ procrustes(P0[fit], P4[fit])
    N0 = unit(P0)
    c = np.zeros(len(blk))
    for g in np.unique(blk):
        m = np.where(blk == g)[0]
        _, _, Vt = np.linalg.svd(N0[m], full_matrices=False)
        u = Vt[0]
        r = unit(P0[m] - np.outer(P0[m] @ u, u))
        q = unit(R[m] - np.outer(R[m] @ u, u))
        c[m] = (r * q).sum(1)
    return c[hold], hold


def synth(rng, nh=336, per_group=6, ni=120, shared_rank=5, priv_rank=3, rel=0.9,
          priv_amp=1.0, noise=1.0):
    A_shared = np.repeat(rng.standard_normal((nh // per_group, shared_rank)), per_group, axis=0)
    Wp = rng.standard_normal((nh, priv_rank))
    out = []
    for _ in range(2):
        Wps = rel * Wp + math.sqrt(max(1 - rel ** 2, 0.0)) * rng.standard_normal((nh, priv_rank))
        out.append(A_shared @ rng.standard_normal((shared_rank, ni))
                   + priv_amp * (Wps @ rng.standard_normal((priv_rank, ni)))
                   + noise * rng.standard_normal((nh, ni)))
    return out


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'scope': 'n = 1 MODEL; no 3b off400 exists, so no second-model replicate'}
    za = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off0.npz')
    zb = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off400.npz')
    D0, D4 = za['delta'].astype(np.float64), zb['delta'].astype(np.float64)
    lay, hd = za['layer'].astype(np.int64), za['head'].astype(np.int64)
    gblk = lay * 2 + hd // 6
    A0, A4 = loadings(D0), loadings(D4)
    E0, E4 = two_way_resid(D0), two_way_resid(D4)
    n0, n4 = np.linalg.norm(E0, axis=1), np.linalg.norm(E4, axis=1)
    blk_s = np.repeat(np.arange(56), 6)

    # ── observed, split SWEPT ──
    print(f'  OBSERVED — {N_SPLIT} independent whole-group splits')
    means, allc, alllay = [], [], []
    for _ in range(N_SPLIT):
        c, hold = residual_cosines(A0, A4, gblk, rng)
        means.append(float(c.mean()))
        allc.append(c)
        alllay.append(lay[hold])
    means = np.array(means)
    cc, ll = np.concatenate(allc), np.concatenate(alllay)
    obs = float(means.mean())
    print(f"    mean(c) {obs:+.4f}   split-to-split sd {means.std(ddof=1):.4f}   "
          f"[{means.min():+.4f}, {means.max():+.4f}]")
    print(f"    per-head c: median {np.median(cc):+.4f}  q25 {np.percentile(cc, 25):+.4f}  "
          f"q75 {np.percentile(cc, 75):+.4f}  frac > 0: {float((cc > 0).mean()):.4f}")
    prof = {int(L): float(cc[ll == L].mean()) for L in sorted(set(ll.tolist()))}
    out['observed'] = {'mean_c': obs, 'split_sd': float(means.std(ddof=1)),
                       'split_min': float(means.min()), 'split_max': float(means.max()),
                       'per_head_median': float(np.median(cc)),
                       'per_head_q25': float(np.percentile(cc, 25)),
                       'per_head_q75': float(np.percentile(cc, 75)),
                       'frac_positive': float((cc > 0).mean()), 'per_layer_mean_c': prof}
    lo = [prof[k] for k in sorted(prof)[:7]]
    hi = [prof[k] for k in sorted(prof)[-7:]]
    print(f"    per-layer mean(c): first 7 layers {np.mean(lo):+.4f}   last 7 {np.mean(hi):+.4f}")

    # ── matched null, fresh split every draw ──
    print(f"\n  MATCHED NULL — surrogate frac0 tuned to the data's {RULE['target_frac0']:.4f}")
    best = None
    for nz in (8.0, 16.0, 32.0, 64.0):
        Xa, Xb = synth(rng, priv_amp=0.0, noise=nz)
        _, f = privatise(loadings(Xa), blk_s)
        if best is None or abs(f - RULE['target_frac0']) < abs(best[1] - RULE['target_frac0']):
            best = (nz, f)
    nz, fbest = best
    matched = abs(fbest - RULE['target_frac0']) <= RULE['frac0_tol']
    print(f'    chosen noise {nz}, frac0 {fbest:.4f}, matched {matched}')
    nulls = []
    for _ in range(N_NULL):
        Xa, Xb = synth(rng, priv_amp=0.0, noise=nz)
        c, _ = residual_cosines(loadings(Xa), loadings(Xb), blk_s, rng)
        nulls.append(float(c.mean()))
    nulls = np.array(nulls)
    q = float(np.percentile(nulls, RULE['percentile']))
    print(f"    null over {N_NULL} draws: mean {nulls.mean():+.4f}  sd {nulls.std(ddof=1):.4f}  "
          f"p99.9 {q:+.4f}  max {nulls.max():+.4f}")

    print('  GATE — positive control, priv_amp = 1.0, must reach 2x the null mean')
    pos = []
    for _ in range(60):
        Ya, Yb = synth(rng, priv_amp=1.0, rel=0.9, noise=nz)
        c, _ = residual_cosines(loadings(Ya), loadings(Yb), blk_s, rng)
        pos.append(float(c.mean()))
    pos = np.array(pos)
    need = RULE['gate_poscontrol_over_null_mean'] * abs(nulls.mean())
    gate = bool(pos.mean() >= max(need, q))
    print(f"    positive control mean(c) {pos.mean():+.4f}  vs 2x|null mean| {need:.4f} and "
          f"p99.9 {q:+.4f}  ->  {gate}")
    out['matched_null'] = {'noise': nz, 'frac0': fbest, 'matched': bool(matched),
                           'mean': float(nulls.mean()), 'sd': float(nulls.std(ddof=1)),
                           'p999': q, 'max': float(nulls.max()), 'n_draws': N_NULL}
    out['positive_control'] = {'mean_c': float(pos.mean()), 'sd': float(pos.std(ddof=1)),
                               'n': len(pos), 'passes': gate}

    verdict = ('UNVERIFIED_SURROGATE_UNMATCHED' if not matched
               else 'UNVERIFIED_NO_POWER' if not gate
               else 'DIRECTIONAL_PRIVACY_DEAD' if obs < q
               else 'DIRECTIONAL_PRIVACY_BEYOND_SCALE')
    out['verdict'] = verdict
    print(f"\n  REGISTERED T: mean(c) {obs:+.4f} vs null p99.9 {q:+.4f}  ->  {verdict}")

    # ══ companions, reported not gated ══
    print('\n  M4prime — layer-conditional task WITH its own matched null (R32 used a 6-way null)')
    def layer_cond(A0_, A4_, blk_l, hd_, rng_, scalar=None):
        P0, _ = privatise(A0_, blk_l)
        P4, _ = privatise(A4_, blk_l)
        fit, hold = block_split(blk_l, rng_)
        R = P4 @ procrustes(P0[fit], P4[fit])
        Pn, Rn = unit(P0), unit(R)
        hg = hh = ng = 0
        for h in hold:
            cand = np.where(blk_l == blk_l[h])[0]
            pick = (cand[int(np.argmax(Rn[cand] @ Pn[h]))] if scalar is None
                    else cand[int(np.argmin(np.abs(scalar[1][cand] - scalar[0][h])))])
            same = (hd_[pick] // 6) == (hd_[h] // 6)
            hg += int(same)
            if same:
                ng += 1
                hh += int(pick == h)
        return hg / len(hold), (hh / ng if ng else float('nan')), ng
    og, oc, on = layer_cond(A0, A4, lay, hd, np.random.default_rng(SEED))
    sg, sc, sn = layer_cond(A0, A4, lay, hd, np.random.default_rng(SEED), scalar=(n0, n4))
    lc_null = []
    hd_s = np.tile(np.arange(12), 28)
    lay_s = np.repeat(np.arange(28), 12)
    for _ in range(200):
        Xa, Xb = synth(rng, priv_amp=0.0, noise=nz)
        _, cnd, _ = layer_cond(loadings(Xa), loadings(Xb), lay_s, hd_s, rng)
        if cnd == cnd:
            lc_null.append(cnd)
    lcq = float(np.percentile(lc_null, RULE['percentile']))
    print(f"    cosine   P(group) {og:.4f}  P(head|group) {oc:.4f}  n={on}")
    print(f"    M2prime  scalar   P(group) {sg:.4f}  P(head|group) {sc:.4f}  n={sn}  "
          f"<- the baseline 0.8693 never had")
    print(f"    layer-conditional matched null p99.9 {lcq:.4f} over {len(lc_null)} draws  "
          f"-> cosine clears: {oc > lcq}")
    out['M4prime'] = {'cosine_p_group': og, 'cosine_p_head_given_group': oc, 'n_cos': on,
                      'scalar_p_group': sg, 'scalar_p_head_given_group': sc, 'n_scalar': sn,
                      'conditional_null_p999': lcq, 'cosine_clears': bool(oc > lcq),
                      'note': 'conditional is selected on success, so it is upward biased'}

    print('\n  M3prime — RANDOM-position cross-group candidates (R32 used SAME position)')
    P0g, _ = privatise(A0, gblk)
    P4g, _ = privatise(A4, gblk)
    fit, hold = block_split(gblk, np.random.default_rng(SEED))
    Rg = P4g @ procrustes(P0g[fit], P4g[fit])
    Pn, Rn = unit(P0g), unit(Rg)
    rng3 = np.random.default_rng(SEED + 11)
    hits = 0
    for h in hold:
        pool = np.where(gblk != gblk[h])[0]
        cand = np.concatenate([[h], rng3.choice(pool, 5, replace=False)])
        hits += int(cand[int(np.argmax(Rn[cand] @ Pn[h]))] == h)
    m3p = hits / len(hold)
    d = abs(RULE['M3_observed'] - m3p)
    print(f"    random-position cross-group top1 {m3p:.4f}   R32's same-position "
          f"{RULE['M3_observed']:.4f}   |diff| {d:.4f}")
    print(f"    -> contamination flag {'WITHDRAWN as UNVERIFIED' if d < RULE['M3_withdraw_flag_if_absdiff_below'] else 'STANDS'}")
    out['M3prime'] = {'random_position_top1': m3p, 'same_position_top1': RULE['M3_observed'],
                      'abs_diff': d, 'flag_withdrawn': bool(d < RULE['M3_withdraw_flag_if_absdiff_below'])}

    print('\n  ROUTE A vs B — A: hits on the group DOMINANT head. B: accuracy monotone in norm rank.')
    Pn2, Rn2 = unit(P0g), unit(Rg)
    nrm = np.linalg.norm(P0g, axis=1)
    rk, hit = [], []
    for h in hold:
        cand = np.where(gblk == gblk[h])[0]
        rk.append(int(np.where(np.argsort(-nrm[cand]) == np.where(cand == h)[0][0])[0][0]))
        hit.append(int(cand[int(np.argmax(Rn2[cand] @ Pn2[h]))] == h))
    rk, hit = np.array(rk), np.array(hit)
    by = {int(r): float(hit[rk == r].mean()) for r in sorted(set(rk.tolist()))}
    mono = float(np.corrcoef(rk, hit)[0, 1])
    print(f"    accuracy by within-group norm rank (0 = dominant): "
          + '  '.join(f'{r}:{v:.3f}' for r, v in sorted(by.items())))
    print(f"    corr(norm rank, hit) {mono:+.4f}   "
          f"{'B (monotone in norm)' if abs(mono) > 0.2 else 'neither cleanly'}")
    out['route_A_vs_B'] = {'accuracy_by_norm_rank': by, 'corr_rank_hit': mono}

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r33_private_beyond_scale.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
