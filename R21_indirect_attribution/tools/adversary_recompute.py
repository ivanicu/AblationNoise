#!/usr/bin/env python3
"""D159-D167 -- every number an adversary returned about R21, RE-DERIVED here from the frozen results.

An agent's report is not evidence. This repository's own rule is that a claim cites the object, so
each of the reviewer's figures is recomputed independently and emitted, and the page quotes the
emitter rather than the transcript. Where my re-derivation disagrees with the report, the emitted
value is the one published and the disagreement is printed.
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROUND = HERE.parent
REPO = ROUND.parent
sys.path.insert(0, str(REPO))
import headline as H                                                     # noqa: E402

NL, NH = 28, 12
BAND = [(L, h) for L in range(14, 28) for h in range(NH)]
K = lambda t: 'L%02dH%02d' % t
CLASSES = ('att', 'mlp', 'emb', 'norm')
N_DRAW = 20000
SEED = 20260729


def med(v):
    w = sorted(v)
    n = len(w)
    return w[n // 2] if n % 2 else 0.5 * (w[n // 2 - 1] + w[n // 2])


def mannwhitney_z(a, b):
    """Normal approximation with tie correction; n is large enough here for it to be honest."""
    allv = sorted(a + b)
    rank = {}
    i = 0
    while i < len(allv):
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        r = (i + j) / 2.0 + 1
        rank[allv[i]] = r
        i = j + 1
    ra = sum(rank[x] for x in a)
    na, nb = len(a), len(b)
    u = ra - na * (na + 1) / 2.0
    mu = na * nb / 2.0
    sd = math.sqrt(na * nb * (na + nb + 1) / 12.0)
    return (u - mu) / sd


def main():
    r21 = json.load(open(ROUND / 'results' / 'r21_indirect_qwen2.5-1.5b.json'))
    C = r21['cells']
    r20 = json.load(open(REPO / 'R20_direct_indirect' / 'results'
                         / 'r20_direct_indirect_qwen2.5-1.5b.json'))['cells']
    out = {}

    # --- D159: the two remaining controls
    last = [(NL - 1, h) for h in range(NH)]
    out['L27_att_abs_max'] = max(C[K(k)]['att_abs'] for k in last)
    out['max_abs_att_minus_att_late'] = max(abs(C[K(k)]['att'] - C[K(k)]['att_late']) for k in BAND)
    out['n_heads_where_att_differs_from_att_late'] = sum(
        1 for k in BAND if C[K(k)]['att'] != C[K(k)]['att_late'])
    out['spearman_own_vs_direct_linear'] = H._spearman(
        [C[K(k)]['own'] for k in BAND], [r20[K(k)]['direct_linear'] for k in BAND])
    out['spearman_direct_linear_vs_direct_renorm'] = H._spearman(
        [r20[K(k)]['direct_linear'] for k in BAND], [r20[K(k)]['direct_renorm'] for k in BAND])
    out['spearman_own_vs_direct_renorm'] = H._spearman(
        [C[K(k)]['own'] for k in BAND], [r20[K(k)]['direct_renorm'] for k in BAND])
    # the control that WAS available at L27, where the decomposition is complete
    out['L27_max_abs_complete_minus_total_r10'] = max(
        abs(C[K(k)]['own'] + C[K(k)]['mlp'] + C[K(k)]['norm'] + C[K(k)]['emb']
            - C[K(k)]['total_r10']) for k in last)

    # --- D160: the 44-head subgroup
    flip = {k: r20[K(k)]['comparator_flip_rate'] for k in BAND}
    stable = [k for k in BAND if flip[k] == 0.0]
    unstable = [k for k in BAND if flip[k] != 0.0]
    out['n_stable'] = len(stable)
    out['spearman_flip_vs_abs_own'] = H._spearman([flip[k] for k in BAND],
                                                  [abs(C[K(k)]['own']) for k in BAND])
    out['spearman_flip_vs_abs_att'] = H._spearman([flip[k] for k in BAND],
                                                  [abs(C[K(k)]['att']) for k in BAND])
    out['median_abs_own_stable'] = med([abs(C[K(k)]['own']) for k in stable])
    out['median_abs_own_unstable'] = med([abs(C[K(k)]['own']) for k in unstable])
    out['mannwhitney_p_abs_own'] = math.erfc(abs(mannwhitney_z(
        [abs(C[K(k)]['own']) for k in stable],
        [abs(C[K(k)]['own']) for k in unstable])) / math.sqrt(2))
    out['mannwhitney_z_abs_own'] = mannwhitney_z([abs(C[K(k)]['own']) for k in stable],
                                                 [abs(C[K(k)]['own']) for k in unstable])

    def att_share(pop):
        v = []
        for k in pop:
            d = sum(abs(C[K(k)][c]) for c in CLASSES)
            if d > 0:
                v.append(abs(C[K(k)]['att']) / d)
        return med(v) if v else float('nan')

    out['att_share_stable'] = att_share(stable)
    # depth-matched null: same per-layer counts, drawn at random within each layer
    comp = {}
    for k in stable:
        comp[k[0]] = comp.get(k[0], 0) + 1
    rng = random.Random(SEED)
    null = []
    for _ in range(N_DRAW):
        pop = []
        for L, n in comp.items():
            pop += rng.sample([(L, h) for h in range(NH)], n)
        null.append(att_share(pop))
    null.sort()
    out['depth_matched_null'] = {
        'mean': sum(null) / len(null), 'p025': null[int(0.025 * len(null))],
        'p975': null[int(0.975 * len(null))],
        'frac_reaching_0.50': sum(1 for z in null if z >= 0.50) / len(null),
        'percentile_of_observed': sum(1 for z in null if z < out['att_share_stable']) / len(null),
        'n_draw': N_DRAW}

    # --- D162: live members
    live_att = {k: (NL - 1 - k[0]) * NH for k in BAND}
    live_mlp = {k: NL - k[0] for k in BAND}
    out['median_live_att_members'] = med([live_att[k] for k in BAND])
    out['median_live_mlp_members'] = med([live_mlp[k] for k in BAND])
    pa = med([abs(C[K(k)]['att']) / live_att[k] for k in BAND if live_att[k] > 0])
    pm = med([abs(C[K(k)]['mlp']) / live_mlp[k] for k in BAND if live_mlp[k] > 0])
    out['per_member_att_live'] = pa
    out['per_member_mlp_live'] = pm
    out['per_member_ratio_live'] = pm / pa
    out['per_member_ratio_published'] = ((med([abs(C[K(k)]['mlp']) for k in BAND]) / 28)
                                         / (med([abs(C[K(k)]['att']) for k in BAND]) / 335))

    # --- D161: cancellation vs the iid random-sign null 1/sqrt(n_live)
    canc = {}
    for cls, live in (('att', live_att), ('mlp', live_mlp)):
        rows = [(k, abs(C[K(k)][cls]) / C[K(k)][cls + '_abs'])
                for k in BAND if C[K(k)][cls + '_abs'] > 0]
        v = sorted(x for _, x in rows)
        canc[cls] = {
            'n': len(rows), 'p10': v[int(0.10 * len(v))], 'median': med(v),
            'p90': v[int(0.90 * len(v))], 'max': v[-1],
            'median_null_1_over_sqrt_n_live': med([1 / math.sqrt(live[k]) for k, _ in rows]),
            'n_layers_below_own_null': len({k[0] for k, x in rows
                                            if x < 1 / math.sqrt(live[k])})}
    out['cancellation'] = canc
    # I BRIEFLY RECORDED A DISAGREEMENT HERE THAT DID NOT EXIST. My first re-derivation took head 0
    # (0.9716) while the reviewer's 0.672 is the per-head MEDIAN over the last layer -- two different
    # statistics of the same quantity, and the layer table below reproduces its number exactly at
    # L27. Kept as a note because reading a mismatch between two statistics as a mismatch between two
    # PEOPLE is how a correct report gets discounted.
    out['L27_mlp_cancellation_head0'] = abs(C[K((27, 0))]['mlp']) / C[K((27, 0))]['mlp_abs']
    out['L27_mlp_cancellation_median'] = med([abs(C[K((27, h))]['mlp']) / C[K((27, h))]['mlp_abs']
                                              for h in range(NH)])
    out['mlp_cancellation_by_layer'] = {f'L{L}': med([abs(C[K((L, h))]['mlp'])
                                                      / C[K((L, h))]['mlp_abs']
                                                      for h in range(NH)])
                                        for L in range(14, 28)}

    # --- D164: NORM against the indirect term rather than SUM|class|
    ind = {k: sum(C[K(k)][c] for c in CLASSES) for k in BAND}
    out['median_norm_over_indirect'] = med([abs(C[K(k)]['norm']) / abs(ind[k])
                                            for k in BAND if ind[k] != 0])
    out['ratio_of_medians_norm_over_indirect'] = (med([abs(C[K(k)]['norm']) for k in BAND])
                                                  / med([abs(ind[k]) for k in BAND]))
    out['median_norm_over_total_here'] = (med([abs(C[K(k)]['norm']) for k in BAND])
                                          / med([abs(C[K(k)]['total_measured_here']) for k in BAND]))
    out['n_norm_exceeds_indirect'] = sum(1 for k in BAND if abs(C[K(k)]['norm']) > abs(ind[k]))
    out['n_norm_exceeds_total'] = sum(1 for k in BAND
                                      if abs(C[K(k)]['norm']) > abs(C[K(k)]['total_measured_here']))
    out['n_norm_exceeds_own'] = sum(1 for k in BAND
                                    if abs(C[K(k)]['norm']) > abs(C[K(k)]['own']))
    out['n_norm_largest_class'] = sum(
        1 for k in BAND if max(CLASSES, key=lambda c: abs(C[K(k)][c])) == 'norm')
    out['n_norm_sign_agrees_with_indirect'] = sum(1 for k in BAND
                                                  if C[K(k)]['norm'] * ind[k] > 0)

    # --- D165: three aggregations that do sum to 1, and the signed one
    def shares(fn):
        r = {}
        for c in CLASSES:
            r[c] = fn(c)
        return r

    med_share = shares(lambda c: med([abs(C[K(k)][c]) / sum(abs(C[K(k)][x]) for x in CLASSES)
                                      for k in BAND]))
    mean_share = shares(lambda c: sum(abs(C[K(k)][c]) / sum(abs(C[K(k)][x]) for x in CLASSES)
                                      for k in BAND) / len(BAND))
    share_of_med = shares(lambda c: med([abs(C[K(k)][c]) for k in BAND])
                          / sum(med([abs(C[K(k)][x]) for k in BAND]) for x in CLASSES))
    signed = shares(lambda c: med([C[K(k)][c] / sum(abs(C[K(k)][x]) for x in CLASSES)
                                   for k in BAND]))
    out['aggregations'] = {'median_of_shares': med_share, 'mean_of_shares': mean_share,
                           'share_of_medians': share_of_med, 'median_signed_share': signed,
                           'sum_median_of_shares': sum(med_share.values()),
                           'sum_mean_of_shares': sum(mean_share.values()),
                           'sum_share_of_medians': sum(share_of_med.values()),
                           'sum_median_signed': sum(signed.values())}

    # --- D166: share by layer, and the band-cut sensitivity
    out['att_share_by_layer'] = {f'L{L}': att_share([(L, h) for h in range(NH)])
                                 for L in range(14, 28)}
    sub = [(L, h) for L in range(14, 22) for h in range(NH)]
    out['att_share_band_L14_L21'] = att_share(sub)
    out['mlp_share_band_L14_L21'] = med([abs(C[K(k)]['mlp'])
                                         / sum(abs(C[K(k)][x]) for x in CLASSES) for k in sub])

    # --- D163: the ratio under one convention, and on the usable population
    usable = [k for k in BAND if abs(C[K(k)]['own']) >= 0.01]
    out['n_usable_own'] = len(usable)
    out['ratio_same_convention'] = (med([abs(C[K(k)]['total_measured_here']) for k in BAND])
                                    / med([abs(C[K(k)]['own']) for k in BAND]))
    out['ratio_published_mixed_convention'] = (med([abs(C[K(k)]['total_r10']) for k in BAND])
                                               / med([abs(C[K(k)]['own']) for k in BAND]))
    out['per_head_ratio_here_over_own_usable'] = med(
        [abs(C[K(k)]['total_measured_here']) / abs(C[K(k)]['own']) for k in usable])
    out['per_head_ratio_r10_over_own_usable'] = med(
        [abs(C[K(k)]['total_r10']) / abs(C[K(k)]['own']) for k in usable])

    op = ROUND / 'results' / 'r21_adversary_recompute.json'
    json.dump(out, open(op, 'w'), indent=1)
    for k, v in out.items():
        if isinstance(v, (int, float)):
            print(f'  {k:48s} {v!r}')
    print(f'  aggregation sums: median-of-shares {out["aggregations"]["sum_median_of_shares"]:.4f}  '
          f'mean {out["aggregations"]["sum_mean_of_shares"]:.4f}  '
          f'share-of-medians {out["aggregations"]["sum_share_of_medians"]:.4f}')
    print(f'  depth-matched null {out["depth_matched_null"]}')
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
