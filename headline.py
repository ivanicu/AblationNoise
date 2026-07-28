#!/usr/bin/env python3
"""THE HANDLE — every number this repository claims, recomputed from its own checked-in results.

    make headline      print them
    make verify        print them and exit non-zero if any README number has drifted

No GPU, no model download, no network, under two seconds. The point is not convenience. Twice in
this project a number reached a README from a commit message and could not be regenerated
afterwards (R4's fold errors, R5's floor-widening range). A claim whose generator does not exist is
indistinguishable from a claim that was never true, so every headline number now has one.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(pattern):
    out = {}
    for f in sorted(glob.glob(str(HERE / pattern))):
        d = json.load(open(f))
        out[d['model']] = d
    return out


def r1():
    """ratio_k1 = band floor / sham floor at k=1.

    The sham arm ablates a head and restores it, so it isolates 'that you ablated one head' from
    'WHICH head you ablated'. The ratio is the quantity that transfers: both arms carry the same
    baseline margin in their denominator, so it cancels and the ratio is immune to the vocabulary
    changes that move the floor itself by 1.7x.
    """
    rows = []
    for name, d in load('R1_noise_floor/results/*.json').items():
        c = d['cells']
        rows.append({'model': name, 'ratio_k1': c['band_k1']['floor'] / c['sham_k1']['floor'],
                     'band_floor': c['band_k1']['floor'], 'sham_floor': c['sham_k1']['floor'],
                     'band_sd': c['band_k1']['sd'], 'sham_sd': c['sham_k1']['sd'],
                     'base_margin': d['base_margin'],
                     'verdict': d['verdict'], 'n_items': d['n_items'],
                     'replicate': name.endswith('-bf16')})
    # internlm2's sham floor is as large as its band floor: on that model the instrument does not
    # separate the two arms at all, so it is excluded by its OWN LIVE CONTROL rather than by a
    # judgement about the model. A cell whose control fails is not a data point that went the other
    # way; it is a cell with no reading.
    for r in rows:
        r['informative'] = (not r['replicate']) and r['ratio_k1'] > 1.5
    inf = [r for r in rows if r['informative']]
    return {'rows': rows, 'n_informative': len(inf),
            'ratio_min': min(r['ratio_k1'] for r in inf),
            'ratio_max': max(r['ratio_k1'] for r in inf)}


def r1_vocabulary():
    """AMENDMENT 2's measurement: the dimensionless floor moves for two reasons.

    The same model, the same draws, the same set sizes -- only the four answer nouns change. The
    raw noise and the floor can move in OPPOSITE directions, because the baseline margin is the
    floor's denominator and the vocabulary moves that too. This is why the repository's transferable
    quantity is a RATIO of two floors rather than a floor.
    """
    old = load('R1_noise_floor/results/original_vocabulary/*.json')
    new = load('R1_noise_floor/results/*.json')
    rows = []
    for name, o in old.items():
        n = new.get(name)
        if n is None:
            continue
        for k in (1, 5):
            ck, nk = f'band_k{k}', f'band_k{k}'
            if ck not in o['cells'] or nk not in n['cells']:
                continue
            rows.append({'model': name, 'k': k,
                         # THE NUMBER THE '7 OF 8' CLAIM RESTS ON. The author's eight prior
                         # single-head effects were measured in the ORIGINAL room vocabulary, so
                         # the floor they are placed against must be the original one too. Emitted
                         # here, from the original-vocabulary file, rather than left as a figure
                         # in prose whose provenance is invisible.
                         'two_sd_original': 2 * o['cells'][ck]['sd'],
                         'sd_original': o['cells'][ck]['sd'],
                         'sd_pct': 100 * (n['cells'][nk]['sd'] / o['cells'][ck]['sd'] - 1),
                         'floor_pct': 100 * (n['cells'][nk]['floor'] / o['cells'][ck]['floor'] - 1),
                         'base_old': o['base_margin'], 'base_new': n['base_margin']})
    return rows


def _pct(vals):
    v = sorted(vals)
    n = len(v)
    def q(f):
        # Linear interpolation, matching numpy's default so the runner's own percentile keys and
        # these recomputed ones cannot disagree on the files that have both.
        if n == 1:
            return v[0]
        x = f * (n - 1)
        lo = int(x)
        hi = min(lo + 1, n - 1)
        return v[lo] + (x - lo) * (v[hi] - v[lo])
    return {'null_median': q(0.5), 'null_p10': q(0.10),
            'null_iqr': q(0.75) - q(0.25), 'null_min': min(v), 'null_max': max(v)}


def r2():
    rows = []
    for name, d in load('R2_inversion/results/*.json').items():
        # Older result files predate the validity key; recomputing it from the logprob rather than
        # defaulting it keeps a missing key from silently reading as 'valid'.
        bp = d.get('baseline_prob', math.exp(d['baseline_logprob']))
        rows.append({'model': name, 'baseline_prob': bp, 'valid': bp > 0.1,
                     'sign_correct': bool(d['sign_correct']), 'd_top': d['d_top'],
                     # The heavy-tailed null R2's docstring is about: one draw of thirty at -13.66
                     # while the other 29 sat inside +-1.0. Emitted so the prose that cites it has
                     # a generator behind it.
                     'null_sd': d['null']['sd'],
                     # COMPUTED FROM THE DRAWS, not read from a key. The percentile keys were
                     # added to the runner after the first models were measured, so d.get()
                     # returns None on phi and qwen -- and a table row rendered from None is a row
                     # with nothing behind it. The 30 draws are in every file; use them.
                     **_pct(d['null']['values'])})
    valid = [r for r in rows if r['valid']]
    return {'rows': rows, 'n_valid': len(valid),
            'n_inverted': sum(not r['sign_correct'] for r in valid)}


def r5():
    """Does ablating at EVERY position instead of one make the effect easier to read?

    Reported under two floor definitions. They disagree about how much the floor widens and agree
    about the direction in all six cells -- so the direction is a property of the data and the
    magnitude is a property of the statistic, which is exactly the distinction the original
    write-up failed to make.
    """
    rows = []
    for name, d in load('R5_factorial/results/*.json').items():
        for ro in ('margin', 'kl'):
            F, A = d['cells'][f'final_{ro}'], d['cells'][f'all_{ro}']
            wF, wA = F['null_p90'] - F['null_p10'], A['null_p90'] - A['null_p10']
            rows.append({
                'model': name, 'readout': ro,
                'read_2sd_final': abs(F['effect']) / (2 * F['null_sd']),
                'read_2sd_all': abs(A['effect']) / (2 * A['null_sd']),
                'read_w_final': abs(F['effect']) / wF, 'read_w_all': abs(A['effect']) / wA,
                'floor_widen_sd': A['null_sd'] / F['null_sd'], 'floor_widen_w': wA / wF,
                'effect_change': abs(A['effect']) / abs(F['effect']),
                'change_2sd': (abs(A['effect']) / (2 * A['null_sd'])) /
                              (abs(F['effect']) / (2 * F['null_sd'])),
                'change_w': (abs(A['effect']) / wA) / (abs(F['effect']) / wF),
                'mech_attn': d['mechanism_attn'], 'mechanism': d['mechanism'],
                'effect_final': F['effect'], 'effect_all': A['effect'],
                'baseline_final': F['baseline'],
            })
    # THE ~100x SCALE CLAIM, computed rather than characterised. Readability is a ratio, so a cell
    # can clear its null with an effect two orders of magnitude smaller than another cell's.
    eff = [abs(r['effect_final']) for r in rows]
    kle = [abs(r['effect_final']) for r in rows if r['readout'] == 'kl']
    return {'rows': rows, 'n_cells': len(rows),
            'effect_scale_span': max(eff) / min(eff),
            'kl_effect_span': max(kle) / min(kle),
            'n_worse_2sd': sum(r['read_2sd_all'] < r['read_2sd_final'] for r in rows),
            'n_worse_w': sum(r['read_w_all'] < r['read_w_final'] for r in rows),
            'widen_sd': (min(r['floor_widen_sd'] for r in rows),
                         max(r['floor_widen_sd'] for r in rows)),
            'widen_w': (min(r['floor_widen_w'] for r in rows),
                        max(r['floor_widen_w'] for r in rows)),
            'effect_change': (min(r['effect_change'] for r in rows),
                              max(r['effect_change'] for r in rows))}


def r6():
    """AMENDED STATISTIC (R6_intervention/AMENDMENT_1_statistic_degenerates.md).

    readability(X) = |positive control effect| / band sd(X) -- a known, previously established
    effect measured against the null of the SAME arm. The pre-registered ratio_k1 is reported
    beside it and marked degenerate wherever the sham sd has collapsed, because that is the number
    the pre-registration named and hiding it would be a quieter kind of revision.
    """
    rows = []
    for name, d in load('R6_intervention/results/*.json').items():
        a = d['arms']
        r = {'model': name, 'informative': d['informative'],
             'check1': d['check1_zero_reproduces_r1'].get('reproduces'),
             'check1_rel_diff': d['check1_zero_reproduces_r1'].get('rel_diff'),
             'dead_arms': d['check2_dead_arms'], 'round_valid': d['round_valid']}
        for iv in ('zero', 'mean', 'resample'):
            r[f'read_{iv}'] = abs(a[iv]['positive_control']) / a[iv]['band_sd']
            r[f'bandsd_{iv}'] = a[iv]['band_sd']
            r[f'shamsd_{iv}'] = a[iv]['sham_sd']
            r[f'pc_{iv}'] = a[iv]['positive_control']
            r[f'ratio_k1_{iv}'] = a[iv]['ratio_k1']
            # The pre-registered statistic is degenerate exactly when its denominator has
            # collapsed relative to the arm it was calibrated on. Flagged per arm rather than
            # dropped, so the reader sees which number the pre-registration actually named.
            r[f'ratio_k1_degenerate_{iv}'] = bool(
                a[iv]['sham_sd'] < 0.05 * a['zero']['sham_sd'])
        for iv in ('mean', 'resample'):
            r[f'rr_{iv}'] = r[f'read_{iv}'] / r['read_zero']
        rows.append(r)
    if not rows:
        return None
    inf = [r for r in rows if r['informative']]
    def med(xs):
        xs = sorted(xs)
        n = len(xs)
        return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)
    return {'rows': rows, 'n_informative': len(inf),
            # The pre-registered gate band, emitted so a threshold quoted in prose is traceable to
            # the code that applies it rather than to someone's memory of the pre-registration.
            'gate_band_low': 0.67, 'gate_band_high': 1.5,
            # Emitted into the JSON, not only into the human print. Detector 6 reads --json, and a
            # quantity that exists in one output mode and not the other is how the two drift: the
            # prose cites a number the machine-readable path never produced, and nothing notices.
            'sham_collapse_max': max(r['shamsd_zero'] / r['shamsd_mean'] for r in rows),
            'median_rr_mean': med([r['rr_mean'] for r in inf]),
            'median_rr_resample': med([r['rr_resample'] for r in inf]),
            'n_valid_rounds': sum(r['round_valid'] for r in rows),
            'all_check1_pass': all(r['check1'] for r in rows if r['check1'] is not None)}


def r7():
    """At a FIXED displacement size, does the direction change readability?

    R6 could not answer this because its arms differed in size by 4-7x. R7's three matched arms
    write a point exactly d = ||x - mu|| away from x and differ only in which way; `zero` is the
    unmatched anchor that must reproduce R1. AMENDMENT 1 merges two of the three pre-registered
    worlds -- they had identical rows -- so the gate turns on S (size is all) alone.
    """
    rows = []
    for name, d in load('R7_norm_matched/results/*.json').items():
        a = d['arms']
        r = {'model': name, 'include': d['include'], 'include_fail': d['include_fail'],
             'round_valid': d['round_valid'], 'matched': d['check1_matched'],
             'match_spread': d['check1_spread'],
             'check2': d['check2_zero_reproduces_r1'].get('reproduces'),
             'check2_rel_diff': d['check2_zero_reproduces_r1'].get('rel_diff'),
             'dead_arms': d['check3_dead_arms'],
             'anchor_ratio': a['zero']['realized_disp_rms'] / a['mean']['realized_disp_rms'],
             'overshoot': a['shrink'].get('n_overshoot_past_origin', 0),
             'overshoot_pct': 100 * a['shrink'].get('n_overshoot_past_origin', 0) /
                              max(1, d['n_items'] * d['n_draws'])}
        for arm in ('zero', 'mean', 'shrink', 'randdir'):
            r[f'read_{arm}'] = a[arm]['readability']
            r[f'floor_{arm}'] = a[arm]['band_floor']
        r['rr_shrink'] = d['rr']['shrink']
        r['rr_randdir'] = d['rr']['randdir']
        # THE QUANTITY THAT DECIDED WHY TWO ROUNDS RETURNED `NOT MET`. The mean arm's readability
        # as a fraction of the SAME model's zero arm. Not a matched comparison -- zero displaces
        # by ||x|| and mean by d -- so it says nothing about direction. What it does say is that
        # the fraction is STABLE across models, which is what makes the |PC| > 1 band-sd exclusion
        # a threshold crossing a smooth quantity rather than an instrument failing.
        r['mean_over_zero'] = a['mean']['readability'] / a['zero']['readability']
        rows.append(r)
    if not rows:
        return None
    inc = [r for r in rows if r['include'] and r['round_valid']]
    def med(xs):
        xs = sorted(xs); n = len(xs)
        return None if not n else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)
    mz = [r['mean_over_zero'] for r in rows]
    out = {'rows': rows, 'n_included': len(inc), 'n_valid': sum(r['round_valid'] for r in rows),
           'mean_over_zero_min': min(mz), 'mean_over_zero_max': max(mz),
           'mean_arm_readability_deficit_min': 1 / max(mz),
           'mean_arm_readability_deficit_max': 1 / min(mz),
           'n_mean_arm_died': sum(r['read_mean'] < 1 for r in rows),
           'worst_match_spread_pct': 100 * max(r['match_spread'] for r in rows),
           'total_overshoot': sum(r['overshoot'] for r in rows),
           'median_rr_shrink': med([r['rr_shrink'] for r in inc]),
           'median_rr_randdir': med([r['rr_randdir'] for r in inc])}
    if out['median_rr_shrink'] is not None:
        # The gate turns on S alone (AMENDMENT 1). S is refused as soon as either matched arm's
        # median lands outside the pre-registered band; it is not confirmed by one arm.
        s_ok = (0.67 <= out['median_rr_shrink'] <= 1.5 and
                0.67 <= out['median_rr_randdir'] <= 1.5)
        d_ok = (not (0.5 <= out['median_rr_shrink'] <= 2.0) or
                not (0.5 <= out['median_rr_randdir'] <= 2.0))
        out['gate'] = ('SIZE-IS-ALL' if s_ok else
                       'DIRECTION-MATTERS' if d_ok else 'AMBIGUOUS')
        # The ordering is reported as an ORDERING because AMENDMENT 1 forbids saying why.
        if inc:
            order = sorted(('mean', 'shrink', 'randdir'),
                           key=lambda a: med([r[f'read_{a}'] for r in inc]))
            out['readability_order_low_to_high'] = order
            out['order_consistent'] = all(
                sorted(('mean', 'shrink', 'randdir'), key=lambda a: r[f'read_{a}']) == order
                for r in inc)
            # THE ORDER IS REPORTED OVER EVERY CELL, not only the included ones. It is a
            # WITHIN-CELL comparison -- three readabilities measured on the same model, the same
            # items and the same draws -- so it needs no ratio, no cross-model aggregation and no
            # inclusion rule. The inclusion rule exists to protect a RATIO whose denominator can
            # be a dead arm; an ordering has no denominator to protect. Both counts are printed
            # so a reader can see that the wider one is not the gate.
            out['n_cells_total'] = len(rows)
            out['n_cells_matching_order'] = sum(
                sorted(('mean', 'shrink', 'randdir'), key=lambda a: r[f'read_{a}']) == order
                for r in rows)
    return out


def out_mz(R):
    return '  '.join(f"{r['model'].split('-')[0]} {r['mean_over_zero']:.2f}" for r in R['rows'])


def r6_diag():
    """The pre-registered separator between 'gentler intervention' and 'nearly the identity'.

    displacement_ratio = ||x_i - mean_over_items|| / ||x_i||, over band heads, from a capture pass
    with no ablation at all. Its complement is the fraction of a head's final-position output that
    does NOT vary across items -- which is what makes mean-ablation small there.
    """
    rows = []
    for name, d in load('R6_intervention/results/r6_diag_item_variance_*.json').items():
        rows.append({'model': name, 'median': d['displacement_ratio_median'],
                     'p10': d['displacement_ratio_p10'], 'p90': d['displacement_ratio_p90'],
                     'item_independent_pct': 100 * (1 - d['displacement_ratio_median']),
                     'n_heads': d['n_heads_measured'], 'verdict': d['verdict']})
    if not rows:
        return None
    meds = [r['median'] for r in rows]
    return {'rows': rows, 'displacement_pct_min': 100 * min(meds),
            'displacement_pct_max': 100 * max(meds),
            'item_independent_pct_min': 100 * (1 - max(meds)),
            'item_independent_pct_max': 100 * (1 - min(meds)),
            'n_reaching_world_G': sum(m > 0.5 for m in meds),
            'n_world_I': sum(m < 0.2 for m in meds)}


def r4():
    p = HERE / 'R4_predictability' / 'results' / 'r4_predictability.json'
    if not p.exists():
        return None
    return json.load(open(p))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    A, B, E = r1(), r2(), r5()
    D, V, S, G, R = r4(), r1_vocabulary(), r6(), r6_diag(), r7()

    if args.json:
        print(json.dumps({'r1': A, 'r1_vocabulary': V, 'r2': B, 'r4': D, 'r5': E, 'r6': S, 'r6_diag': G, 'r7': R},
                         indent=2, default=float))
        return 0

    print("R1  how much of an ablation effect is WHICH component rather than THAT one?")
    for r in sorted(A['rows'], key=lambda r: r['ratio_k1']):
        # NOT "excluded by its own sham control" -- that string said the instrument was dead on
        # this model, and it is not: internlm2's zero-arm positive control is 4.69 band sd, the
        # second strongest of the four measured in R7. ratio_k1 = 0.98 says something else
        # entirely -- that on this model an EARLY-layer head and a LATE-layer head do comparable
        # damage. That is a fact about its damage profile, not about a failed control, and the
        # two were conflated in a label a reader sees before they see any number.
        tag = 'replicate' if r['replicate'] else ('' if r['informative'] else
                                                  'band ~ sham: early and late heads damage alike')
        print(f"      {r['model']:<20} band {r['band_floor']:.4f} / sham {r['sham_floor']:.4f}"
              f" = {r['ratio_k1']:6.2f}x  {tag}")
    print(f"      -> {A['ratio_min']:.1f}x-{A['ratio_max']:.1f}x over "
          f"{A['n_informative']} informative models")
    print(f"      baseline margins: " +
          '  '.join(f"{r['model']} {r['base_margin']:.3f}" for r in A['rows']) + "\n")
    if V:
        print("R1' changing ONLY the four answer nouns (Amendment 2)")
        for r in V:
            if r['k'] == 1:
                print(f"      {r['model']:<16} k=1   2 sd in the ORIGINAL vocabulary = "
                      f"{r['two_sd_original']:.3f} margin units  <- the floor the author's own "
                      f"prior effects are placed against")
        for r in V:
            print(f"      {r['model']:<16} k={r['k']:<3} raw sd {r['sd_pct']:+6.1f}%   "
                  f"floor {r['floor_pct']:+6.1f}%   baseline {r['base_old']:.3f}"
                  f" -> {r['base_new']:.3f}")
        print("      -> raw noise and the dimensionless floor can move in OPPOSITE directions\n")

    print("R2  how often does ablating a KNOWN mechanism move the outcome the wrong way?")
    for r in sorted(B['rows'], key=lambda r: -r['baseline_prob']):
        print(f"      {r['model']:<20} baseline p {r['baseline_prob']:.5f}  "
              f"{'valid  ' if r['valid'] else 'INVALID'}  effect {r['d_top']:+7.3f}  "
              f"sign {'correct' if r['sign_correct'] else '*** INVERTED ***'}")
    print(f"      -> {B['n_inverted']} of {B['n_valid']} valid cells inverted")
    hv = max(B['rows'], key=lambda r: abs(r['null_min']))
    print(f"      heaviest null tail: {hv['model']} min {hv['null_min']:.2f} "
          f"vs sd {hv['null_sd']:.3f} -- why percentiles, not sd\n")

    if D:
        t = D['two_point']
        print("R4  can the floor be predicted instead of measured?")
        print(f"      within a model: power law, R2 "
              f"{min(f['r2'] for f in D['within_model_powerlaw'].values()):.3f}-"
              f"{max(f['r2'] for f in D['within_model_powerlaw'].values()):.3f}")
        print(f"      two-point rule: {t['n_within_2x']} of {t['n_heldout']} held-out cells "
              f"within 2x, median {t['median_factor_error']:.2f}x")
        print(f"      across models : {D['verdict_across_models']} -- the pre-registered gate is "
              f"met by {D['gate_met_by']} of {D['feature_sweep_n']} admissible estimators\n")
    else:
        print("R4  not yet computed -- run  python3 R4_predictability/run.py\n")

    print("R5  does ablating at EVERY position make the effect easier to read?")
    for r in E['rows']:
        print(f"      {r['model']:<16} {r['readout']:<7} "
              f"2sd {r['read_2sd_final']:6.3f}->{r['read_2sd_all']:6.3f}   "
              f"p10p90 {r['read_w_final']:6.3f}->{r['read_w_all']:6.3f}   "
              f"{'WORSE' if r['read_2sd_all'] < r['read_2sd_final'] else 'better'}")
    print(f"      -> worse in {E['n_worse_2sd']} of {E['n_cells']} cells on the 2sd floor and "
          f"{E['n_worse_w']} of {E['n_cells']} on the p10-p90 floor")
    print(f"      |effect| at the final position spans {E['effect_scale_span']:.0f}x across "
          f"cells ({E['kl_effect_span']:.1f}x within the KL readout alone) -- "
          f"readability is a RATIO, not a size")
    print(f"      floor widens {E['widen_sd'][0]:.2f}-{E['widen_sd'][1]:.2f}x (2sd) / "
          f"{E['widen_w'][0]:.2f}-{E['widen_w'][1]:.2f}x (p10-p90); "
          f"|effect| changes {E['effect_change'][0]:.2f}-{E['effect_change'][1]:.2f}x")

    if S:
        print("\nR6  is the floor a property of ablation, or of ZEROING?  (amended statistic)")
        print(f"      {'model':<16} {'zero':>8}{'mean':>8}{'resample':>10}   "
              f"{'rr mean':>8}{'rr resamp':>10}   checks")
        for r in S['rows']:
            ck = ('CHECK1 ok' if r['check1'] else 'CHECK1 FAIL') + \
                 ('' if not r['dead_arms'] else f", dead: {','.join(r['dead_arms'])}")
            print(f"      {r['model']:<16} {r['read_zero']:>8.2f}{r['read_mean']:>8.2f}"
                  f"{r['read_resample']:>10.2f}   {r['rr_mean']:>8.2f}{r['rr_resample']:>10.2f}"
                  f"   {ck}")
        print(f"      readability = |positive control| / band sd, per arm")
        print(f"      median rr: mean {S['median_rr_mean']:.2f}x  "
              f"resample {S['median_rr_resample']:.2f}x  over {S['n_informative']} informative "
              f"cells; {S['n_valid_rounds']} of {len(S['rows'])} rounds fully valid")
        deg = [f"{r['model']}/{iv}" for r in S['rows'] for iv in ('mean', 'resample')
               if r[f'ratio_k1_degenerate_{iv}']]
        if deg:
            worst = S['sham_collapse_max']
            print(f"      pre-registered ratio_k1 DEGENERATE (sham sd collapses up to "
                  f"{worst:.0f}x) on: {', '.join(deg)} -- see AMENDMENT 1")

    if G:
        print("\nR6' the pre-registered separator: gentler intervention, or nearly the identity?")
        for r in G['rows']:
            print(f"      {r['model']:<16} displacement ||x-mean||/||x||  median {r['median']:.3f}"
                  f"  [p10 {r['p10']:.3f}, p90 {r['p90']:.3f}]  over {r['n_heads']:>3} band heads"
                  f"  -> {r['verdict']}")
        print(f"      mean-ablation displaces {G['displacement_pct_min']:.0f}-"
              f"{G['displacement_pct_max']:.0f}% of what zeroing displaces; a head's final-position"
              f" output is {G['item_independent_pct_min']:.0f}-"
              f"{G['item_independent_pct_max']:.0f}% item-independent")
        print(f"      {G['n_reaching_world_G']} of {len(G['rows'])} models reach the "
              f"pre-registered threshold for 'gentler' -- so that world is refused")

    if R:
        print("\nR7  at a FIXED displacement size, does the DIRECTION change readability?")
        print(f"      {'model':<16}{'zero':>7}{'mean':>7}{'shrink':>8}{'randdir':>9}   "
              f"{'rr shr':>7}{'rr rnd':>8}   match  checks")
        for r in R['rows']:
            ck = ('ok' if r['check2'] else 'CHECK2 FAIL') + \
                 ('' if not r['dead_arms'] else f" dead:{','.join(r['dead_arms'])}") + \
                 ('' if r['include'] else f" EXCLUDED:{','.join(r['include_fail'])}")
            print(f"      {r['model']:<16}{r['read_zero']:>7.2f}{r['read_mean']:>7.2f}"
                  f"{r['read_shrink']:>8.2f}{r['read_randdir']:>9.2f}   "
                  f"{r['rr_shrink']:>7.2f}{r['rr_randdir']:>8.2f}   "
                  f"{100*r['match_spread']:>4.2f}%  {ck}")
        print(f"      readability = |positive control| / band sd; rr is vs the `mean` arm")
        print(f"      mean arm as a fraction of the SAME model's zero arm: "
              f"{out_mz(R)}  -> the exclusion threshold crosses a smooth quantity")
        print(f"      displacement matching worst spread {R['worst_match_spread_pct']:.2f}% "
              f"across all cells; shrink overshoot past origin: {R['total_overshoot']}")
        if R.get('gate'):
            print(f"      median rr: shrink {R['median_rr_shrink']:.2f}x  "
                  f"randdir {R['median_rr_randdir']:.2f}x  over {R['n_included']} included cells"
                  f"  -> {R['gate']}")
            print(f"      readability order low->high: "
                  f"{' < '.join(R['readability_order_low_to_high'])}"
                  f"  -- same order in {R['n_cells_matching_order']} of "
                  f"{R['n_cells_total']} cells (within-cell, no ratio, no inclusion rule)")

    if args.check:
        claims = [
            ('R1 ratio min', A['ratio_min'], 2.74, 0.01),
            ('R1 ratio max', A['ratio_max'], 12.27, 0.01),
            ('R1 informative models', A['n_informative'], 4, 0),
            ('R2 valid cells', B['n_valid'], 4, 0),
            ('R2 inverted', B['n_inverted'], 0, 0),
            ('R5 cells', E['n_cells'], 6, 0),
            ('R5 worse on 2sd', E['n_worse_2sd'], 6, 0),
            ('R5 worse on p10-p90', E['n_worse_w'], 6, 0),
        ]
        if D:
            t = D['two_point']
            claims += [('R4 two-point within 2x', t['n_within_2x'], 12, 0),
                       ('R4 two-point median', t['median_factor_error'], 1.15, 0.01),
                       ('R4 gate met by', D['gate_met_by'], 60, 0)]
        bad = [(n, g, w) for n, g, w, tol in claims if abs(g - w) > tol]
        print()
        for n, g, w in bad:
            print(f"  STALE: {n} is {g}, the README says {w}")
        if bad:
            return 1
        print(f"  README check: {len(claims)} numbers reproduce from the checked-in results")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
