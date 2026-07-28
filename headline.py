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


def r2():
    rows = []
    for name, d in load('R2_inversion/results/*.json').items():
        # Older result files predate the validity key; recomputing it from the logprob rather than
        # defaulting it keeps a missing key from silently reading as 'valid'.
        bp = d.get('baseline_prob', math.exp(d['baseline_logprob']))
        rows.append({'model': name, 'baseline_prob': bp, 'valid': bp > 0.1,
                     'sign_correct': bool(d['sign_correct']), 'd_top': d['d_top']})
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
                'mech_attn': d['mechanism_attn'], 'mechanism': d['mechanism'],
            })
    return {'rows': rows, 'n_cells': len(rows),
            'n_worse_2sd': sum(r['read_2sd_all'] < r['read_2sd_final'] for r in rows),
            'n_worse_w': sum(r['read_w_all'] < r['read_w_final'] for r in rows),
            'widen_sd': (min(r['floor_widen_sd'] for r in rows),
                         max(r['floor_widen_sd'] for r in rows)),
            'widen_w': (min(r['floor_widen_w'] for r in rows),
                        max(r['floor_widen_w'] for r in rows)),
            'effect_change': (min(r['effect_change'] for r in rows),
                              max(r['effect_change'] for r in rows))}


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
    D = r4()

    if args.json:
        print(json.dumps({'r1': A, 'r2': B, 'r4': D, 'r5': E}, indent=2, default=float))
        return 0

    print("R1  how much of an ablation effect is WHICH component rather than THAT one?")
    for r in sorted(A['rows'], key=lambda r: r['ratio_k1']):
        tag = 'replicate' if r['replicate'] else ('' if r['informative'] else
                                                  'EXCLUDED by its own sham control')
        print(f"      {r['model']:<20} band {r['band_floor']:.4f} / sham {r['sham_floor']:.4f}"
              f" = {r['ratio_k1']:6.2f}x  {tag}")
    print(f"      -> {A['ratio_min']:.1f}x-{A['ratio_max']:.1f}x over "
          f"{A['n_informative']} informative models\n")

    print("R2  how often does ablating a KNOWN mechanism move the outcome the wrong way?")
    for r in sorted(B['rows'], key=lambda r: -r['baseline_prob']):
        print(f"      {r['model']:<20} baseline p {r['baseline_prob']:.5f}  "
              f"{'valid  ' if r['valid'] else 'INVALID'}  effect {r['d_top']:+7.3f}  "
              f"sign {'correct' if r['sign_correct'] else '*** INVERTED ***'}")
    print(f"      -> {B['n_inverted']} of {B['n_valid']} valid cells inverted\n")

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
    print(f"      floor widens {E['widen_sd'][0]:.2f}-{E['widen_sd'][1]:.2f}x (2sd) / "
          f"{E['widen_w'][0]:.2f}-{E['widen_w'][1]:.2f}x (p10-p90); "
          f"|effect| changes {E['effect_change'][0]:.2f}-{E['effect_change'][1]:.2f}x")

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
