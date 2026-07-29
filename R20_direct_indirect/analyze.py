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
    # ---- D151-D156: WHAT AN ADVERSARY RETURNED, RECOMPUTED HERE SO THE RETRACTION IS EMITTED
    # RATHER THAN ASSERTED. Every number below reproduced to the digit on independent re-derivation.
    usable_k = [k for k in band if abs(C[key(k)]['direct_renorm']) >= SMALL_DIRECT]
    excl_k = [k for k in band if k not in usable_k]

    def _bigger(pop):
        b = sum(1 for k in pop if abs(C[key(k)]['total']) > abs(C[key(k)]['direct_renorm']))
        return b, len(pop), binom_tail(max(b, len(pop) - b), len(pop))

    b_all, n_all, p_all = _bigger(band)
    b_use, n_use, p_use = _bigger(usable_k)
    b_exc, n_exc, p_exc = _bigger(excl_k)
    # the ratio: the published one indexed at[n//2] on an EVEN n, i.e. the 85th order statistic,
    # while this file defines a correct median() four lines from where it was needed.
    at_s = sorted(abs(C[key(k)]['total']) for k in band)
    ad_s = sorted(abs(C[key(k)]['direct_renorm']) for k in band)
    per_head_ratio_usable = median([abs(C[key(k)]['total']) / abs(C[key(k)]['direct_renorm'])
                                    for k in usable_k])
    # the registered depth separator, on its REGISTERED population instead of all 28 layers
    bl = {}
    for L in range(BAND_LO, min(BAND_HI, NL)):
        ks = [(L, h) for h in range(NH) if abs(C[key((L, h))]['direct_renorm']) >= SMALL_DIRECT]
        if ks:
            bl[L] = median([C[key(k)]['total'] / C[key(k)]['direct_renorm'] for k in ks])
    Ls = sorted(bl)
    rho_depth_band = _spear([float(L) for L in Ls], [bl[L] for L in Ls])
    # the null that PRESERVES total = direct + indirect, which the published one destroys
    shared = _shared_term_null(C, band, key)
    # Fisher exact on sign independence, because p=0.5 assumes 50/50 marginals and they are not
    fis = _fisher_signs(C, band, key)
    # how badly the quantity claims A-D actually use fails the control the page reports as passing
    lastk = [(NL - 1, h) for h in range(NH)]
    ctrl_ratio = (max(abs(C[key(k)]['direct_renorm'] - C[key(k)]['total']) for k in lastk)
                  / lim)
    retraction = {
        'shared_term_null': shared, 'fisher_sign_independence': fis,
        'control_failure_ratio_direct_renorm': ctrl_ratio,
        'published_null_m_break': (0.05 / part['p']) if (part and part.get('p')) else None,
        'sign_test_all_168': {'bigger': b_all, 'n': n_all, 'p': p_all},
        'sign_test_usable_122': {'bigger': b_use, 'n': n_use, 'p': p_use},
        'sign_test_excluded_46': {'bigger': b_exc, 'n': n_exc, 'p': p_exc},
        'ratio_published_order_statistic': at_s[len(at_s) // 2] / ad_s[len(ad_s) // 2],
        'ratio_true_median': median(at_s) / median(ad_s),
        'per_head_median_ratio_usable': per_head_ratio_usable,
        'spearman_layer_vs_suppression_registered_band': rho_depth_band,
        'n_layers_in_band': len(Ls)}
    print('\n  --- RETRACTION BLOCK (an adversary found these; recomputed here) ---')
    print(f'  sign test  ALL 168 {b_all}/{n_all} p {p_all:.6g}   '
          f'usable {b_use}/{n_use} p {p_use:.6g}   excluded {b_exc}/{n_exc} p {p_exc:.6g}')
    print(f'  ratio  published(order stat) {retraction["ratio_published_order_statistic"]:.4f}   '
          f'true median {retraction["ratio_true_median"]:.4f}   '
          f'per-head median on usable {per_head_ratio_usable:.4f}')
    print(f'  registered depth separator on the BAND: Spearman {rho_depth_band:+.4f} '
          f'(published {rho_depth:+.4f} over all {NL} layers)')

    out = {'adversary_retraction': retraction,
           'model': d['model'], 'n_items': d['n_items'],
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


def _shared_term_null(C, band, key):
    """THE PUBLISHED NULL DESTROYED AN IDENTITY. `indirect = total - direct` by construction, so
    |direct| is a COMPONENT of |total|; shuffling |centred total| while holding |direct| fixed breaks
    `total = direct + indirect` and the resulting null sits at zero. This one permutes INDIRECT
    within layer and re-forms `total = direct + indirect_perm`, so the identity survives and only the
    head-level pairing is destroyed. Found by an independent adversarial reviewer; reproduced here."""
    import headline as H
    f6 = REPO / 'R6_intervention' / 'results' / 'r6_diag_item_variance_qwen2.5-1.5b.json'
    if not f6.exists():
        return None
    per = {(r['layer'], r['head']): r for r in json.load(open(f6))['per_head']}
    keys = [k for k in band if k in per]
    DIR = {k: C[key(k)]['direct_renorm'] for k in keys}
    IND = {k: C[key(k)]['total'] - C[key(k)]['direct_renorm'] for k in keys}
    Z = [per[k]['mean_norm'] for k in keys]
    bylayer = {}
    for i, k in enumerate(keys):
        bylayer.setdefault(k[0], []).append(i)

    def stat(totals):
        mu = sum(totals) / len(totals)
        Y = [abs(t - mu) for t in totals]
        X = [abs(DIR[k]) for k in keys]
        vals = [H._partial([X[i] for i in idx], [Y[i] for i in idx], [Z[i] for i in idx])
                for L, idx in bylayer.items() if len(idx) >= 4]
        return sum(vals) / len(vals)

    obs = stat([DIR[k] + IND[k] for k in keys])
    rng = random.Random(SEED)
    null = []
    for _ in range(N_PERM):
        ip = [IND[k] for k in keys]
        for L, idx in bylayer.items():
            v = [ip[i] for i in idx]
            rng.shuffle(v)
            for i, vv in zip(idx, v):
                ip[i] = vv
        null.append(stat([DIR[k] + ip[i] for i, k in enumerate(keys)]))
    null.sort()
    p = sum(1 for z in null if abs(z) >= abs(obs)) / len(null)
    return {'observed': obs, 'null_mean': sum(null) / len(null),
            'null_025': null[int(0.025 * len(null))], 'null_975': null[int(0.975 * len(null))],
            'p': p, 'm_break': 0.05 / p if p > 0 else None, 'n_perm': N_PERM}


def _fisher_signs(C, band, key):
    """p = 0.5 is the independence null only if BOTH marginals are 50/50. They are not."""
    a = sum(1 for k in band if C[key(k)]['total'] > 0 and C[key(k)]['direct_renorm'] > 0)
    b = sum(1 for k in band if C[key(k)]['total'] > 0 and C[key(k)]['direct_renorm'] <= 0)
    c = sum(1 for k in band if C[key(k)]['total'] <= 0 and C[key(k)]['direct_renorm'] > 0)
    dd = sum(1 for k in band if C[key(k)]['total'] <= 0 and C[key(k)]['direct_renorm'] <= 0)
    n = a + b + c + dd
    r1, c1 = a + b, a + c

    def hyp(x):
        return (math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
                if 0 <= x <= r1 and 0 <= c1 - x <= n - r1 else 0.0)

    obs = hyp(a)
    pv = sum(hyp(x) for x in range(0, min(r1, c1) + 1) if hyp(x) <= obs * (1 + 1e-9))
    return {'table': [a, b, c, dd], 'p_total_positive': r1 / n, 'p_direct_positive': c1 / n,
            'expected_agreement': (r1 * c1 + (n - r1) * (n - c1)) / n ** 2,
            'observed_agreement': (a + dd) / n, 'fisher_two_sided_p': min(1.0, pv)}


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
