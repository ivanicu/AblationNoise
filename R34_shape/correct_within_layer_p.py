#!/usr/bin/env python3
"""R34's within-layer control had the wrong null. Reproduced, corrected, and its POWER measured.

The navigator found the defect; the numbers below are re-measured here, because a navigator's
judgement binds and its facts do not.

THE DEFECT. duplication_and_magnitude.py built its within-layer control by ranking both variables
inside each layer and then permuting the ranks GLOBALLY across all 56 / 72 groups. But there are
exactly 2 KV groups per layer in BOTH models -- 28 layers x 2 = 56, 36 x 2 = 72 -- so:

  * ranking inside a layer of 2 yields exactly +-0.5, and rho_w is ALGEBRAICALLY A PAIRED SIGN TEST:
    rho_w = (concordant - discordant) / n_layers
  * a GLOBAL permutation destroys the one-per-layer balance the statistic depends on, so it is not
    the null of that statistic at all

THE CORRECT NULL flips the sign WITHIN each layer, which is exact and needs no permutation: under
the null each layer is concordant with probability 1/2, independently, so the count is Binomial.

═══ WHAT THIS FILE ESTABLISHES, AND WHAT IT DOES NOT ═══
It does NOT reopen R34's registered verdict. DUPLICATION_DEAD was read off the RAW Spearman
(-0.1801, p 0.185 in 1.5b), which the control never touched. The correction runs TOWARD
significance -- the reported p was too SMALL -- so the control looked more alive than it was and the
collapse reading is strengthened, not weakened.

It DOES establish the control's POWER, which was never stated and which decides what the control is
allowed to say. A sign test on 28 pairs cannot reach p <= 0.05 unless |rho_w| is large; below that
the control is silent, and silence is UNVERIFIED on the unsound side of the proxy ledger, never an
acquittal.

Also asserts groups-per-layer == 2, so that if the cell set ever changes this file fails loudly
instead of computing a sign test on something that is not a sign test.
"""
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
RANK = 5


def two_way_resid(D):
    mu = D.mean()
    return D - mu - (D.mean(1) - mu)[:, None] - (D.mean(0) - mu)[None, :]


def loadings(D, rank=RANK):
    E = two_way_resid(D)
    U, S, Vt = np.linalg.svd(E, full_matrices=False)
    E1 = E - S[0] * np.outer(U[:, 0], Vt[0])
    U2, S2, _ = np.linalg.svd(E1, full_matrices=False)
    return U2[:, :rank] * S2[:rank]


def binom_two_sided(k, n, p=0.5):
    """Exact two-sided p by the method of small likelihoods."""
    def pmf(i):
        return math.comb(n, i) * p ** i * (1 - p) ** (n - i)
    t = pmf(k) * (1 + 1e-9)
    return float(sum(pmf(i) for i in range(n + 1) if pmf(i) <= t))


def min_abs_rho_for_alpha(n, alpha=0.05):
    """Smallest |concordant - discordant|/n whose exact two-sided p is <= alpha."""
    for d in range(n + 1):
        k = (n + d) / 2
        if k != int(k):
            continue
        if binom_two_sided(int(k), n) <= alpha:
            return d / n
    return float('nan')


def main():
    out = {'defect': 'R34 permuted the within-layer ranks GLOBALLY, destroying the one-per-layer '
                     'balance; with 2 KV groups per layer the statistic is a paired SIGN TEST and '
                     'its exact null is Binomial(n_layers, 1/2)',
           'scope': 'does NOT reopen DUPLICATION_DEAD, which was read off the RAW Spearman'}
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
        fg, mg, gl = np.zeros(len(gs)), np.zeros(len(gs)), np.zeros(len(gs), dtype=int)
        for k, g in enumerate(gs):
            m = gid == g
            P = A[m] - A[m].mean(0)
            fg[k] = 1 - (P ** 2).sum() / (A[m] ** 2).sum()
            mg[k] = np.median(nrm[m])
            gl[k] = lay[m][0]
        # THE ASSERT the navigator asked for: this statistic IS a sign test only if it is 2 per layer
        counts = np.array([(gl == L).sum() for L in np.unique(gl)])
        assert (counts == 2).all(), f'{tag}: groups-per-layer is not 2 everywhere: {set(counts)}'
        conc = disc = 0
        for L in np.unique(gl):
            i = np.where(gl == L)[0]
            a, b = i[0], i[1]
            s1, s2 = fg[a] - fg[b], mg[a] - mg[b]
            if s1 == 0 or s2 == 0:
                continue
            if (s1 > 0) == (s2 > 0):
                conc += 1
            else:
                disc += 1
        n = conc + disc
        rho_w = (conc - disc) / n
        p = binom_two_sided(conc, n)
        floor = min_abs_rho_for_alpha(n)
        r = {'n_layers_used': n, 'concordant': conc, 'discordant': disc, 'rho_w': rho_w,
             'p_exact_binomial_two_sided': p,
             'min_abs_rho_w_detectable_at_0p05': floor,
             'control_is_silent_below': floor}
        res[tag] = r
        print(f'\n  {tag}   {len(gs)} groups, {len(counts)} layers, exactly '
              f'{set(counts.tolist())} groups per layer (asserted)')
        print(f"    concordant {conc} / discordant {disc} over {n} layers   rho_w {rho_w:+.4f}")
        print(f"    EXACT two-sided binomial p {p:.4f}")
        print(f"    power floor: |rho_w| must reach {floor:.4f} for p <= 0.05 on {n} pairs")
        print(f"    -> the control cannot exclude within-layer duplication below |rho_w| = "
              f"{floor:.4f}; UNVERIFIED there, not an acquittal")
    out['cells'] = res

    # annotate the R34 result rather than rewriting it (L81)
    rp = HERE / 'results' / 'r34_duplication_and_magnitude.json'
    if rp.exists():
        d = json.load(open(rp))
        d['ANNOTATION_2026_07_30_within_layer_p_corrected'] = {
            'why': out['defect'],
            'superseded_p_values': {k: v.get('p_perm_within_layer') for k, v in d['cells'].items()},
            'corrected_exact_binomial_p': {k: res[k]['p_exact_binomial_two_sided']
                                           for k in res if k in d['cells']},
            'power_floor_abs_rho_w': {k: res[k]['min_abs_rho_w_detectable_at_0p05']
                                      for k in res if k in d['cells']},
            'verdict_unchanged': 'DUPLICATION_DEAD was read off the RAW Spearman; the correction '
                                 'runs toward significance so the collapse reading is strengthened',
            'generator': 'R34_shape/correct_within_layer_p.py'}
        json.dump(d, open(rp, 'w'), indent=1)
        print(f'\n  annotated {rp} (body preserved, correction added as a new key)')

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r34_within_layer_p_correction.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
