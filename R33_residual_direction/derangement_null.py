#!/usr/bin/env python3
"""R33's gate, rerun with a null that IS THE DATA. No parametric family anywhere. Zero forwards.

R33 could not certify mean(c) = +0.7131 because its null was a 5-parameter surrogate that could
match neither the data's frac0 nor carry detectable structure at the noise that matching forced.
Every attempt to fix that by adding parameters is the same mistake with more knobs: matching frac0
ALONE was never going to identify a surrogate, because frac0 is a ratio of sums that spans
[0.0324, 0.8763] across the 56 groups and describes no single group.

THE DERANGEMENT NULL ENDS THE FAMILY PROBLEM PERMANENTLY.

    fit Omega on the fit half with the TRUE pairing
    R = P4 . Omega
    then DERANGE head labels WITHIN EACH HELD-OUT GROUP, in the off400 side only, AFTER the fit

  preserves  both loading spectra · every head's norm · all 56 within-group Gram matrices ·
             both sum-zero constraints · frac0 exactly · the depth gradient · everything
  destroys   cross-item-set head correspondence, and nothing else

A derangement, not a permutation: no head may keep its own label, so the null contains zero true
pairs by construction rather than 1/6 of them in expectation.

═══ WHY THE OLD NULL'S BASELINE WAS WRONG, NOT JUST ITS FAMILY ═══
Inside a group of m, sum_h P_h = 0 exactly, so two distinct rows have expected cosine -1/(m-1) =
-0.2. A null that returns 0.000 is therefore mis-stating its own baseline by ~0.12 -- in the
conservative direction, which is why nothing was wrongly certified, but it was still wrong.

═══ REGISTERED BEFORE THE RUN ═══
  T   IF mean(c_hold) < the derangement null's 99.9th percentile
      ->  DIRECTIONAL_PRIVACY_DEAD, and the identification line closes on a measured negative.
  No positive control is needed or used: the null is the data, so there is no family to have power
  against. The only remaining instrument question is whether the derangement destroys what it
  claims to, and it does so by construction -- it changes exactly one thing.
  1000 draws, split swept, held-out groups only.
  ALSO RERUN HERE: M4', whose p99.9 of 0.2752 came from the refuted family and is UNVERIFIED.
  SCOPE: n = 1 MODEL. No 3b off400 exists, so no second-model replicate of THIS statistic.
"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
RANK = 5
N_SPLIT = 200
N_NULL = 1000
RULE = {'n_splits': N_SPLIT, 'n_null_draws': N_NULL, 'percentile': 99.9, 'rank': RANK,
        'sumzero_pair_cosine_baseline': -1 / 5}


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
    return P


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


def derange(k, rng):
    """A permutation with no fixed point. Rejection sampling; k>=2 always terminates fast."""
    while True:
        p = rng.permutation(k)
        if not np.any(p == np.arange(k)):
            return p


def cosines(A0, A4, blk, rng, deranged=False):
    P0, P4 = privatise(A0, blk), privatise(A4, blk)
    fit, hold = block_split(blk, rng)
    R = P4 @ procrustes(P0[fit], P4[fit])          # Omega ALWAYS from the true pairing
    if deranged:                                    # ...and the labels move only afterwards
        R = R.copy()
        for g in np.unique(blk[hold]):
            m = np.where(blk == g)[0]
            R[m] = R[m][derange(len(m), rng)]
    N0 = unit(P0)
    c = np.zeros(len(blk))
    for g in np.unique(blk):
        m = np.where(blk == g)[0]
        _, _, Vt = np.linalg.svd(N0[m], full_matrices=False)
        u = Vt[0]
        r = unit(P0[m] - np.outer(P0[m] @ u, u))
        q = unit(R[m] - np.outer(R[m] @ u, u))
        c[m] = (r * q).sum(1)
    return c[hold]


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'null': 'derangement of head labels within held-out groups, off400 side, AFTER the '
                   'Procrustes fit; preserves both spectra, all norms, every within-group Gram, '
                   'both sum-zero constraints and frac0 exactly',
           'scope': 'n = 1 MODEL; no 3b off400 exists'}
    za = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off0.npz')
    zb = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off400.npz')
    D0, D4 = za['delta'].astype(np.float64), zb['delta'].astype(np.float64)
    lay, hd = za['layer'].astype(np.int64), za['head'].astype(np.int64)
    gblk = lay * 2 + hd // 6
    A0, A4 = loadings(D0), loadings(D4)
    print(f"  sanity: |sum over heads of A0| = {np.abs(A0.sum(0)).max():.3e}  "
          f"(two_way_resid forces it; the sum-zero pair baseline is {-1 / 5:.4f}, not 0)")

    obs = np.array([float(cosines(A0, A4, gblk, rng).mean()) for _ in range(N_SPLIT)])
    print(f"\n  OBSERVED  {N_SPLIT} splits: mean(c) {obs.mean():+.4f}  split sd "
          f"{obs.std(ddof=1):.4f}  [{obs.min():+.4f}, {obs.max():+.4f}]")

    nulls = np.array([float(cosines(A0, A4, gblk, rng, deranged=True).mean())
                      for _ in range(N_NULL)])
    q = float(np.percentile(nulls, RULE['percentile']))
    sep = (obs.mean() - nulls.mean()) / nulls.std(ddof=1)
    print(f"  DERANGEMENT NULL  {N_NULL} draws: mean {nulls.mean():+.4f}  sd "
          f"{nulls.std(ddof=1):.4f}  p99 {np.percentile(nulls, 99):+.4f}  p99.9 {q:+.4f}  "
          f"max {nulls.max():+.4f}")
    print(f"  separation {sep:.1f} null sd")
    out['observed'] = {'mean_c': float(obs.mean()), 'split_sd': float(obs.std(ddof=1)),
                       'min': float(obs.min()), 'max': float(obs.max()), 'n_splits': N_SPLIT}
    out['derangement_null'] = {'mean': float(nulls.mean()), 'sd': float(nulls.std(ddof=1)),
                               'p99': float(np.percentile(nulls, 99)), 'p999': q,
                               'max': float(nulls.max()), 'n_draws': N_NULL}
    out['separation_null_sd'] = float(sep)

    # ── M4' rerun under the same null ──
    print('\n  M4prime rerun — layer-conditional, derangement null replacing the refuted family')
    def layer_cond(rng_, deranged=False):
        P0, P4 = privatise(A0, lay), privatise(A4, lay)
        fit, hold = block_split(lay, rng_)
        R = P4 @ procrustes(P0[fit], P4[fit])
        if deranged:
            R = R.copy()
            for g in np.unique(lay[hold]):
                m = np.where(lay == g)[0]
                R[m] = R[m][derange(len(m), rng_)]
        Pn, Rn = unit(P0), unit(R)
        hg = hh = ng = 0
        for h in hold:
            cand = np.where(lay == lay[h])[0]
            pick = cand[int(np.argmax(Rn[cand] @ Pn[h]))]
            same = (hd[pick] // 6) == (hd[h] // 6)
            hg += int(same)
            if same:
                ng += 1
                hh += int(pick == h)
        return hg / len(hold), (hh / ng if ng else float('nan')), ng
    og, oc, on = layer_cond(np.random.default_rng(SEED))
    ln = [layer_cond(rng, deranged=True)[1] for _ in range(300)]
    ln = np.array([x for x in ln if x == x])
    lq = float(np.percentile(ln, RULE['percentile']))
    print(f"    observed  P(group) {og:.4f}  P(head|group) {oc:.4f}  n={on}")
    print(f"    derangement null on the conditional: mean {ln.mean():.4f}  p99.9 {lq:.4f}  "
          f"over {len(ln)} draws  ->  clears: {oc > lq}")
    out['M4prime_rerun'] = {'p_correct_group': og, 'p_correct_head_given_group': oc, 'n': on,
                            'null_mean': float(ln.mean()), 'null_p999': lq,
                            'clears': bool(oc > lq),
                            'caveat': 'conditional is selected on success and is upward biased'}

    verdict = 'DIRECTIONAL_PRIVACY_DEAD' if obs.mean() < q else 'DIRECTIONAL_PRIVACY_BEYOND_SCALE'
    out['verdict'] = verdict
    print(f"\n  REGISTERED T: mean(c) {obs.mean():+.4f} vs null p99.9 {q:+.4f}  ->  {verdict}")
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r33_derangement_null.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
