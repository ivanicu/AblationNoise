#!/usr/bin/env python3
"""Is head identity CONFINED to the shared subspace, or does it live outside it? Zero forwards.

R32's forced choice used loadings from ranks 1..5 -- the top of the two-way residual, which is where
the shared field lives (top-5 hold ~91% of the residual's energy). So top1 = 0.9107 could mean a head
is identifiable by its coordinates WITHIN the shared field, which is a weaker claim than head identity
being a property of the head at all scales.

This file runs the identical forced choice on DISJOINT RANK WINDOWS:

    [1,6)   the shared field itself, what R32 used
    [6,11)  immediately below it
    [11,21) well outside any rank the shared-field story reaches
    [21,41) the tail

If identity is confined to the shared field, it must collapse toward chance in the high windows. If it
survives out there, the head owns a private mixing vector at every scale, not merely a coordinate in
one global field.

═══ THE CONTROL REGISTRATION IS DIFFERENT HERE, AND THAT IS THE POINT ═══
Three gates failed today and ALL THREE failed the same way: I registered a threshold against an
ANALYTIC expectation of the null -- monotone from rel=0, inside a p95, chance = 1/6 -- instead of
against the null's MEASURED distribution. R32's C1 landed at 0.0893 against a band of [0.11, 0.23]
because privatise() forces each group's six P-vectors to sum to zero, so under pure noise the true
pairing is DISFAVOURED and never sits at 1/6.

So this file does not assume where its null sits. It MEASURES it, per window, and registers against
its own percentile:

    for each rank window, run the no-private-rule surrogate N_CTRL times
    threshold = the 95th percentile of that surrogate's own top1 distribution
    the observed must clear ITS OWN window's threshold, not a number I guessed

═══ REGISTERED BEFORE THE RUN ═══
  W1  observed top1 in window [11,21) must exceed that window's surrogate p95
      -> identity EXTENDS beyond the shared subspace
  W2  if it does not, identity is CONFINED to the top-10 subspace, and the claim narrows to
      "a head is identifiable by its coordinates in one global field", not "a head owns a private
      mixing vector"
  GATE: the strong-private surrogate (rel=0.9) must clear its own window's p95 in window [1,6),
        or the instrument has no power there and every window is UNVERIFIED.
  No threshold is amended after any number is seen. Scope is unchanged: n = 1 MODEL, no 3b replicate.

⚠⚠ ANNOTATED IMMEDIATELY AFTER THE RUN. Two defects the navigator found, both of which this file
inherits from R32 and neither of which its measured-null repair addresses.

  DEFECT A — THE SURROGATE IS NOT IN THE DATA'S REGIME, WHICH IS DEEPER THAN THE BAND.
  Measured: variance_fraction_removed_by_block_mean is 0.9862 for the no-private surrogate and
  0.1468 for the observed data. So the surrogate's group structure eats 98.6% of the loading energy
  and the statistic is computed on the 1.4% left over, while the observed statistic runs on 85.3%
  surviving energy. The surrogate never tested "no private rule" -- it tested "no private rule AND
  group-dominance 6.7x higher than reality". Measuring its distribution instead of guessing a band
  fixes the WRONG HALF of the problem: the distribution is correct for a null that is not the data's.
  The repair is to MATCH the surrogate on frac0 = 0.147 +- 0.02 BEFORE drawing, then take quantiles.

  DEFECT B — split='head' IS OPTIMISTICALLY BIASED BY CONSTRUCTION.
  The fit set contains heads that are CANDIDATES for held-out heads. privatise() forces sum_m P = 0
  within a group, so cos(P0_h, P0_m) ~ -1/5 for m != h; aligning a fit candidate's R_m to its own
  P0_m pushes that candidate's similarity to the true head negative AND pushes R_h = -sum_{m!=h} R_m
  toward P0_h. Both act the same way. That is exactly the 0.9107 vs 0.8631 gap R32 measured between
  the head split and the whole-group split. EVERY NUMBER IN THIS FILE USES split='head' AND IS
  THEREFORE INFLATED BY ROUGHLY THAT MARGIN.

WHAT SURVIVES BOTH DEFECTS, because it is a statement about R32's control and not about this file's
observed values: the [1,6) control MINIMUM over 30 draws is 0.0893, which is EXACTLY the single value
R32's C1 returned, against a median of 0.1756 and a range of [0.0893, 0.2321]. So R32's C1 drew the
minimum of thirty. My commit body for R32 diagnosed that 0.0893 as sum-zero geometry disfavouring the
true pairing; the measured distribution sits AT chance, so that mechanism story is refuted. It was one
unlucky draw -- the single-draw defect for the fourth time today, this time inside a control.
"""
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
N_CTRL = 30
WINDOWS = ((1, 6), (6, 11), (11, 21), (21, 41))
RULE = {'n_control_draws': N_CTRL, 'percentile': 95, 'windows': [list(w) for w in WINDOWS],
        'W1_window': [11, 21], 'chance_group': 1 / 6}


