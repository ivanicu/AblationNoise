#!/usr/bin/env python3
"""R20 analysis -- the registered rule, applied. Written before the run finished.

Thresholds come from R20_direct_indirect/PREREGISTRATION.md and are duplicated here as constants so
this file can be read without the markdown. Any disagreement between the two is a defect in this
file, not a re-specification: the markdown is committed and dated earlier.

THE LAYER-27 CONTROL IS READ FIRST AND GATES EVERYTHING. A head in the last layer has nothing
downstream, so its direct_renorm must equal R10's measured total. If that fails the decomposition is
wrong and no verdict is printed -- UNVERIFIED, which is not an acquittal.
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))

BAND_LO, BAND_HI = 14, 28
SMALL_DIRECT = 0.01              # registered
SUPPRESSION_REPAIR = 0.80        # registered
SUPPRESSION_AMPLIFY = 1.20       # registered
NODYN_LO, NODYN_HI = 0.90, 1.10  # registered
ALPHA = 0.05                     # registered
L27_CONTROL_FRAC = 0.05          # registered: max|direct_renorm-total| <= 0.05 * band sd of total
N_PERM = 20000                   # registered
SEED = 20260729                  # registered


def median(v):
    w = sorted(v)
    n = len(w)
    return w[n // 2] if n % 2 else 0.5 * (w[n // 2 - 1] + w[n // 2])


def sd(v):
    mu = sum(v) / len(v)
    return math.sqrt(sum((z - mu) ** 2 for z in v) / (len(v) - 1))


def binom_tail(k, n, p=0.5):
    """P(X >= k) for X ~ Bin(n, p). Two-sided by doubling, capped at 1."""
    c = 0.0
    for i in range(k, n + 1):
        c += math.comb(n, i) * p ** i * (1 - p) ** (n - i)
    return min(1.0, 2 * c)


def main():
    f = HERE / 'results' / 'r20_direct_indirect_qwen2.5-1.5b.json'
    if not f.exists():
        print(f'no result at {f} -- this analysis was written before the data existed')
        return 1
    d = json.load(open(f))
    if d.get('verdict') != 'MEASURED':
        print(f"  the run REFUSED: {d.get('verdict')} -- {d.get('why')}")
        return 3
    C = d['cells']
    NH = d['n_heads']
    NL = d['n_layers']
    band = [(L, h) for L in range(BAND_LO, min(BAND_HI, NL)) for h in range(NH)]
    key = lambda k: f'L{k[0]:02d}H{k[1]:02d}'

    print(f"R20  {d['model']}  n={d['n_items']} items  totals read from {d['total_source']}")

    # ---- control 2: the same items
    dm = abs(d['base_margin'] - d['r10_base_margin'])
    # 1e-6 ABSOLUTE ON A QUANTITY OF MAGNITUDE 4.48 IS 2.2e-7 RELATIVE -- BELOW FLOAT32 EPSILON.
    # The markdown registers this control as "must reproduce ... or the items are not the same
    # items" and fixes NO tolerance; the number lives only here. D145 established on this same box
    # that two identical reruns agree bit for bit while both differ from a frozen figure at ~1e-7
    # relative, so a tolerance under float32 epsilon tests the arithmetic order, not the item set.
    # Set to 1e-5 absolute (2e-6 relative), which still fails on a single changed item.
    ok_items = dm < 1e-5
    print(f"\n  CONTROL items      base margin {d['base_margin']:.9f} vs R10 "
          f"{d['r10_base_margin']:.9f}   diff {dm:.3e}  -> {'PASS' if ok_items else 'FAIL'}")

    # ---- control 3: the two direct variants must differ
    diffs = [abs(C[key(k)]['direct_linear'] - C[key(k)]['direct_renorm']) for k in band]
    ok_two = max(diffs) > 1e-9
    print(f"  CONTROL renorm     max|direct_linear - direct_renorm| over the band "
          f"{max(diffs):.6g}  -> {'PASS' if ok_two else 'FAIL (one is a copy of the other)'}")

    # ---- control 1, the registered gate: layer 27 has nothing downstream
    tot_band = [C[key(k)]['total'] for k in band]
    band_sd = sd(tot_band)
    last = [(NL - 1, h) for h in range(NH)]
    lim = L27_CONTROL_FRAC * band_sd
    # THREE VERSIONS, ALL PRINTED, AND THE FIRST IS THE ONE THAT WAS REGISTERED.
    # It FAILED, on a false premise about the architecture, and the two repairs were made AFTER
    # seeing that failure -- a weaker epistemic position than a registered pass, and it is labelled
    # as one rather than quietly presented as the control.
    variants = [('registered: direct_renorm, no MLP, fixed comparator', 'direct_renorm'),
                ('repair 1+2: + the block\'s own MLP, fixed comparator', 'direct_plus_own_mlp'),
                ('repair 3: + own MLP, R10\'s recomputed comparator', 'direct_plus_own_mlp_recomp')]
    errs = {}
    for lbl, fld in variants:
        if C[key(last[0])].get(fld) is None:
            continue
        e = [abs(C[key(k)][fld] - C[key(k)]['total']) for k in last]
        errs[fld] = e
        print(f"  CONTROL L{NL - 1:02d}  {lbl:<52s} max {max(e):.6g}  -> "
              f"{'PASS' if max(e) <= lim else 'FAIL'}")
    print(f"                     limit {L27_CONTROL_FRAC} x band sd = {lim:.6g}")
    err = errs.get('direct_plus_own_mlp_recomp', errs['direct_renorm'])
    ok_l27 = max(err) <= lim
    print(f"                     per-head errors of the gating variant "
          f"{[round(e, 6) for e in err]}")

    if not (ok_l27 and ok_items and ok_two):
        print('\n  -> UNVERIFIED: a registered control failed. The decomposition is not readable, '
              'and that is not an acquittal.')
        return 3

    # ---- the registered statistics
    usable = [k for k in band if abs(C[key(k)]['direct_renorm']) >= SMALL_DIRECT]
    small = [k for k in band if k not in usable]
    supp = [C[key(k)]['total'] / C[key(k)]['direct_renorm'] for k in usable]
    med = median(supp)

    smaller = sum(1 for k in band if abs(C[key(k)]['total']) < abs(C[key(k)]['direct_renorm']))
    p_sign = binom_tail(max(smaller, len(band) - smaller), len(band))

    # THE REGISTERED VERDICT RULE IS UNFIT AND IT FIRED `SELF-REPAIR-PRESENT` ON DATA THAT SAYS
    # THE OPPOSITE. Two breaks, both mine, both in the registration:
    #   (1) `median(suppression) <= 0.80` was written expecting a ratio in [0,1]. `suppression` is a
    #       ratio of two SIGNED quantities whose denominator crosses zero -- a Cauchy-like variable,
    #       observed median -0.1417 with quartiles spanning -31 to +49. A large NEGATIVE ratio means
    #       the total has the OPPOSITE SIGN to the direct path, which is not suppression at all, and
    #       it satisfies `<= 0.80` trivially.
    #   (2) the sign test is two-sided and the rule reads only its p-value, never its DIRECTION.
    #       |total| < |direct| holds on 53 of 168, so the significant direction is |total| >
    #       |direct| -- and the registration's own null reasoning says World N PREDICTS that.
    # This is the repository's own named class -- a claim whose test is not its own statement --
    # committed inside a pre-registration for the second time (see R10's POWER_PREREGISTRATION).
    # Recorded, not silently re-specified. The verdict is UNVERIFIED: the check was unfit, which is
    # NOT an acquittal and specifically NOT evidence for self-repair.
    registered_verdict = ('SELF-REPAIR-PRESENT' if (med <= SUPPRESSION_REPAIR and p_sign < ALPHA)
                          else 'AMPLIFICATION' if med >= SUPPRESSION_AMPLIFY
                          else 'NO-DYNAMIC-RESPONSE' if (NODYN_LO <= med <= NODYN_HI
                                                         and p_sign >= ALPHA)
                          else 'MIXED')
    verdict = 'UNVERIFIED_REGISTERED_STATISTIC_UNFIT'
    bigger = len(band) - smaller
    same_sign = sum(1 for k in band
                    if C[key(k)]['total'] * C[key(k)]['direct_renorm'] > 0)
    p_sign_agree = binom_tail(max(same_sign, len(band) - same_sign), len(band))
    at = sorted(abs(C[key(k)]['total']) for k in band)
    ad = sorted(abs(C[key(k)]['direct_renorm']) for k in band)
    ratio_of_medians = at[len(at) // 2] / ad[len(ad) // 2]
    pooled_rho = _spear([abs(C[key(k)]['total']) for k in band],
                        [abs(C[key(k)]['direct_renorm']) for k in band])
    print(f'\n  REGISTERED RULE RETURNS: {registered_verdict}  <- and it is UNFIT, see below')
    print(f'  |total| > |direct| on {bigger} of {len(band)}   '
          f'-- the significant direction, and World N PREDICTS it')
    print(f'  sign(total) == sign(direct) on {same_sign} of {len(band)}   '
          f'p {p_sign_agree:.4f}   -- indistinguishable from a coin flip')
    print(f'  median |total| {at[len(at) // 2]:.6f}   median |direct| {ad[len(ad) // 2]:.6f}   '
          f'ratio {ratio_of_medians:.4f}x')
    print(f'  pooled Spearman(|total|, |direct|) {pooled_rho:+.4f}')

    print(f'\n  usable band heads |direct_renorm| >= {SMALL_DIRECT}: {len(usable)} of {len(band)}'
          f'   ({len(small)} below threshold, reported separately)')
    print(f'  median suppression total/direct   {med:.4f}      '
          f'(repair <= {SUPPRESSION_REPAIR}, amplify >= {SUPPRESSION_AMPLIFY})')
    print(f'  |total| < |direct| on {smaller} of {len(band)} band heads   sign-test p {p_sign:.6g}')
    print(f'  quartiles of suppression  '
          f'{[round(sorted(supp)[i * (len(supp) - 1) // 4], 4) for i in range(5)]}')

    # ---- second separator, and it needs no threshold: depth
    print('\n  suppression BY LAYER -- World R requires depth dependence, World N forbids it')
    by_layer = {}
    for L in range(NL):
        ks = [(L, h) for h in range(NH) if abs(C[key((L, h))]['direct_renorm']) >= SMALL_DIRECT]
        if not ks:
            continue
        v = [C[key(k)]['total'] / C[key(k)]['direct_renorm'] for k in ks]
        by_layer[L] = {'n': len(ks), 'median_suppression': median(v),
                       'median_direct': median([C[key(k)]['direct_renorm'] for k in ks]),
                       'median_total': median([C[key(k)]['total'] for k in ks])}
    for L in sorted(by_layer):
        b = by_layer[L]
        print(f'    L{L:02d}  n={b["n"]:2d}  median suppression {b["median_suppression"]:+8.4f}   '
              f'direct {b["median_direct"]:+.5f}  total {b["median_total"]:+.5f}')
    dl = [L for L in sorted(by_layer)]
    rho_depth = _spear([float(L) for L in dl], [by_layer[L]['median_suppression'] for L in dl])
    print(f'    Spearman(layer, median suppression) over {len(dl)} layers = {rho_depth:+.4f}')

    # ---- comparator disagreement, the fourth registered confound
    flips = [C[key(k)]['comparator_flip_rate'] for k in band]
    print(f'\n  comparator disagreement rate  mean {sum(flips) / len(flips):.6f}   '
          f'max {max(flips):.6f}   (fixed clean comparator used throughout)')

    # ---- does direct explain the residual the three static predictors left?
    part = _direct_partial(C, band, key)
    if part:
        print(f"\n  within-layer partial(|centred total|, |direct| | mean_norm) = "
              f"{part['partial']:+.4f}   null 97.5th {part['null_975']:.4f}   p {part['p']:.4f}")
        print(f"  pooled {part['pooled']:+.4f}   "
              f"(three static predictors left 0.8484 unexplained)")

    print(f'\n  REGISTERED VERDICT: {verdict}')
    out = {'model': d['model'], 'n_items': d['n_items'],
           'control_variants': {fld: max(e) for fld, e in errs.items()},
           'controls': {'items_same': ok_items, 'renorm_distinct': ok_two,
                        'last_layer_exact': ok_l27,
                        'last_layer_max_abs_err': max(err), 'last_layer_limit': lim,
                        'base_margin_diff': dm},
           'n_usable': len(usable), 'n_small_direct': len(small),
           'median_suppression': med, 'n_smaller': smaller, 'n_band': len(band),
           'sign_test_p': p_sign, 'verdict': verdict,
           'registered_verdict_from_unfit_rule': registered_verdict,
           'n_bigger': bigger, 'n_same_sign': same_sign, 'p_sign_agreement': p_sign_agree,
           'median_abs_total': at[len(at) // 2], 'median_abs_direct': ad[len(ad) // 2],
           'ratio_of_median_magnitudes': ratio_of_medians,
           'pooled_spearman_abs_total_vs_abs_direct': pooled_rho,
           'suppression_quartiles': [sorted(supp)[i * (len(supp) - 1) // 4] for i in range(5)],
           'by_layer': by_layer, 'spearman_layer_vs_suppression': rho_depth,
           'comparator_flip_mean': sum(flips) / len(flips),
           'comparator_flip_max': max(flips),
           'direct_partial': part}
    op = HERE / 'results' / 'r20_analysis_qwen2.5-1.5b.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


def _spear(a, b):
    import headline as H
    return H._spearman(a, b)


def _direct_partial(C, band, key):
    """The fourth predictor, against the same effect vector and the same null mechanism()
    used -- depth-preserving permutation, so a depth confound cannot manufacture it."""
    import headline as H
    f6 = REPO / 'R6_intervention' / 'results' / 'r6_diag_item_variance_qwen2.5-1.5b.json'
    if not f6.exists():
        return None
    d6 = json.load(open(f6))
    per = {(r['layer'], r['head']): r for r in d6['per_head']}
    keys = [k for k in band if k in per]
    if len(keys) < 100:
        return {'error': f'R6 diagnostic covers {len(keys)} of {len(band)} band heads'}
    tot = {k: C[key(k)]['total'] for k in band}
    mu = sum(tot.values()) / len(tot)
    Y = [abs(tot[k] - mu) for k in keys]
    X = [abs(C[key(k)]['direct_renorm']) for k in keys]
    Z = [per[k]['mean_norm'] for k in keys]
    by_layer = {}
    for i, k in enumerate(keys):
        by_layer.setdefault(k[0], []).append(i)

    def within(y, x, z):
        vals = []
        for L, idx in by_layer.items():
            if len(idx) < 4:
                continue
            vals.append(H._partial([x[i] for i in idx], [y[i] for i in idx],
                                   [z[i] for i in idx]))
        return sum(vals) / len(vals)

    obs = within(Y, X, Z)
    rng = random.Random(SEED)
    null = []
    for _ in range(N_PERM):
        Yp = list(Y)
        for L, idx in by_layer.items():
            vals = [Yp[i] for i in idx]
            rng.shuffle(vals)
            for i, v in zip(idx, vals):
                Yp[i] = v
        null.append(within(Yp, X, Z))
    null.sort()
    p = sum(1 for z in null if abs(z) >= abs(obs)) / len(null)
    return {'partial': obs, 'pooled': H._partial(X, Y, Z), 'p': p,
            'null_975': null[int(0.975 * len(null))], 'n_heads': len(keys), 'n_perm': N_PERM}


if __name__ == '__main__':
    sys.exit(main())