def two_way_resid(D):
    mu = D.mean()
    return D - mu - (D.mean(1) - mu)[:, None] - (D.mean(0) - mu)[None, :]


def loadings_window(D, lo, hi):
    """U.S over a RANK WINDOW [lo,hi) of the two-way residual. lo=1 skips the leading direction."""
    U, S, _ = np.linalg.svd(two_way_resid(D), full_matrices=False)
    return U[:, lo:hi] * S[lo:hi]


def privatise(A, blk):
    P = A.copy()
    for g in np.unique(blk):
        m = blk == g
        P[m] -= A[m].mean(0)
    return P


def procrustes(X, Y):
    U, _, Vt = np.linalg.svd(Y.T @ X)
    return U @ Vt


def forced_choice(A0, A4, blk, rng):
    P0, P4 = privatise(A0, blk), privatise(A4, blk)
    n = A0.shape[0]
    idx = rng.permutation(n)
    fit, hold = idx[:n // 2], idx[n // 2:]
    R = P4 @ procrustes(P0[fit], P4[fit])
    Pn = P0 / (np.linalg.norm(P0, axis=1, keepdims=True) + 1e-300)
    Rn = R / (np.linalg.norm(R, axis=1, keepdims=True) + 1e-300)
    hits = 0
    for h in hold:
        cand = np.where(blk == blk[h])[0]
        hits += int(cand[int(np.argmax(Rn[cand] @ Pn[h]))] == h)
    return hits / len(hold)


def synth(rng, nh=336, ni=120, per_group=6, shared_rank=5, priv_rank=3, rel=0.9,
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
           'scope': 'n = 1 MODEL; no 3b off400 on disk so no second disjoint-item-set replicate'}
    blk_s = np.repeat(np.arange(56), 6)
    za = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off0.npz')
    zb = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off400.npz')
    D0, D4 = za['delta'].astype(np.float64), zb['delta'].astype(np.float64)
    lay, hd = za['layer'].astype(np.int64), za['head'].astype(np.int64)
    blk = lay * 2 + hd // 6

    print(f'  {N_CTRL} no-private-rule surrogate draws per window; threshold = that window\'s own p95')
    print(f"    {'window':<12}{'observed':<12}{'ctrl p95':<12}{'ctrl med':<12}{'strong p95':<13}"
          f"{'clears':<9}lift")
    res = {}
    for lo, hi in WINDOWS:
        obs = forced_choice(loadings_window(D0, lo, hi), loadings_window(D4, lo, hi), blk,
                            np.random.default_rng(SEED))
        ctrl, strong = [], []
        for _ in range(N_CTRL):
            Xa, Xb = synth(rng, priv_amp=0.0)
            ctrl.append(forced_choice(loadings_window(Xa, lo, hi), loadings_window(Xb, lo, hi),
                                      blk_s, np.random.default_rng(SEED)))
            Ya, Yb = synth(rng, priv_amp=1.0, rel=0.9)
            strong.append(forced_choice(loadings_window(Ya, lo, hi), loadings_window(Yb, lo, hi),
                                        blk_s, np.random.default_rng(SEED)))
        p95 = float(np.percentile(ctrl, 95))
        sp95 = float(np.percentile(strong, 95))
        r = {'observed_top1': obs, 'control_p95': p95, 'control_median': float(np.median(ctrl)),
             'control_min': float(min(ctrl)), 'control_max': float(max(ctrl)),
             'strong_private_median': float(np.median(strong)), 'strong_private_p95': sp95,
             'clears_own_p95': bool(obs > p95),
             'lift_over_control_median': obs / max(np.median(ctrl), 1e-9),
             'instrument_has_power': bool(np.median(strong) > p95)}
        res[f'{lo}_{hi}'] = r
        print(f"    [{lo},{hi})".ljust(16) + f"{obs:<12.4f}{p95:<12.4f}{r['control_median']:<12.4f}"
              f"{sp95:<13.4f}{str(r['clears_own_p95']):<9}{r['lift_over_control_median']:.2f}x")
    out['windows'] = res

    gate = res['1_6']['instrument_has_power']
    out['gate_passed'] = bool(gate)
    w1 = res['11_21']
    verdict = ('UNVERIFIED_NO_POWER' if not gate
               else 'IDENTITY_EXTENDS_BEYOND_SHARED_SUBSPACE' if w1['clears_own_p95']
               else 'IDENTITY_CONFINED_TO_TOP10')
    out['verdict'] = verdict
    print(f"\n  GATE: strong-private median clears its own p95 in [1,6) -> {gate}")
    print(f"  W1: window [11,21) observed {w1['observed_top1']:.4f} vs its own control p95 "
          f"{w1['control_p95']:.4f}  ->  {verdict}")

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r32_rank_window.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
