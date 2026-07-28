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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


# A REFUSAL IS NOT A CELL, AND THE GATE CRASHED ON ITS FIRST ONE. Task 58 refused phi-3.5-mini
# correctly -- its tokenizer scores `pine` on the fragment "p" and `frost` on "fro", so the margin
# is not about the answer -- and wrote a REFUSED artifact into the results directory, exactly as
# designed. `load()` then handed that artifact to r10(), which asked for `d['layers']` and died.
# THE REFUSAL MECHANISM, WORKING AS INTENDED, BROKE `make verify` FOR EVERY FUTURE CLONE.
# Refusals are skipped here rather than in each consumer -- a guard that has to be remembered in
# eleven places is a guard that will be missing from the twelfth -- and the count is RETURNED, not
# swallowed, because a silently dropped refusal is a measurement that looks like it never happened.
REFUSALS: dict[str, list[str]] = {}


def load(pattern):
    out = {}
    for f in sorted(glob.glob(str(HERE / pattern))):
        d = json.load(open(f))
        if str(d.get('verdict', '')).startswith('REFUSED'):
            REFUSALS.setdefault(pattern, []).append(
                f"{d.get('model', '?')}: {d.get('verdict')} -- {d.get('why', '')[:110]}")
            continue
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


def r1_prior_effects():
    """The eight single-head effects the front page's first paragraph is about.

    Asserted in prose since the repository was published and shown nowhere -- an outside reader's
    finding, and a fair one: the claim that made this work worth publishing had no object behind it
    here. The set is E132b's own `drop` field, so it is defined by the source experiment rather than
    chosen to fit the floor.
    """
    p = HERE / 'R1_noise_floor' / 'results' / 'prior_effects' / \
        'e132b_eight_single_head_effects.json'
    return json.load(open(p)) if p.exists() else None


def cross_round_scale():
    """R1 and R2 on ONE scale, matched at k=5: why did the two rounds disagree?

    R5 was built to answer this and returned MIXED over three candidate factors -- readout, site,
    mechanism size. None of them is the answer. Put both rounds on the readout's DYNAMIC RANGE
    (baseline -> where the model sits with the mechanism gone) and the effects are comparable while
    the FLOORS differ by 5-50x.

    The floor for margin is exactly 0 (indifference among the four rooms). For induction logprob it
    is uniform chance over the sampled id range -- an ASSUMPTION, stated, because R2 draws tokens
    uniformly from ~39k ids so that is where a model with no induction sits.
    """
    import math
    CH = math.log(1 / 39000)
    out = {'chance_logprob': CH, 'r1': [], 'r2': []}
    for name, d in load('R1_noise_floor/results/*.json').items():
        c = d['cells'].get('band_k5')
        if not c:
            continue
        rng = abs(d['base_margin'])
        out['r1'].append({'model': name, 'range': rng, 'noise_pct': 100 * 2 * c['sd'] / rng})
    sn = r1_set_null()
    if sn:
        rng = sn['base_margin']; sd2 = 2 * sn['null']['sd']
        for k in ('COPY', 'READ'):
            e = abs(sn['sets'][k]['drop'])
            out['r1'].append({'model': f'qwen2.5-1.5b {k} set (orig vocab)', 'range': rng,
                              'effect_pct': 100 * e / rng, 'noise_pct': 100 * sd2 / rng,
                              'eff_over_noise': e / sd2})
    for name, d in load('R2_inversion/results/*.json').items():
        b = d['baseline_logprob']
        if math.exp(b) <= 0.1:
            continue
        rng = b - CH; e = abs(d['d_top']); sd2 = 2 * d['null']['sd']
        out['r2'].append({'model': name, 'range': rng, 'effect_pct': 100 * e / rng,
                          'noise_pct': 100 * sd2 / rng, 'eff_over_noise': e / sd2})
    eff = [r['effect_pct'] for r in out['r1'] + out['r2'] if 'effect_pct' in r]
    noi = [r['noise_pct'] for r in out['r1'] + out['r2']]
    out['effect_pct_range'] = [min(eff), max(eff)]
    out['noise_pct_range'] = [min(noi), max(noi)]
    out['noise_spread_x'] = max(noi) / min(noi)
    return out


def r10():
    """Every head ablated once, no sampling anywhere, in the ORIGINAL vocabulary.

    At k=1 inside a layer there is nothing to sample -- there are only NH heads -- so thirty draws
    would be sampling with replacement from twelve objects. This measures all of them, which makes
    every number here exact and lets each published effect be placed against ITS OWN LAYER's floor
    rather than one pooled over fourteen.
    """
    import re as _re
    out = {}
    for name, d in load('R10_exhaustive/results/*.json').items():
        layers = {int(k): v for k, v in d['layers'].items()}
        rows = []
        pe = r1_prior_effects()
        if pe:
            pool = pe['floor_2sd_same_vocabulary']
            for h, e in sorted(pe['effects'].items(), key=lambda kv: -kv[1]['abs']):
                L = int(_re.match(r'L(\d+)H', h).group(1))
                if L not in layers:
                    continue
                own = 2 * layers[L]['sd']
                rows.append({'head': h, 'drop': e['drop'], 'layer': L, 'own_floor_2sd': own,
                             'x_own': e['abs'] / own, 'x_pooled': e['abs'] / pool,
                             'inside_own': e['abs'] < own, 'inside_pooled': e['abs'] < pool})
        out[name] = {
            'n_items': d['n_items'], 'base_margin': abs(d['base_margin']),
            'sampling': d.get('sampling'), 'rooms': d['rooms'],
            'layer_sd': {L: layers[L]['sd'] for L in sorted(layers)},
            'layer_2sd': {L: 2 * layers[L]['sd'] for L in sorted(layers)},
            'per_head_L22': layers[22]['per_head'] if 22 in layers else None,
            'effects_vs_own_layer': rows,
            'n_inside_own': sum(r['inside_own'] for r in rows),
            'n_inside_pooled': sum(r['inside_pooled'] for r in rows),
            'spearman_rho_layer_sd': d['spearman_rho_layer_sd'],
            # Emitted so the number can be QUOTED while being REFUSED. R10's own gate reports
            # BAND-IS-EXCEPTIONAL from this excess, computed by extrapolating the sham half to the
            # band's depth -- the estimator R9 established is unfit. A refused verdict still has to
            # carry its number, or the refusal cannot be checked either.
            'refused_gate_excess': d.get('band_excess_over_trend'),
            'refused_gate_verdict': d.get('verdict'),
        }
    return out or None


def _spearman(a, b):
    rk = lambda v: [sorted(v).index(x) for x in v]  # noqa: E731
    x, y = rk(a), rk(b)
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    num = sum((i - mx) * (j - my) for i, j in zip(x, y))
    den = math.sqrt(sum((i - mx) ** 2 for i in x) * sum((j - my) ** 2 for j in y))
    return num / den if den else float('nan')


def centred_null():
    """THE NULL IS NOT CENTRED AT ZERO, and every verdict in this repository assumed it was.

    `distinguishable` has always been `|drop| > 2*sd`. That statistic implicitly places the null at
    zero. Measured: the studied band's mean drop is **+0.0479**, which is 0.20 sd -- ablating a
    random late-layer head IMPROVES the correct-answer margin more often than it hurts, 100 of 168.
    A head that does nothing therefore sits 0.0479 AWAY from the null's centre, and the question
    "is this head unusual among random heads" is `|drop - mean| > 2*sd`, not `|drop| > 2*sd`.

    IT CHANGES THE HEADLINE COUNT. L16H3 goes from 0.96x (inside) to 1.06x (CLEARS), so the correct
    figure is 1 of 8, not 0 of 8. The proven copy head moves the other way, 0.27x -> 0.37x, and
    stays far inside. Seven of eight are unaffected in substance.

    AND THE SHIFT IS NOT AN INTERVENTION ARTIFACT, which had to be checked before the centred
    statistic could be trusted. If zero-ablating ANY head nudged this readout upward, the +0.0479
    would be a property of the operation rather than of the band. The sham band (L0-7) is
    essentially centred -- +0.0040, 0.10 sd, a 51/45 sign split -- while the studied band is at 0.20
    sd with 100/68. The offset grows with depth alongside the spread; it is a fact about the late
    band, not about zeroing.
    """
    p = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    pe = r1_prior_effects()
    if not (p.exists() and pe):
        return None
    t = json.load(open(p))
    L = {int(k): v for k, v in t['layers'].items()}

    def stats(lo, hi):
        v = [x for k in range(lo, hi + 1) for x in L[k]['per_head'].values()]
        m = sum(v) / len(v)
        sd = math.sqrt(sum((y - m) ** 2 for y in v) / (len(v) - 1))
        return {'n': len(v), 'mean': m, 'sd': sd, 'mean_over_sd': m / sd,
                'n_positive': sum(1 for x in v if x > 0),
                'n_negative': sum(1 for x in v if x < 0)}

    bands = {'sham_L0_7': stats(0, 7), 'mid_L8_13': stats(8, 13),
             'studied_L14_27': stats(14, 27), 'all_L0_27': stats(0, 27)}
    b = bands['studied_L14_27']
    mu, two_sd = b['mean'], 2 * b['sd']
    rows = [{'head': h, 'drop': e['drop'],
             'x_uncentred': e['abs'] / two_sd,
             'x_centred': abs(e['drop'] - mu) / two_sd}
            for h, e in sorted(pe['effects'].items(), key=lambda kv: -kv[1]['abs'])]
    allb = [x for k in range(14, 28) for x in L[k]['per_head'].values()]
    return {'bands': bands, 'null_mean': mu, 'two_sd': two_sd, 'effects': rows,
            'n_clear_uncentred': sum(r['x_uncentred'] > 1 for r in rows),
            'n_clear_centred': sum(r['x_centred'] > 1 for r in rows),
            'band_heads_clear_uncentred': sum(1 for v in allb if abs(v) > two_sd),
            'band_heads_clear_centred': sum(1 for v in allb if abs(v - mu) > two_sd)}


def reference_class():
    """Does the CHOICE of null decide the verdict? Pre-registered before running: >=4 of 8 clearing
    the sham-band floor would mean the reference class is doing the work. Observed 3. IT DID NOT FIRE.

    But the shape is the result, and it is sharper than the threshold it was testing. The studied
    band's floor is 0.4870; the SHAM band's (L0-7, heads presumed not to implement this task) is
    0.0792 -- a 6.15x difference from reference class alone. Against the sham floor three of the
    eight clear, including L22H7 at 1.66x.

    AND 78 OF THE 168 BAND HEADS -- 46% -- ALSO CLEAR IT. So clearing the sham floor is not a mark
    of distinction; it is what a coin-flip's worth of late-layer heads do. Combined with R9's result
    that the floor GROWS with depth, the reading is exact:

        L22H7 is distinguishable from an EARLY-layer head and indistinguishable from a LATE-layer
        one. Its ablation number therefore carries DEPTH information, not ROLE information.

    Both floors are defensible and they answer different questions. The verdict on the front page is
    against the band floor -- "is this head special among the heads I might have picked instead?" --
    and it stands at 0 of 8. The sham comparison answers "is this head in the second half of the
    network?", and the eight answer that the same way 46% of the band does.
    """
    p = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    pe = r1_prior_effects()
    if not (p.exists() and pe):
        return None
    t = json.load(open(p))
    L = {int(k): v for k, v in t['layers'].items()}

    def sd(xs):
        m = sum(xs) / len(xs)
        return math.sqrt(sum((y - m) ** 2 for y in xs) / (len(xs) - 1))

    def pool(lo, hi):
        return [v for x in range(lo, hi + 1) for v in L[x]['per_head'].values()]

    band, sham = pool(14, 27), pool(0, 7)
    fb, fs = 2 * sd(band), 2 * sd(sham)
    mus = sum(sham) / len(sham)
    mub = sum(band) / len(band)
    # CENTRED ON EACH NULL'S OWN MEAN. The sham null is nearly centred (+0.0040) so these barely
    # move -- 3 of 8 either way -- which is worth reporting: it shows the centring correction is
    # not selecting the comparison that flatters, it is applying one rule everywhere.
    rows = [{'head': h, 'drop': e['drop'],
             'x_band': abs(e['drop'] - mub) / fb, 'x_sham': abs(e['drop'] - mus) / fs,
             'x_sham_UNCENTRED': e['abs'] / fs,
             'clears_sham': abs(e['drop'] - mus) > fs}
            for h, e in sorted(pe['effects'].items(), key=lambda kv: -kv[1]['abs'])]
    return {'band_floor': fb, 'sham_floor': fs, 'ratio': fb / fs,
            'n_band': len(band), 'n_sham': len(sham),
            'n_clear_band': sum(r['x_band'] > 1 for r in rows),
            'n_clear_sham': sum(r['clears_sham'] for r in rows),
            'preregistered_threshold': 4, 'fired': sum(r['clears_sham'] for r in rows) >= 4,
            # THE PROFILE, because "the second half of the network" was too coarse and was
            # written one step before this measured it. Clearing rate rises with depth (Spearman
            # +0.645 over 28 layers) but NOT monotonically: it peaks at 83% in L16-L17 and falls
            # back to 8-17% by L25/L27, so L25 clears LESS often than L11. A hump, not a half.
            # CENTRED on the sham null's own mean (+0.003977), per the rule applied everywhere on
            # 2026-07-28. The uncentred form is kept beside it because R12's committed thresholds
            # were derived from it, and a pre-registration must be shown to survive a statistic
            # change rather than quietly re-derived under the new one.
            'clearing_rate_by_layer': {x: sum(1 for v in L[x]['per_head'].values()
                                              if abs(v - mus) > fs) / len(L[x]['per_head'])
                                       for x in sorted(L)},
            'clearing_rate_by_layer_UNCENTRED': {
                x: sum(1 for v in L[x]['per_head'].values() if abs(v) > fs)
                / len(L[x]['per_head']) for x in sorted(L)},
            'clearing_centroid_layer_UNCENTRED': (
                sum(x * sum(1 for v in L[x]['per_head'].values() if abs(v) > fs)
                    / len(L[x]['per_head']) for x in sorted(L)) /
                sum(sum(1 for v in L[y]['per_head'].values() if abs(v) > fs)
                    / len(L[y]['per_head']) for y in sorted(L))),
            # PERCENT AS WELL AS FRACTION, because the prose quotes percentages and 0.5833 does
            # not back "58%". A unit mismatch between generator and page is the same defect class
            # as a hand-computed 2*sd: the number is right and nothing can check it.
            'clearing_pct_by_layer': {x: 100 * sum(1 for v in L[x]['per_head'].values()
                                                   if abs(v) > fs) / len(L[x]['per_head'])
                                      for x in sorted(L)},
            'spearman_layer_vs_clearing_rate': _spearman(
                sorted(L), [sum(1 for v in L[x]['per_head'].values() if abs(v) > fs)
                            / len(L[x]['per_head']) for x in sorted(L)]),
            # THE QUANTITIES R12'S PRE-REGISTRATION PREDICTS FROM, emitted so its thresholds are
            # machine-checkable rather than editable prose. Writing them out caught an arithmetic
            # slip in the pre-registration itself: 0.644 x 35 is 22.54, not the 20.5 first written.
            # 20.5 is the MIDPOINT between the two worlds' predictions and is the right window edge;
            # the annotation calling it the relative prediction was wrong.
            'clearing_centroid_layer': (
                sum(x * sum(1 for v in L[x]['per_head'].values() if abs(v - mus) > fs)
                    / len(L[x]['per_head']) for x in sorted(L)) /
                sum(sum(1 for v in L[y]['per_head'].values() if abs(v - mus) > fs)
                    / len(L[y]['per_head']) for y in sorted(L))),
            'n_layers': len(L),
            'peak_layers': [x for x in sorted(L)
                            if sum(1 for v in L[x]['per_head'].values() if abs(v) > fs)
                            / len(L[x]['per_head']) == max(
                                sum(1 for v in L[y]['per_head'].values() if abs(v) > fs)
                                / len(L[y]['per_head']) for y in L)],
            # AND WHERE THE COPY HEAD SITS INSIDE ITS OWN LAYER'S CLEARING SET.
            'L22_clearing': sorted(
                [{'head': f'L22H{h}', 'drop': v}
                 for h, v in L[22]['per_head'].items() if abs(v) > fs],
                key=lambda r: -abs(r['drop'])),
            'copy_head_rank_in_its_layer_clearing_set': sorted(
                [abs(v) for v in L[22]['per_head'].values() if abs(v) > fs],
                reverse=True).index(abs(L[22]['per_head']['7'])) + 1,
            'n_published_in_peak_layers': sum(
                1 for h in pe['effects']
                if int(h[1:h.index('H')]) in (16, 17)),
            'band_heads_clearing_sham': sum(1 for v in band if abs(v) > fs),
            # For a 36-layer model: ABSOLUTE predicts the same centroid LAYER, RELATIVE the same
            # DEPTH FRACTION. At 28 layers those coincide; at 36 they are ~5 layers apart, which is
            # why the second model separates worlds the first cannot.
            'clearing_centroid_depth_fraction': (
                sum(x * sum(1 for v in L[x]['per_head'].values() if abs(v - mus) > fs)
                    / len(L[x]['per_head']) for x in sorted(L)) /
                sum(sum(1 for v in L[y]['per_head'].values() if abs(v - mus) > fs)
                    / len(L[y]['per_head']) for y in sorted(L)) / (len(L) - 1)),
            # R12'S PRE-REGISTERED WINDOW EDGES, emitted so they are checked constants rather than
            # prose a later edit could move. They are half a layer either side of the midpoint
            # between the two worlds' predictions (17.39 and 22.54).
            'r12_window_absolute_max': 19.5, 'r12_window_relative_min': 20.5,
            # THE MIDPOINTS, both forms. The window edges sit half a layer either side of the
            # midpoint, so a reader can check that the committed edges still straddle it after the
            # statistic changed -- which is the whole content of R12's addendum.
            'clearing_centroid_depth_fraction_UNCENTRED': (
                sum(x * sum(1 for v in L[x]['per_head'].values() if abs(v) > fs)
                    / len(L[x]['per_head']) for x in sorted(L)) /
                sum(sum(1 for v in L[y]['per_head'].values() if abs(v) > fs)
                    / len(L[y]['per_head']) for y in sorted(L)) / (len(L) - 1)),
            'r12_midpoint_uncentred': (
                sum(x * sum(1 for v in L[x]['per_head'].values() if abs(v) > fs)
                    / len(L[x]['per_head']) for x in sorted(L)) /
                sum(sum(1 for v in L[y]['per_head'].values() if abs(v) > fs)
                    / len(L[y]['per_head']) for y in sorted(L))) * (1 + 35 / (len(L) - 1)) / 2,
            'r12_relative_prediction_uncentred': (
                sum(x * sum(1 for v in L[x]['per_head'].values() if abs(v) > fs)
                    / len(L[x]['per_head']) for x in sorted(L)) /
                sum(sum(1 for v in L[y]['per_head'].values() if abs(v) > fs)
                    / len(L[y]['per_head']) for y in sorted(L))) * 35 / (len(L) - 1),
            'r12_midpoint_centred': (
                sum(x * sum(1 for v in L[x]['per_head'].values() if abs(v - mus) > fs)
                    / len(L[x]['per_head']) for x in sorted(L)) /
                sum(sum(1 for v in L[y]['per_head'].values() if abs(v - mus) > fs)
                    / len(L[y]['per_head']) for y in sorted(L))) * (1 + 35 / (len(L) - 1)) / 2,
            'predicted_centroid_absolute_36L': (
                sum(x * sum(1 for v in L[x]['per_head'].values() if abs(v - mus) > fs)
                    / len(L[x]['per_head']) for x in sorted(L)) /
                sum(sum(1 for v in L[y]['per_head'].values() if abs(v - mus) > fs)
                    / len(L[y]['per_head']) for y in sorted(L))),
            'predicted_centroid_relative_36L': (
                sum(x * sum(1 for v in L[x]['per_head'].values() if abs(v - mus) > fs)
                    / len(L[x]['per_head']) for x in sorted(L)) /
                sum(sum(1 for v in L[y]['per_head'].values() if abs(v - mus) > fs)
                    / len(L[y]['per_head']) for y in sorted(L)) / (len(L) - 1) * 35),
            'pct_band_clearing_sham': 100 * sum(1 for v in band if abs(v) > fs) / len(band),
            'rows': rows}


def power():
    """THE POSITIVE CONTROL FOR THE PROJECT'S CENTRAL NULL, which had never been stated.

    The headline is a measured ZERO: none of the eight published effects is distinguishable from a
    random head. This repository's own rule -- **a measured 0 is INADMISSIBLE until that same
    instrument has passed a positive control** -- was never applied to it. A zero from an instrument
    that has never returned non-zero is silence, not an acquittal.

    It passes, and the control was sitting in the same run. NINE heads are BOTH resolvable at 2
    sigma AND beyond the exhaustive floor, at 1.18x to 2.54x the floor and 2.5x to 22.1x their own
    SEM. The instrument returns non-zero on the same data that returns zero for the eight.

    AND THE DESIGN HAS THE DYNAMIC RANGE. For 167 of 168 heads the floor EXCEEDS that head's own
    measurement noise, so "measurable and distinguishable" is achievable in principle for nearly
    every head. The exception is named rather than averaged away: L26H7's 2*SEM is 0.4991 against a
    floor of 0.4870, so its own item-to-item variance exceeds the entire between-head spread and NO
    VERDICT about it is possible. One head, stated, not swept in.

    THE NULL IS ALSO NOT A LANDSLIDE, and saying so is part of reporting it. The largest published
    effect reaches 96% of the threshold. Seven of the eight sit at 0.27x or below; one just missed.
    """
    a = HERE / 'R11_instrument_noise' / 'results' / 'r11_itemsA_qwen2.5-1.5b.json'
    pe = r1_prior_effects()
    if not (a.exists() and pe):
        return None
    import re as _re
    A = json.load(open(a))
    L = {int(k): v for k, v in A['layers'].items()}
    band = [(x, int(h)) for x in range(14, 28) for h in L[x]['per_head']]
    d = {k: L[k[0]]['per_head'][str(k[1])] for k in band}
    sem = {k: L[k[0]]['per_head_sem'][str(k[1])] for k in band}

    def sd(xs):
        m = sum(xs) / len(xs)
        return math.sqrt(sum((y - m) ** 2 for y in xs) / (len(xs) - 1))

    floor = 2 * sd(list(d.values()))
    both = [k for k in band if abs(d[k]) > floor and abs(d[k]) > 2 * sem[k]]
    undecidable = [k for k in band if 2 * sem[k] >= floor]
    eight = {(int(m.group(1)), int(m.group(2)))
             for h in pe['effects'] if (m := _re.match(r'L(\d+)H(\d+)', h))}
    ts = sorted(2 * sem[k] for k in band)
    return {
        'floor': floor, 'n_heads': len(band),
        'two_sem_min': ts[0], 'two_sem_median': ts[len(ts) // 2], 'two_sem_max': ts[-1],
        'n_with_room': len(band) - len(undecidable),
        'pct_with_room': 100 * (len(band) - len(undecidable)) / len(band),
        'undecidable': [{'head': f'L{x}H{h}', 'drop': d[(x, h)], 'two_sem': 2 * sem[(x, h)]}
                        for x, h in undecidable],
        'n_positive_control': len(both),
        'positive_control': [{'head': f'L{x}H{h}', 'drop': d[(x, h)],
                              'x_floor': abs(d[(x, h)]) / floor,
                              'x_own_sem': abs(d[(x, h)]) / (2 * sem[(x, h)])}
                             for x, h in sorted(both, key=lambda k: -abs(d[k]))],
        'largest_published_pct_of_threshold': 100 * max(abs(d[k]) for k in eight) / floor,
        'second_largest_x_floor': sorted((abs(d[k]) / floor for k in eight), reverse=True)[1],
    }


def r11():
    """R11 -- the instrument's own noise, MEASURED, and the ranking's stability across item sets.

    Two exhaustive runs on DISJOINT item sets (seeds 3000..3400 and 3400..3800), with the runner
    finally storing `per_head_sem = sd_over_items / sqrt(n)` -- a quantity every previous run
    computed and threw away. Three readings, all fixed in PREREGISTRATION.md before either job left
    the queue, plus the rank-stability question the depth control could not answer.

    READING 1 REPLACES A WITHDRAWN BOUND AND REVERSES ITS ANSWER. The quiet-layer bound published
    two steps earlier said 3 of 8 effects were "measurable"; it was withdrawn because a quiet layer
    is quiet in both terms. Measured directly: **8 of 8 are resolvable at 2 sigma**, from 1.27x
    (L22H7) to 13.97x (L16H3). The bound was wrong in method AND in answer.

    So the repository's finding reaches its sharpest form, and both halves are now measurements:
        EVERY one of the eight is RESOLVABLE      8 of 8, |drop| > 2*SEM
        NOT ONE is DISTINGUISHABLE from a random head   0 of 8, |drop| < the exhaustive floor
    The measurement was never the problem. Being measurable and being special are different
    properties, and only the second one failed.
    """
    a = HERE / 'R11_instrument_noise' / 'results' / 'r11_itemsA_qwen2.5-1.5b.json'
    b = HERE / 'R11_instrument_noise' / 'results' / 'r11_itemsB_qwen2.5-1.5b.json'
    an = HERE / 'R11_instrument_noise' / 'results' / 'r11_analysis.json'
    pe = r1_prior_effects()
    if not (a.exists() and b.exists() and an.exists() and pe):
        return None
    import re as _re
    A, B = json.load(open(a)), json.load(open(b))
    LA = {int(k): v for k, v in A['layers'].items()}
    LB = {int(k): v for k, v in B['layers'].items()}
    band = [(x, int(h)) for x in range(14, 28) for h in LA[x]['per_head']]
    dA = {(x, h): LA[x]['per_head'][str(h)] for x, h in band}
    dB = {(x, h): LB[x]['per_head'][str(h)] for x, h in band}
    # THE CENTRING WAS NEVER APPLIED HERE, AND THE FRONT PAGE'S RANKS ARE CENTRED. `-abs(dA[k])`
    # places the null at zero -- the same defect corrected in R1 and again in R2 (D75), a THIRD
    # instance. It matters: uncentred, L22H7 moves 56 -> 96; CENTRED, which is what the front page
    # reports, it moves 41 -> 160, the largest move of all 168. So the stability claim published in
    # this round was computed on a ranking the repository does not use. Both are emitted now, and
    # the CENTRED one is primary because it is the one that validates a published number.
    muA = sum(dA.values()) / len(dA)
    muB = sum(dB.values()) / len(dB)
    oA = sorted(band, key=lambda k: -abs(dA[k] - muA))
    oB = sorted(band, key=lambda k: -abs(dB[k] - muB))
    rA = {k: i for i, k in enumerate(oA, 1)}
    rB = {k: i for i, k in enumerate(oB, 1)}
    uA = {k: i for i, k in enumerate(sorted(band, key=lambda k: -abs(dA[k])), 1)}
    uB = {k: i for i, k in enumerate(sorted(band, key=lambda k: -abs(dB[k])), 1)}
    eight = {(int(m.group(1)), int(m.group(2))): h
             for h in pe['effects'] if (m := _re.match(r'L(\d+)H(\d+)', h))}
    semA = {(x, int(h)): v for x, L in LA.items() for h, v in L['per_head_sem'].items()}
    rows = [{'head': eight[k], 'drop': dA[k], 'two_sem': 2 * semA[k],
             'ratio': abs(dA[k]) / (2 * semA[k]),
             'rank_A': rA[k], 'rank_B': rB[k], 'rank_move': rA[k] - rB[k]}
            for k in sorted(eight, key=lambda k: rA[k])]
    semB = {(x, int(h)): v for x, L in LB.items() for h, v in L['per_head_sem'].items()}
    rows_b = [{'head': eight[k], 'drop': dB[k], 'two_sem': 2 * semB[k],
               'ratio': abs(dB[k]) / (2 * semB[k])}
              for k in sorted(eight, key=lambda k: rA[k])]
    band_ratio_a = [abs(dA[k]) / (2 * semA[k]) for k in band]
    band_ratio_b = [abs(dB[k]) / (2 * semB[k]) for k in band]
    n = len(band)
    mx = sum(rA[k] for k in band) / n
    my = sum(rB[k] for k in band) / n
    rho = (sum((rA[k] - mx) * (rB[k] - my) for k in band) /
           math.sqrt(sum((rA[k] - mx) ** 2 for k in band) *
                     sum((rB[k] - my) ** 2 for k in band)))
    an = json.load(open(an))
    worst = max(rows, key=lambda r: abs(r['rank_move']))
    # THE NOMINAL COVERAGE OF THE BAND THE AGREEMENT RATE IS COMPARED AGAINST. Emitted rather
    # than written into the prose as "~95%", because a theoretical constant quoted from memory is
    # still a number with no generator -- and this one is 95.45, not 95.
    nominal = 100.0 * math.erf(2 / math.sqrt(2))
    return {'nominal_coverage_2sigma_pct': nominal, 'n_items_A': A['n_items'], 'n_items_B': B['n_items'], 'n_band_heads': n,
            'n_resolvable': an['n_measurable'], 'n_defined': an['n_defined'],
            'agree_within_sem': an['agree_within_sem'], 'n_band_pairs': an['n_band_pairs'],
            'agree_pct': an['agree_pct'],
            'floor_A': an['floor_A'], 'floor_B': an['floor_B'],
            'floor_divergence_pct': an['floor_divergence_pct'],
            'kill_threshold_pct': an['kill_threshold_pct'], 'verdict': an['verdict'],
            'rank_spearman_A_vs_B': rho,
            'centring_muA': muA, 'centring_muB': muB,
            'rank_spearman_uncentred': _spearman([uA[k] for k in band], [uB[k] for k in band]),
            'rms_disp_centred': math.sqrt(sum((rA[k] - rB[k]) ** 2 for k in band) / len(band)),
            'rms_disp_uncentred': math.sqrt(sum((uA[k] - uB[k]) ** 2 for k in band) / len(band)),
            'L22H7_centred_A': rA[(22, 7)], 'L22H7_centred_B': rB[(22, 7)],
            'L22H7_uncentred_A': uA[(22, 7)], 'L22H7_uncentred_B': uB[(22, 7)],
            'worst_mover_centred': (lambda w: {'head': f'L{w[0]}H{w[1]}',
                                               'move': rA[w] - rB[w]})(
                max(band, key=lambda k: abs(rA[k] - rB[k]))),
            'worst_mover_uncentred': (lambda w: {'head': f'L{w[0]}H{w[1]}',
                                                 'move': uA[w] - uB[w]})(
                max(band, key=lambda k: abs(uA[k] - uB[k]))),
            'top9_overlap_across_item_sets': len(set(oA[:9]) & set(oB[:9])),
            'published_in_B_top9': sum(1 for k in oB[:9] if k in eight),
            # THE ONE HEAD THAT MOVES. Every other published head shifts by <=5 places of 168;
            # the independently proven copy head shifts 40, and reading 2 independently flags it as
            # the worst SEM-vs-disagreement case in the band. A copy head's contribution depends on
            # WHICH object is being copied, so item-dependence is what it should look like -- its
            # instability is evidence FOR item-dependent machinery, not against it.
            'least_stable_published_head': worst['head'],
            'least_stable_rank_move': worst['rank_move'],
            # DOES THE RESOLVABILITY VERDICT ITSELF REPLICATE? `8 of 8 resolvable` was computed on
            # the PUBLISHED item set only, and stated without that scope. On the disjoint set it is
            # 7 of 8: L22H7 goes 1.27 -> 0.57 and flips. Every other head is stable and far above 1,
            # and across all 168 band heads the two runs agree on 157 verdicts with Spearman
            # +0.9825 -- so the instrument is reliable and this ONE head is not.
            'n_resolvable_B': sum(1 for r in rows_b if r['ratio'] > 1),
            'resolvable_verdicts_agree': sum(1 for a, b in zip(rows, rows_b)
                                             if (a['ratio'] > 1) == (b['ratio'] > 1)),
            'band_resolvable_A': sum(1 for v in band_ratio_a if v > 1),
            'band_resolvable_B': sum(1 for v in band_ratio_b if v > 1),
            'band_verdicts_agree': sum(1 for a, b in zip(band_ratio_a, band_ratio_b)
                                       if (a > 1) == (b > 1)),
            'band_ratio_spearman': _spearman(band_ratio_a, band_ratio_b),
            # AS A PERCENTAGE TOO, because the prose quotes one and 157/168 does not back "93.5%".
            'band_verdicts_agree_pct': 100 * sum(1 for a, b in zip(band_ratio_a, band_ratio_b)
                                                 if (a > 1) == (b > 1)) / len(band_ratio_a),
            'effects_B': rows_b,
            'effects': rows}


def adversary_scoring():
    """SCORE THE ADVERSARY-PREDICTION FILE AGAINST THE DEFECTS FOUND AFTER IT WAS WRITTEN.

    ADVERSARY.md says a row not raised is a MISS, and that "a finding absent from this list is the
    most valuable thing" an adversary can return. It was written at 67 ledger rows. Nobody had ever
    scored it -- and the rows found since are exactly the material to score it with.

        clean hit                  D79 <- A1   (and A1 was marked ACTED ON, yet the same error
                                                recurred one step later)
        class-level hit            D71 <- A7   (threshold degrades as the artifact grows, unwatched)
        partial                    D76 <- A2   (one synthetic task; did not predict a degenerate one)
        14 others                  not on the page in any form

        1 of 17 =  5.9% clean   ·   3 of 17 = 17.6% counting class-level and partial

    BOTH BOUNDS ARE EMITTED because the generosity of matching is a choice, and this repository has
    already been caught letting a choice like that move a headline by 2.2x.

    THE VALUE WAS NOT IN THE FORECAST. A4 was resolved by the file itself and scored the author
    "badly -- under-severe"; A7's act of being written found the real problem. Writing predictions
    was productive; the predictions were mostly wrong. Only the second is a failure.

    AND THE FILE CARRIED AN ERROR THE LEDGER HAD ALREADY FIXED. Its A1 row described the eight as
    "five read-head candidates, one proven copy head, two unlabelled". R16 read the source and found
    seven selected plus one externally-known copy head; that was filed as D80 -- AND LANDED ON THE
    PRIOR-EFFECTS NOTE ONLY. The identical sentence sat in the file whose job is to score me.
    """
    f = HERE / 'ADVERSARY.md'
    d = HERE / 'defects.json'
    if not (f.exists() and d.exists()):
        return None
    rows = json.load(open(d))['defects']
    BASELINE = 67          # the ledger size stated in ADVERSARY.md when it was written
    # THE WINDOW IS FROZEN, AND THE FIRST VERSION OF THIS FUNCTION GOT IT WRONG. Scoring "every
    # defect after the file was written" makes the denominator grow forever, so the hit rate decays
    # toward zero without the file getting any worse -- a badly defined estimand, and it moved twice
    # within one step (5.9% -> 5.6%) as this same step added rows. The right estimand is: OF THE
    # DEFECTS FOUND BETWEEN THE FILE'S WRITING AND THE MOMENT IT WAS SCORED, how many did it
    # anticipate? That window is D68..D84. Anything later faces the file EXTENDED with A9-A13, which
    # is a different object and must be scored separately when it is scored at all.
    WINDOW = [f'D{i}' for i in range(68, 85)]
    after = [r for r in rows if r['id'] in WINDOW]
    HIT = {'D79': 'A1'}
    CLASS = {'D71': 'A7'}
    PARTIAL = {'D76': 'A2'}
    ids = [r['id'] for r in after]
    miss = [i for i in ids if i not in HIT and i not in CLASS and i not in PARTIAL]
    n = len(after)
    return {'baseline_rows': BASELINE, 'current_rows': len(rows), 'n_after': n,
            'n_clean_hit': len(HIT), 'n_class': len(CLASS), 'n_partial': len(PARTIAL),
            'n_miss': len(miss), 'miss_ids': miss,
            'pct_clean': 100 * len(HIT) / n if n else float('nan'),
            'pct_generous': 100 * (len(HIT) + len(CLASS) + len(PARTIAL)) / n if n else float('nan'),
            'window': [WINDOW[0], WINDOW[-1]],
            'rounds_covered': ['R1', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10'],
            'rounds_uncovered_before_this_step': ['R11', 'R12', 'R13', 'R14', 'R15', 'R16', 'R17',
                                                  'R18']}


def instrument_triangle():
    """ALL THREE PAIRWISE RELATIONSHIPS BETWEEN THE THREE INSTRUMENT CLASSES, with a layer control.

    The repository had measured ONE edge -- R16's attention x ablation -- and called it "no arbiter".
    That rested on a single edge of a triangle. Closing it does two things.

    FIRST, IT NARROWS R16 BY HALF. Within layer, the ROOM-attention edge is +0.0060 and +0.1289: it
    does not survive, and the pooled -0.19 was mostly the shared layer trend. Only the NAME-attention
    edge holds, at -0.4341 and -0.3427 within layer.

    SECOND, attention.room_att x OV.rooms is -0.2124 pooled and -0.1788 within layer: attention to
    the room token ANTI-correlates with the OV circuit's ability to copy the room token.

    So the three ways this literature identifies a copy head -- it attends to the thing, ablating it
    hurts, its OV maps the thing to itself -- are mutually uninformative or mildly opposed here.

    THE SCOPE IS NARROWER THAN IT LOOKS. Three instruments disagreeing does NOT mean all three are
    wrong: a head can attend to X, not copy X directly, and still matter through composition, which
    is exactly what disagreement predicts. What follows is only that on this task these three
    operationalizations do not identify the same heads, so none of them ALONE licenses "the copy
    head". Each is specific -- E132's final-position attention, zero-ablation at final or all
    positions, direct-path OV -- not attention or ablation in general.
    """
    f = HERE / 'R16_selection_vs_effect' / 'results' / 'instrument_triangle_qwen2.5-1.5b.json'
    if not f.exists():
        return None
    d = json.load(open(f))
    e = d['edges']
    return {'n_heads': d['n_heads'], 'edges': e,
            'r16_room_survives': abs(e['attention.room_att x ablation.I_final']['within_layer_abs'])
            > 0.15,
            'r16_name_survives': abs(e['attention.name_att x ablation.I_final']['within_layer_abs'])
            > 0.15}


def ov_copying():
    """A THIRD INSTRUMENT, AND THE FIRST ONE INDEPENDENT OF BOTH ATTENTION AND ABLATION.

    D101 said this repository is a two-instrument disagreement with no arbiter, and D100 said every
    role claim traces to attention. The model's own WEIGHTS are a third instrument and cost nothing:
    a copy head's OV circuit should map a room token back to itself.

        M[t,s] = W_E[t] . W_O_h . W_V_kv . W_E[s]  + a per-t bias term, over the 4 room tokens
        GQA: query head h uses KV head h//6.  tie_word_embeddings=True, so W_U = W_E.

    POSITIVE CONTROL PASSES: 16 of 168 band heads map all 4 rooms to themselves, normalized diagonal
    dominance up to +2.45. The instrument can find copiers.

    THE TARGET FAILS. L22H7 -- the head E123 named the copy head, and the only head in this
    repository with any independently claimed role -- scores diag_wins 1/4, which is CHANCE, at
    normalized dominance -0.4949, RANK 140 OF 168, 17.3rd percentile.

    P6, AND THE DIRECTION MATTERS: this is the DIRECT path only. No layernorm, no MLPs, no
    composition with other heads. A HIGH score is evidence of direct copying; a LOW score is NOT
    evidence of no copying, because a head can copy through composition. So L22H7's result is
    UNVERIFIED for "not a copy head", not OVERTURNED. What it does establish is that the copy-head
    label has never been supported by the weights, and nobody had looked.

    AND THREE INSTRUMENTS CONVERGE ON A DIFFERENT HEAD. L17H0 is in the published eight (attention),
    ranks 4th of 168 under I_all ablation (R18), and is 3rd of 168 here (+2.4383, diag_wins 4/4).
    That conjunction is POST HOC -- the top-6 was read after computing -- so it is a hypothesis, and
    R19's prediction registers it against data that does not yet exist.
    """
    f = HERE / 'R16_selection_vs_effect' / 'results' / 'ov_copying_qwen2.5-1.5b.json'
    g = HERE / 'R16_selection_vs_effect' / 'results' / 'ov_copying_3sets_qwen2.5-1.5b.json'
    if not f.exists():
        return None
    three = None
    if g.exists():
        gg = json.load(open(g))
        rr = gg['per_head']
        def rk3(key, nm):
            o = sorted(rr, key=lambda x: -rr[x][nm]['dom'])
            return o.index(key) + 1
        three = {'sets': gg['sets'], 'n': len(rr),
                 'perfect': {nm: sum(1 for v in rr.values() if v[nm]['wins'] == n)
                             for nm, n in gg['sets'].items()},
                 'max_dom': {nm: max(v[nm]['dom'] for v in rr.values()) for nm in gg['sets']},
                 'heads': {k: {nm: {'dom': rr[k][nm]['dom'], 'rank': rk3(k, nm)}
                               for nm in gg['sets']}
                           for k in ('L22H7', 'L17H0', 'L16H3')}}
    d = json.load(open(f))
    rows = d['per_head']
    n = len(rows)
    c = sorted(r['dom_norm'] for r in rows)
    idx = {(r['layer'], r['head']): r for r in rows}
    order = sorted(rows, key=lambda r: -r['dom_norm'])
    from collections import Counter
    def rank(L, h):
        return next(i for i, r in enumerate(order, 1) if (r['layer'], r['head']) == (L, h))
    k = idx[(22, 7)]
    return {'n_heads': n, 'rooms': d['rooms'],
            'dom_min': c[0], 'dom_median': c[n // 2], 'dom_max': c[-1],
            'diag_wins_hist': dict(sorted(Counter(r['diag_wins'] for r in rows).items())),
            'n_perfect': sum(1 for r in rows if r['diag_wins'] == 4),
            'L22H7': {'diag_wins': k['diag_wins'], 'dom_norm': k['dom_norm'],
                      'rank': rank(22, 7), 'percentile': 100 * (1 - (rank(22, 7) - 1) / n)},
            'L17H0': {'diag_wins': idx[(17, 0)]['diag_wins'],
                      'dom_norm': idx[(17, 0)]['dom_norm'], 'rank': rank(17, 0)},
            'top6': [{'head': f"L{r['layer']}H{r['head']}", 'dom_norm': r['dom_norm'],
                      'diag_wins': r['diag_wins']} for r in order[:6]],
            'three_sets': three}


def resolution_limit():
    """CAN THE MANDATED METHOD ANSWER THIS REPOSITORY'S OWN SURVIVING QUESTION? At this n, no.

    `10 of 168 clear the exhaustive floor` is the last positive count on the front page and it is a
    2*sd number, on a distribution the page itself says 2*sd does not test (excess kurtosis 7.31).
    Recomputed with the empirical conditional randomization percentile the repository now mandates,
    leave-one-out so no head is judged against a null containing itself:

        minimum attainable p from an empirical null over 168 values   1/169 = 0.0059
        Bonferroni at alpha 0.05 needs                                0.05/168 = 0.00030  UNREACHABLE
        BH-FDR at alpha 0.05                                          0 discoveries
        uncorrected empirical p <= 0.05                               8 of 168
        the published 2-sigma count                                   10 of 168

    THE P-VALUES SHOW WHY. The eight smallest are 1/167, 2/167, 3/167 ... An empirical null built
    from the population being tested converts every p into a RANK DIVIDED BY n, so the test has no
    resolution beyond ordering. ZERO DISCOVERIES IS A RESOLUTION LIMIT, NOT AN ABSENCE, and the limit
    is computed before the test rather than read off it.

    THE SET-LEVEL TEST DOES HAVE RESOLUTION, and the difference is the point: its null is GENERATED
    by 50,000 matched-layer resamples rather than BEING the population. Per-head significance needs a
    resampled null or a larger reference class; a count at a fixed threshold does not -- which is why
    this leaves the transport result untouched.
    """
    f = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    if not f.exists():
        return None
    d = json.load(open(f))
    L = {int(k): v for k, v in d['layers'].items()}
    NH = len(L[14]['per_head'])
    band = [(x, h) for x in range(14, 28) for h in range(NH)]
    v = {k: L[k[0]]['per_head'][str(k[1])] for k in band}
    n = len(band)
    ps = []
    for k in band:
        others = [v[j] for j in band if j != k]
        mu = sum(others) / len(others)
        x = abs(v[k] - mu)
        ps.append(((1 + sum(1 for z in others if abs(z - mu) >= x)) / (1 + len(others)), k))
    ps.sort()
    alpha = 0.05
    crit = [(i + 1) * alpha / n for i in range(n)]
    hits = [i for i in range(n) if ps[i][0] <= crit[i]]
    mu = sum(v.values()) / n
    sd = math.sqrt(sum((z - mu) ** 2 for z in v.values()) / (n - 1))
    return {'n': n, 'min_attainable_p': 1 / (n + 1), 'bonferroni_needs': alpha / n,
            'bonferroni_reachable': (1 / (n + 1)) <= (alpha / n),
            'bh_discoveries': (max(hits) + 1) if hits else 0,
            'bh_first_threshold': crit[0],
            'uncorrected_at_05': sum(1 for q, _ in ps if q <= alpha),
            'two_sd_count': sum(1 for z in v.values() if abs(z - mu) > 2 * sd),
            'excess_kurtosis': sum((z - mu) ** 4 for z in v.values()) / n / sd ** 4 - 3,
            'smallest_ps': [{'head': f'L{k[0]}H{k[1]}', 'p': q} for q, k in ps[:8]]}


def wo_conditioning():
    """AN OUTSIDE CRITIQUE OF R6, MEASURED FROM THE WEIGHTS RATHER THAN ACCEPTED IN PROSE.

    The critique: displacement_ratio = ||x - xbar|| / ||x|| cannot say whether mean-ablation is
    near-identity, because a small displacement can lie along a very high-gain direction of W_O and a
    large one can land in its approximate nullspace. Both halves are computable from the weights
    alone -- no GPU, no activations.

    For a per-head displacement d the functional version is r_out = ||W_h d|| / ||W_h x||, and since
    numerator and denominator pass through the SAME block, r_out / r is bounded in [1/kappa, kappa]
    with kappa = cond(W_h).

        168 band heads, each block 1536 x 128
        condition number  min 2.82  p25 4.31  MEDIAN 5.86  p75 7.61  max 17.67 (L27H10)
        stable rank       (sum s)^2 / (sum s^2)   MEDIAN 117.2 of 128

    THE NULLSPACE HALF IS REFUTED: at stable rank 117 of 128 there is essentially no nullspace to
    land in. THE HIGH-GAIN HALF IS BOUNDED at about 6x median rather than unbounded. So the critique
    is right that displacement_ratio is not a sufficient statistic, and the magnitude of its error is
    finite and measured. R6's verdict was already UNDECIDABLE; this does not change it, it explains
    part of why.

    THE BOUND IS LOOSE. [1/kappa, kappa] is a worst case over ARBITRARY directions, while the real
    displacement is item-to-item variation of a live activation and most likely lies in the
    high-variance directions. Tightening needs the activations, which were never stored.
    """
    f = HERE / 'R6_intervention' / 'results' / 'wo_block_conditioning_qwen2.5-1.5b.json'
    if not f.exists():
        return None
    d = json.load(open(f))
    rows = d['per_head']
    c = sorted(r['cond'] for r in rows)
    sr = sorted(r['srank'] for r in rows)
    w = max(rows, key=lambda r: r['cond'])
    n = len(c)
    return {'n_heads': n, 'block_shape': d['block_shape'], 'head_dim': d['head_dim'],
            'cond_min': c[0], 'cond_p25': c[n // 4], 'cond_median': c[n // 2],
            'cond_p75': c[3 * n // 4], 'cond_max': c[-1],
            'worst_head': f"L{w['layer']}H{w['head']}",
            'srank_median': sr[n // 2],
            'srank_of_dims': d['head_dim']}


def floor_transport():
    """DOES A SCALAR FLOOR TRANSPORT? Out-of-sample calibration across four configurations.

    This is the one result here that is not about the eight heads at all. It is about the method.

    A "noise floor" is only a floor if the decision rule it defines means the same thing somewhere
    else. Transport A's WHOLE rule -- |x - mu_A| > floor_A -- into three other configurations, each
    differing from A in EXACTLY ONE factor, and compare what it says against what that
    configuration's own reference class says.

        configuration                        own floor  own rate  A-rule rate  ratio   differs by
        A  I_final @ unshuffled                 0.4870     5.95%       5.95%   1.00    (positive ctrl)
        D  I_final @ unshuffled, NEW items      0.4891     5.95%       5.95%   1.00    item sample
        C  I_all   @ unshuffled                 0.9766     8.33%      19.64%   2.36    intervention
        B  I_final @ SHUFFLED                   0.4023     7.14%       3.57%   0.50    task/position

    THE POSITIVE CONTROL IS ROW D AND IT IS ALSO THE DISCRIMINATOR. A completely fresh item draw --
    seeds 3400-3800 against 3000-3400 -- transports at ratio 1.00. So the instrument IS stable in the
    way R11 established, and a failure elsewhere cannot be blamed on sampling noise.

    AND THE TWO FAILURES POINT IN OPPOSITE DIRECTIONS. Believing A's floor under a different
    INTERVENTION calls 33 of 168 heads distinguishable where that configuration's own reference says
    14 -- the false-positive rate inflates 2.36x. Believing it under a different TASK calls 6 where
    its own reference says 12 -- you miss half. A SCALAR FLOOR IS NOT MERELY IMPRECISE; ITS BIAS
    DEPENDS ON WHICH WAY THE CONFIGURATION MOVED, so no safety factor fixes it.

    WHAT THIS IS NOT. The "own rate" is itself a 2*sd threshold on a heavy-tailed distribution, so
    this compares TWO APPLICATIONS OF THE SAME RULE rather than testing against a true alpha. That is
    the right comparison for transportability, which is the question, but it is not a calibration
    against a nominal 5%. One model, one band L14-27, one task family, k=1, and one contrast per axis.
    """
    import math as _m
    files = [
        ('A  I_final @ unshuffled', 'R10_exhaustive/results/r10_exhaustive_qwen2.5-1.5b.json',
         'same configuration -- POSITIVE CONTROL'),
        ('D  I_final @ new items', 'R11_instrument_noise/results/r11_itemsB_qwen2.5-1.5b.json',
         'item sample ONLY'),
        ('C  I_all   @ unshuffled', 'R18_all_positions/results/r18_allpos_qwen2.5-1.5b.json',
         'intervention support ONLY'),
        ('B  I_final @ shuffled', 'R15_shuffled_scan/results/r15_shuffled_qwen2.5-1.5b.json',
         'task / answer position ONLY')]
    rows = []
    ref = None
    for name, rel, why in files:
        f = HERE / rel
        if not f.exists():
            return None
        d = json.load(open(f))
        L = {int(k): v for k, v in d['layers'].items()}
        NH = len(L[14]['per_head'])
        b = [(x, h) for x in range(14, 28) for h in range(NH)]
        v = [L[x]['per_head'][str(h)] for x, h in b]
        mu = sum(v) / len(v)
        fl = 2 * _m.sqrt(sum((z - mu) ** 2 for z in v) / (len(v) - 1))
        if ref is None:
            ref = (mu, fl)
        own = sum(1 for z in v if abs(z - mu) > fl)
        transported = sum(1 for z in v if abs(z - ref[0]) > ref[1])
        # WHICH KNOB FAILS? Transporting both at once cannot say whether the CENTRE or the SCALE is
        # the thing that does not travel, and the two have completely different remedies: a local
        # re-centring is cheap, a local scale means the floor is not a number you can carry.
        scale_only = sum(1 for z in v if abs(z - mu) > ref[1])      # local centre, A's scale
        centre_only = sum(1 for z in v if abs(z - ref[0]) > fl)     # A's centre, local scale
        rows.append({'config': name, 'differs_by': why, 'n': len(v),
                     # THE UNIFYING QUANTITY. Whether the CENTRE's transport matters is not a
                     # constant of this repository -- it depends on how big the centre SHIFT is
                     # relative to the DESTINATION's scale. On the band-to-band axes that is a few
                     # percent and the centre is irrelevant; on the layer axis it is over half, and
                     # there the centre matters as much as the scale.
                     'shift_over_dest_scale': abs(mu - ref[0]) / fl,
                     'own_floor': fl, 'own_mu': mu,
                     'own_n': own, 'own_pct': 100 * own / len(v),
                     'transported_n': transported, 'transported_pct': 100 * transported / len(v),
                     'ratio': transported / own if own else float('nan'),
                     'scale_only_n': scale_only, 'centre_only_n': centre_only,
                     'scale_only_ratio': scale_only / own if own else float('nan'),
                     'centre_only_ratio': centre_only / own if own else float('nan'),
                     'mu_ratio': mu / ref[0] if ref[0] else float('nan'),
                     'floor_ratio': fl / ref[1]})
    # THE FOURTH AXIS: LAYER BAND. It is the largest known variation in this repository (6.15x)
    # and it was not in the table. It is also the only axis where the REVERSE direction can be
    # tested, because both regions come from the SAME result file.
    d = json.load(open(HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'))
    L = {int(k): v for k, v in d['layers'].items()}
    NH = len(L[0]['per_head'])

    def region(lo, hi):
        v = [L[x]['per_head'][str(h)] for x in range(lo, hi) for h in range(NH)]
        mu = sum(v) / len(v)
        return v, mu, 2 * _m.sqrt(sum((z - mu) ** 2 for z in v) / (len(v) - 1))

    vS, muS, fS = region(0, 8)
    vB, muB, fB = region(14, 28)

    def cnt(v, mu, f):
        return sum(1 for z in v if abs(z - mu) > f)

    layer = {
        'sham_n': len(vS), 'sham_mu': muS, 'sham_floor': fS,
        'band_mu': muB, 'band_floor': fB,
        'floor_ratio_band_over_sham': fB / fS, 'mu_ratio': muB / muS,
        'sham_own': cnt(vS, muS, fS), 'sham_by_band_rule': cnt(vS, muB, fB),
        'band_own': cnt(vB, muB, fB), 'band_by_sham_rule': cnt(vB, muS, fS),
        'sham_scale_only': cnt(vS, muS, fB), 'sham_centre_only': cnt(vS, muB, fS),
        'shift_over_sham_scale': abs(muB - muS) / fS,
        # emitted as a PERCENT as well, because the pages quote it that way and a value
        # the reference set holds only as a fraction cannot back prose that says 55.5%
        'shift_over_sham_scale_pct': 100 * abs(muB - muS) / fS}
    layer['ratio_down'] = layer['sham_by_band_rule'] / max(layer['sham_own'], 1e-9)
    layer['ratio_up'] = layer['band_by_sham_rule'] / layer['band_own']
    return {'reference_mu': ref[0], 'reference_floor': ref[1], 'rows': rows, 'layer_axis': layer}


def selection_overlap():
    """THE EIGHT WERE SELECTED, EVALUATED AND AUDITED ON THE SAME ITEMS. Established from source.

        e132_read_head.py:29        SEEDS = list(range(3000, 3300))   <- head SELECTION
        e132b_read_head_causal.py:27 SEEDS = list(range(3000, 3300))  <- causal EVALUATION of the 8
        R10_exhaustive/run.py:72     SEEDS = list(range(3000, 3400))  <- THIS AUDIT, first 120
        R11 set B                          range(3400, 3800)          <- the ONLY independent items

    All three take the first items that pass the same baseline-correct filter starting from seed
    3000, and R14 measured that filter as rejecting nothing on this task for this model. So the
    selection set, the evaluation set and the audit set are the SAME 120 ITEMS. Winner's curse is
    maximal and nothing in this repository had said so.

    IT CUTS BOTH WAYS AND BOTH ARE STATED. The "not enriched" null is STRENGTHENED -- the eight fail
    to beat matched-layer random on the very data they were chosen on, with full home advantage. But
    every head-level number here except R11's set B is computed on the data the heads were selected
    on, which is a scope on all of it.

    THE SHRINKAGE TEST, on the only independent items available:

        aggregation          the eight   matched-layer null median      p (shrink more)
        sum-ratio               0.8425             1.0180                  0.0150
        mean-of-ratios          0.8257             1.0085                  0.0098
        median-of-ratios        0.9919             1.0135                  0.2769

    TWO OF THREE FIRE AND THE MEDIAN DOES NOT, so the aggregation is reported rather than chosen:
    L16H3 and L22H7 carry 75% of sum|c_A|, which makes the sum-ratio essentially a two-head
    statistic. THE SET-LEVEL WINNER'S CURSE IS NOT A SET PROPERTY. It is one head.

    L22H7 ALONE retains 0.0401 of its centred effect on independent items -- the LOWEST of all 168
    band heads, 0.0th percentile, exact one-head p = 0.0118. Its own eleven layer-mates retain 0.59
    to 1.22. That is what the rank move 41 -> 160 was, and it now has a name: the one head in this
    repository with an independently established prior claim shows the strongest selection
    inflation. Identifying it needs no peeking -- "the head with a prior claim" is specified by role,
    not by the table -- but the threshold was not pre-registered and the reading is post hoc.

    RTM CONTROL: regression to the mean shrinks whatever was extreme, and the eight are BELOW the
    matched-layer null median on set A. So RTM predicts they shrink LESS than random, and the
    observed direction runs against that prediction rather than being explained by it.
    """
    import random as _r
    import statistics as _st
    a = HERE / 'R11_instrument_noise' / 'results' / 'r11_itemsA_qwen2.5-1.5b.json'
    b = HERE / 'R11_instrument_noise' / 'results' / 'r11_itemsB_qwen2.5-1.5b.json'
    pe = r1_prior_effects()
    if not (a.exists() and b.exists() and pe):
        return None
    A, B = json.load(open(a)), json.load(open(b))
    LA = {int(k): v for k, v in A['layers'].items()}
    LB = {int(k): v for k, v in B['layers'].items()}
    NH = len(LA[14]['per_head'])
    band = [(x, h) for x in range(14, 28) for h in range(NH)]
    by_layer = {}
    for k in band:
        by_layer.setdefault(k[0], []).append(k)
    va = {k: LA[k[0]]['per_head'][str(k[1])] for k in band}
    vb = {k: LB[k[0]]['per_head'][str(k[1])] for k in band}
    mua = sum(va.values()) / len(va)
    mub = sum(vb.values()) / len(vb)
    ca = {k: abs(va[k] - mua) for k in band}
    cb = {k: abs(vb[k] - mub) for k in band}
    eight = sorted((int(k[1:k.index('H')]), int(k[k.index('H') + 1:])) for k in pe['effects'])
    eight = [k for k in eight if 14 <= k[0] < 28]
    N = 50000
    aggs = {
        'sum_ratio': lambda S: sum(cb[k] for k in S) / max(1e-12, sum(ca[k] for k in S)),
        'mean_of_ratios': lambda S: sum(cb[k] / max(1e-12, ca[k]) for k in S) / len(S),
        'median_of_ratios': lambda S: _st.median([cb[k] / max(1e-12, ca[k]) for k in S])}
    out = {}
    for nm, f in aggs.items():
        t = f(eight)
        rng = _r.Random(41)
        null = sorted(f([rng.choice(by_layer[k[0]]) for k in eight]) for _ in range(N))
        out[nm] = {'observed': t, 'null_median': null[N // 2],
                   'p': (1 + sum(1 for z in null if z <= t)) / (1 + N)}
    ret = sorted(cb[k] / max(1e-12, ca[k]) for k in band if ca[k] > 1e-9)
    r227 = cb[(22, 7)] / ca[(22, 7)]
    return {
        'selection_seeds': [3000, 3300], 'audit_seeds': [3000, 3400],
        'independent_seeds': [3400, 3800], 'same_item_set': True,
        'aggregations': out, 'n_replicates': N,
        'top2_share_of_sum': (ca[(16, 3)] + ca[(22, 7)]) / sum(ca[k] for k in eight),
        'L22H7_retention': r227,
        'L22H7_percentile': 100 * sum(1 for z in ret if z < r227) / len(ret),
        'L22H7_one_head_p': (1 + sum(1 for z in ret if z <= r227)) / (1 + len(ret)),
        'band_median_retention': ret[len(ret) // 2],
        'L22_layermates': sorted(round(cb[k] / max(1e-12, ca[k]), 2)
                                 for k in by_layer[22] if k != (22, 7)),
        'per_head': [{'head': f'L{x}H{h}', 'a': ca[(x, h)], 'b': cb[(x, h)],
                      'retention': cb[(x, h)] / max(1e-12, ca[(x, h)])} for x, h in eight]}


def set_enrichment():
    """THE TEST THIS PROJECT SHOULD HAVE RUN FIRST: are the eight ENRICHED against MATCHED random?

    Every earlier round compared each head, one at a time, against a SCALAR floor. That is the wrong
    question twice over: it tests eight hypotheses without correction, and it compares band heads to
    a reference class that does not hold layer fixed. The question the audit is actually asking is

        is the PRE-SPECIFIED SET of eight more extreme than a random set of eight
        drawn from THE SAME LAYERS?

    T_pub = mean over the set of |tau_h - mu_band|, and the null replaces each published head with a
    uniformly random head FROM ITS OWN LAYER, 50,000 times. Layer matching is not decoration: the
    eight sit in L16-L22, effect magnitude varies strongly with depth, and an unmatched null would
    manufacture enrichment out of nothing but where the heads live.

                    T_pub    matched-layer null median         p
        I_final    0.1154              0.1670               0.7994
        I_all      0.3196              0.4004               0.6782

    NOT ENRICHED UNDER EITHER INTERVENTION -- and T_pub is BELOW the null median in both. The eight
    published heads are, on average, LESS extreme than random heads from the same layers.

    THE INSTRUMENT IS ALIVE AND CALIBRATED, both checked before the null was believed:
        positive control -- the actual top-8 by |centred| scores p = 0.00004
        null calibration -- 200 random matched sets give p < 0.05 at a rate of 0.035, nominal 0.05

    AND THIS RETIRES MY OWN HEADLINE FROM ONE STEP EARLIER. R18 found L17H0 at rank 4 of 168 under
    I_all and this file called it "the result". Its one-head exact randomization p is 0.0296, which
    is 0.237 after Bonferroni over the eight heads that were tested. IT IS A POST-SELECTION
    DESCRIPTIVE TAIL, not a finding, and 168 heads were scanned to surface it.

    BOTH DISTRIBUTIONS ARE HEAVY-TAILED -- excess kurtosis 7.31 under I_final and 6.67 under I_all --
    which is why the 2*sd floor is not a test in either arm and the percentile is used instead.
    """
    import random as _r
    fa = HERE / 'R18_all_positions' / 'results' / 'r18_allpos_qwen2.5-1.5b.json'
    fb = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    pe = r1_prior_effects()
    if not (fa.exists() and fb.exists() and pe):
        return None
    A, B = json.load(open(fa)), json.load(open(fb))
    LA = {int(k): v for k, v in A['layers'].items()}
    LB = {int(k): v for k, v in B['layers'].items()}
    NH = len(LA[0]['per_head'])
    band = [(x, h) for x in range(14, 28) for h in range(NH)]
    by_layer = {}
    for k in band:
        by_layer.setdefault(k[0], []).append(k)
    eight = sorted((int(k[1:k.index('H')]), int(k[k.index('H') + 1:])) for k in pe['effects'])
    eight = [k for k in eight if 14 <= k[0] < 28]

    def arm(L):
        v = {k: L[k[0]]['per_head'][str(k[1])] for k in band}
        mu = sum(v.values()) / len(v)
        sd = math.sqrt(sum((z - mu) ** 2 for z in v.values()) / (len(v) - 1))
        kurt = sum((z - mu) ** 4 for z in v.values()) / len(v) / sd ** 4 - 3
        return v, mu, sd, kurt

    N = 50000
    out = {}
    # ONE SEEDED STREAM PER RANDOMIZATION, NOT ONE SHARED GENERATOR. D72 recorded exactly this
    # defect once already: a later loop continued an earlier one's generator, so adding a
    # computation silently moved results that had nothing to do with it. Adding the signed test
    # below moved the magnitude p from 0.6782 to 0.6774 and the positive-control count from 1 to 2 --
    # small, and entirely an artefact of draw order. Independent streams make every number here a
    # function of its own inputs.
    for tag, L in (('I_final', LB), ('I_all', LA)):
        rng = _r.Random(19 if tag == 'I_final' else 20)
        v, mu, sd, kurt = arm(L)

        def T(st):
            return sum(abs(v[k] - mu) for k in st) / len(st)

        def Ts(st):
            return sum(v[k] - mu for k in st) / len(st)

        t = T(eight)
        null = sorted(T([rng.choice(by_layer[k[0]]) for k in eight]) for _ in range(N))
        # THE NULL DRAWS WITH REPLACEMENT AND THE OBSERVED SET CANNOT. The eight sit in layer
        # multiset {16:1, 17:3, 18:1, 19:2, 22:1}, so a with-replacement draw can pick the same L17
        # head twice while the published set has eight DISTINCT heads. Sampling with replacement
        # gives the set mean a larger variance -- no finite-population correction -- so the null is
        # WIDER than the correct one and the test is CONSERVATIVE. Measured: sd ratio 1.031 and
        # 1.045, p moving 0.7994 -> 0.8069 and 0.6817 -> 0.6917, i.e. AWAY from significance. Both
        # are emitted; the distinct-per-layer version is the correct one and the difference changes
        # no conclusion.
        import collections as _c
        cnt = _c.Counter(k[0] for k in eight)
        rng2 = _r.Random(19 if tag == 'I_final' else 20)

        def draw_distinct():
            st = []
            for lay, c in cnt.items():
                st += rng2.sample(by_layer[lay], c)
            return st

        nulld = sorted(T(draw_distinct()) for _ in range(N))
        # SIGNED AS WELL, because |.| discards the sign and R19's own pre-registration says so:
        # "if each head had a signed mechanistic claim, do not take the absolute value". The eight
        # were selected as read heads plus one copy head, so the pre-specified direction is HURT --
        # ablating a head that carries the answer should LOWER the margin.
        ts = Ts(eight)
        nulls = sorted(Ts([rng.choice(by_layer[k[0]]) for k in eight]) for _ in range(N))
        out[tag] = {'T_pub': t, 'null_median': null[N // 2],
                    'p': (1 + sum(1 for z in null if z >= t)) / (1 + N),
                    'p_distinct_per_layer': (1 + sum(1 for z in nulld if z >= t)) / (1 + N),
                    'null_median_distinct': nulld[N // 2],
                    # the sd ratio is quoted on the pages, so it must be EMITTED rather
                    # than recomputed by a reader from two medians
                    'null_sd_ratio_repl_over_distinct':
                        math.sqrt(sum((z - sum(null) / N) ** 2 for z in null) / N)
                        / math.sqrt(sum((z - sum(nulld) / N) ** 2 for z in nulld) / N),
                    'layer_multiset': dict(cnt),
                    'excess_kurtosis': kurt, 'sd': sd,
                    'below_null_median': t < null[N // 2],
                    'T_pub_signed': ts, 'null_median_signed': nulls[N // 2],
                    'p_hurt': (1 + sum(1 for z in nulls if z >= ts)) / (1 + N),
                    'p_help': (1 + sum(1 for z in nulls if z <= ts)) / (1 + N),
                    'n_raw_pos': sum(1 for z in v.values() if z > 0),
                    'n_raw_neg': sum(1 for z in v.values() if z < 0),
                    'n_above_mu': sum(1 for z in v.values() if z > mu),
                    'n_below_mu': sum(1 for z in v.values() if z < mu), 'mu': mu}
    # positive control + calibration, on the arm the newest claim came from
    rng = _r.Random(21)
    v, mu, sd, kurt = arm(LA)

    def T(st):
        return sum(abs(v[k] - mu) for k in st) / len(st)

    top8 = sorted(band, key=lambda k: -abs(v[k] - mu))[:8]
    t = T(top8)
    null = [T([rng.choice(by_layer[k[0]]) for k in top8]) for _ in range(N)]
    pc_hits = sum(1 for z in null if z >= t)
    pc = (1 + pc_hits) / (1 + N)
    # and a SEPARATE positive control for the SIGNED test, because a control on the magnitude
    # statistic says nothing about whether the signed one can fire.
    def Ts_(st):
        return sum(v[k] - mu for k in st) / len(st)

    rng = _r.Random(22)
    tops = sorted(band, key=lambda k: -(v[k] - mu))[:8]
    tsv = Ts_(tops)
    pc_signed_hits = sum(1 for _ in range(N)
                         if Ts_([rng.choice(by_layer[k[0]]) for k in tops]) >= tsv)
    rng = _r.Random(23)
    hits = 0
    for _ in range(200):
        st = [rng.choice(by_layer[k[0]]) for k in eight]
        tt = T(st)
        nn = [T([rng.choice(by_layer[k2[0]]) for k2 in st]) for _ in range(400)]
        hits += (1 + sum(1 for z in nn if z >= tt)) / 401 < 0.05
    c = sorted(abs(v[k] - mu) for k in band)
    x = abs(v[(17, 0)] - mu)
    return {'arms': out, 'n_replicates': N,
            'positive_control_p': pc,
            'positive_control_hits': pc_hits,
            'positive_control_signed_hits': pc_signed_hits, 'null_calibration_rate': hits / 200,
            'L17H0_abs_centred': x, 'L17H0_sd_units': x / sd,
            'L17H0_one_head_p': (1 + sum(1 for z in c if z >= x)) / (1 + len(c)),
            'L17H0_bonferroni_8': min(1.0, 8 * (1 + sum(1 for z in c if z >= x)) / (1 + len(c)))}


def r18():
    """R18 -- is `final`-only a proxy for a head? NO, on all four pre-registered components.

    THE CORRECTED POSITIVE CONTROL PASSES EXACTLY. R18's original gate -- "the mean effect must rise"
    -- was withdrawn as D88 before this run landed: I_all strictly contains I_final in what it
    REMOVES, but the EFFECT need not grow, because cancellation and backup paths can shrink or flip
    it. The structural replacement: at the LAST layer the two interventions differ only in positions
    no later layer can read, so eta_h must be ~0. Observed max|eta| at L27 = 0.00000, to every digit
    stored, against a between-head sd of 0.17827. Saturation 0.29% against a 50% refusal.

    H-SUPPORT FAILS 4 OF 4:
        Spearman(tau_final, tau_all)   +0.6230   needs >= 0.9
        published-head verdicts agree     6/8    needs 8/8
        layer-centroid shift            0.1717   needs <= 0.03
        top-10 overlap                   4/10    needs >= 8/10

    SO `final`-ONLY IS NOT A PROXY FOR A HEAD. Every head-level number in this repository is about
    I_final(L,h), the final-query head-output knockout.

    R18's OWN looser rank rule reads differently and BOTH are reported: it pre-registered transfers
    at >=0.7 and does-not at <=0.3, so +0.6230 lands in between and its instruction is to claim
    neither -- the kill does not fire. Picking the convenient threshold is what pre-registration
    exists to prevent.

    L17H0 IS THE RESULT. Under the intervention used throughout this repository it is 0.18x the
    floor at rank 77 of 168 -- one of the seven the audit called unremarkable. Under the total head
    knockout it is 1.40x the floor and the 4TH LARGEST EFFECT OF 168. L17H7 runs the other way,
    0.17x -> 0.00x, rank 79 -> 163. The eight do not move together; the intervention re-sorts them.
    The `x floor` column is NOT comparable across arms because the floor itself doubles.

    AND THE |eta| PROFILE IS NOT MONOTONE IN DEPTH, which confirms D88's retraction empirically:
    0.4541 at L0, 0.1707 by L6, 0.4718 at L18, 0.0000 at L27. The retraction was made on Ivan's
    argument alone; the data now agrees with it.
    """
    a = HERE / 'R18_all_positions' / 'results' / 'r18_allpos_qwen2.5-1.5b.json'
    b = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    pe = r1_prior_effects()
    if not (a.exists() and b.exists() and pe):
        return None
    A, B = json.load(open(a)), json.load(open(b))
    LA = {int(k): v for k, v in A['layers'].items()}
    LB = {int(k): v for k, v in B['layers'].items()}
    NL, NH = len(LA), len(LA[0]['per_head'])

    def centroid(L):
        slo, shi = B['sham_band']
        sham = [v for x in range(slo, shi + 1) for v in L[x]['per_head'].values()]
        mus = sum(sham) / len(sham)
        fs = 2 * math.sqrt(sum((v - mus) ** 2 for v in sham) / (len(sham) - 1))
        rate = {x: sum(1 for v in L[x]['per_head'].values() if abs(v - mus) > fs) / NH
                for x in range(NL)}
        tot = sum(rate.values())
        return sum(x * q for x, q in rate.items()) / tot

    band = [(x, h) for x in range(14, 28) for h in range(NH)]
    va = [LA[x]['per_head'][str(h)] for x, h in band]
    vb = [LB[x]['per_head'][str(h)] for x, h in band]
    mua, mub = sum(va) / len(va), sum(vb) / len(vb)
    ca = [abs(v - mua) for v in va]
    cb = [abs(v - mub) for v in vb]
    fa = 2 * math.sqrt(sum((v - mua) ** 2 for v in va) / (len(va) - 1))
    fb = 2 * math.sqrt(sum((v - mub) ** 2 for v in vb) / (len(vb) - 1))
    oa = sorted(range(len(band)), key=lambda i: -ca[i])
    ob = sorted(range(len(band)), key=lambda i: -cb[i])
    eight = sorted((int(k[1:k.index('H')]), int(k[k.index('H') + 1:])) for k in pe['effects'])
    eight = [k for k in eight if 14 <= k[0] < 28]
    cF, cA = centroid(LB), centroid(LA)
    # THE 3b ARM, and R18's pre-registered rule for R12. Both models' centroids move EARLIER under
    # all-position ablation; the RULE asks whether the shift is a fixed FRACTION of depth or a fixed
    # NUMBER of layers, and it returns UNRESOLVED by 3%: B = 1.468 misses A/2 = 1.421 by 0.047. Had
    # the threshold been chosen after seeing this it would have been called layer-shaped.
    three = HERE / 'R18_all_positions' / 'results' / 'r18_allpos_qwen2.5-3b.json'
    tb = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-3b.json'
    r12 = None
    if three.exists() and tb.exists():
        A3, B3 = json.load(open(three)), json.load(open(tb))
        LA3 = {int(k): v for k, v in A3['layers'].items()}
        LB3 = {int(k): v for k, v in B3['layers'].items()}
        NL3 = A3['n_layers']
        NH3 = len(LA3[0]['per_head'])
        slo3, shi3 = B3['sham_band']

        def cen3(L):
            sh = [v for x in range(slo3, shi3 + 1) for v in L[x]['per_head'].values()]
            mus = sum(sh) / len(sh)
            fs = 2 * math.sqrt(sum((v - mus) ** 2 for v in sh) / (len(sh) - 1))
            rate = {x: sum(1 for v in L[x]['per_head'].values() if abs(v - mus) > fs) / NH3
                    for x in range(NL3)}
            tot = sum(rate.values())
            return sum(x * q for x, q in rate.items()) / tot
        cF3, cA3 = cen3(LB3), cen3(LA3)
        d1l, d2l = cA - cF, cA3 - cF3
        d1f, d2f = d1l / (NL - 1), d2l / (NL3 - 1)
        Aq = abs(d1f - d2f) * (NL3 - 1)
        Bq = abs(d1l - d2l)
        eta3 = max(abs(LA3[NL3 - 1]['per_head'][str(h)] - LB3[NL3 - 1]['per_head'][str(h)])
                   for h in range(NH3))
        r12 = {'centroid_final_3b': cF3, 'centroid_all_3b': cA3,
               'shift_layers_1_5b': d1l, 'shift_layers_3b': d2l,
               'shift_frac_1_5b': d1f, 'shift_frac_3b': d2f,
               'A_fraction_shaped': Aq, 'B_layer_shaped': Bq,
               'A_threshold': Bq / 2, 'B_threshold': Aq / 2,
               'miss_by': Bq - Aq / 2,
               'verdict': ('FRACTION' if Aq <= Bq / 2 else
                           'LAYER' if Bq <= Aq / 2 else 'UNRESOLVED'),
               'pc_last_layer_max_eta_3b': eta3,
               'flip_rate_3b': A3.get('flip_rate')}
    eta_last = [LA[NL - 1]['per_head'][str(h)] - LB[NL - 1]['per_head'][str(h)] for h in range(NH)]
    sd_all = math.sqrt(sum((v - mub) ** 2 for v in vb) / (len(vb) - 1))
    return {
        'pc_last_layer_max_abs_eta': max(map(abs, eta_last)), 'pc_between_head_sd': sd_all,
        'pc_passes': max(map(abs, eta_last)) < sd_all, 'flip_rate': A.get('flip_rate'),
        'spearman': _spearman(ca, cb), 'spearman_needs': 0.9,
        'published_agree': sum(1 for k in eight
                               if (ca[band.index(k)] > fa) == (cb[band.index(k)] > fb)),
        'centroid_final': cF, 'centroid_all': cA, 'r12_rule': r12,
        'depth_frac_final': cF / (NL - 1), 'depth_frac_all': cA / (NL - 1),
        'centroid_shift_layers': cA - cF, 'centroid_shift_norm': abs(cA - cF) / (NL - 1),
        'top10_overlap': len(set(oa[:10]) & set(ob[:10])),
        'floor_final': fb, 'floor_all': fa, 'floor_ratio': fa / fb,
        'h_support_components_failed': sum([
            _spearman(ca, cb) < 0.9,
            sum(1 for k in eight if (ca[band.index(k)] > fa) == (cb[band.index(k)] > fb)) < 8,
            abs(cA - cF) / (NL - 1) > 0.03,
            len(set(oa[:10]) & set(ob[:10])) < 8]),
        'eight': [{'head': f'L{x}H{h}',
                   'final': cb[band.index((x, h))], 'final_xfloor': cb[band.index((x, h))] / fb,
                   'final_rank': ob.index(band.index((x, h))) + 1,
                   'all': ca[band.index((x, h))], 'all_xfloor': ca[band.index((x, h))] / fa,
                   'all_rank': oa.index(band.index((x, h))) + 1} for x, h in eight],
        'eta_by_layer': [sum(abs(LA[x]['per_head'][str(h)] - LB[x]['per_head'][str(h)])
                             for h in range(NH)) / NH for x in range(NL)]}


def r17():
    """R17 -- IS THE HEADLINE AN ARTIFACT OF MEASURING WHERE THE FLOOR IS LARGEST?

    R15 showed the floor tracks the task's baseline margin at Spearman +0.8810. The eight published
    heads were measured on the configuration with the HIGHEST margin available -- every answer at
    line 0, the primacy position, margin 4.477 -- and the floor sits in the DENOMINATOR of `x floor`.
    A larger floor makes every head look smaller. So the repository's headline finding was produced
    at exactly the configuration most favourable to it. That is a directional bias pointing at my own
    conclusion, and R15's scan makes it free to check: the shuffled floor is 17% lower.

        WORLD A  "7 of 8 inside the floor" is a fact about those heads
        WORLD B  it is an artifact of the highest-floor configuration

    KILLED: WORLD B. On the shuffled task, where the floor is 0.4023 against 0.4870, the count goes
    1 of 8 to 0 OF 8. The lower floor rescued nothing. L16H3, the only one that cleared, falls from
    1.06x to 0.92x -- because its NUMERATOR fell 0.72x while the denominator fell only 0.83x.

    TWO NARRATIVE-FRIENDLY PATTERNS APPEAR IN THE SAME TABLE AND BOTH DIE TO CONTROLS RUN IN THE SAME
    COMPUTATION. Both pointed toward the conclusion this repository already argues, which is why the
    controls were run, not a reason to skip them.

      (1) SEVEN OF EIGHT RISE IN RANK, mean 101.6 -> 85.5. But ranks regress toward the middle for
          EVERY head: the slope of (shuffled rank - 84.5) on (unshuffled rank - 84.5) is 0.6092 over
          all 168, which predicts 94.9. Residual -9.43. Against 20,000 random 8-head sets the null sd
          is 13.29 and one-sided p = 0.2351. INSIDE THE NULL. No finding.

      (2) L22H7's RAW EFFECT MORE THAN HALVES, 0.433x, while the floor fell only 0.826x -- and it is
          the only one of the eight to fall in rank. But the median band head's effect fell to 0.723x
          with an IQR of 0.424 to 1.392, so 0.433 is the 26.2nd percentile: inside the IQR, low-normal
          NOT anomalous. It is also the noisiest of the eight -- R11 measured it at 1.27x its own SEM,
          the weakest margin of the set. No finding.

    THIS IS THE FIRST ROUND THAT ATTACKED A HEADLINE CLAIM AND DID NOT MOVE IT. No ledger row is added
    for it, because nothing in the artifact was wrong. The two patterns above were caught before they
    were written down, and a defect caught before shipping is not a defect in the artifact.
    """
    import random as _r
    pe = r1_prior_effects()
    fa_ = HERE / 'R15_shuffled_scan' / 'results' / 'r15_shuffled_qwen2.5-1.5b.json'
    fb_ = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    if not (pe and fa_.exists() and fb_.exists()):
        return None
    a = json.load(open(fa_))
    b = json.load(open(fb_))
    LA = {int(k): v for k, v in a['layers'].items()}
    LB = {int(k): v for k, v in b['layers'].items()}
    NH = a['n_heads_per_layer']
    band = [(x, h) for x in range(14, 28) for h in range(NH)]
    va = [LA[x]['per_head'][str(h)] for x, h in band]
    vb = [LB[x]['per_head'][str(h)] for x, h in band]
    mua, mub = sum(va) / len(va), sum(vb) / len(vb)
    fa = 2 * math.sqrt(sum((v - mua) ** 2 for v in va) / (len(va) - 1))
    fb = 2 * math.sqrt(sum((v - mub) ** 2 for v in vb) / (len(vb) - 1))
    cu = {k: abs(LB[k[0]]['per_head'][str(k[1])] - mub) for k in band}
    cs = {k: abs(LA[k[0]]['per_head'][str(k[1])] - mua) for k in band}
    ru = sorted(band, key=lambda k: -cu[k])
    rs = sorted(band, key=lambda k: -cs[k])
    RU = {k: ru.index(k) + 1 for k in band}
    RS = {k: rs.index(k) + 1 for k in band}
    MID = (len(band) + 1) / 2
    X = [RU[k] - MID for k in band]
    Y = [RS[k] - MID for k in band]
    slope = sum(X[i] * Y[i] for i in range(len(X))) / sum(x * x for x in X)
    eight = [(int(k[1:k.index('H')]), int(k[k.index('H') + 1:])) for k in pe['effects']]
    eight = sorted(k for k in eight if 14 <= k[0] < 28)

    def resid(S):
        return (sum(RS[k] for k in S) / len(S)
                - (MID + slope * (sum(RU[k] for k in S) / len(S) - MID)))

    obs = resid(eight)
    rng = _r.Random(11)
    N = 20000
    null = [resid(rng.sample(band, len(eight))) for _ in range(N)]
    pval = sum(1 for v in null if v <= obs) / N
    rat = sorted((cs[k] / cu[k], k) for k in band if cu[k] > 1e-9)
    r227 = next(r for r, k in rat if k == (22, 7))
    return {'floor_unshuffled': fb, 'floor_shuffled': fa, 'floor_ratio': fa / fb,
            'mid_rank': MID,
            'n_clear_unshuffled': sum(1 for k in eight if cu[k] > fb),
            'n_clear_shuffled': sum(1 for k in eight if cs[k] > fa),
            'rows': [{'head': f'L{x}H{h}', 'cu': cu[(x, h)], 'xf_u': cu[(x, h)] / fb,
                      'ru': RU[(x, h)], 'cs': cs[(x, h)], 'xf_s': cs[(x, h)] / fa,
                      'rs': RS[(x, h)], 'num_ratio': cs[(x, h)] / cu[(x, h)]}
                     for x, h in eight],
            'regression_slope': slope, 'mean_rank_unshuffled': sum(RU[k] for k in eight) / 8,
            'mean_rank_shuffled': sum(RS[k] for k in eight) / 8,
            'predicted_mean_rank': MID + slope * (sum(RU[k] for k in eight) / 8 - MID),
            'residual': obs, 'null_sd': math.sqrt(sum(v * v for v in null) / N),
            'p_one_sided': pval, 'n_null': N,
            'L22H7_num_ratio': r227,
            'L22H7_percentile': 100 * sum(1 for r, _ in rat if r < r227) / len(rat),
            'median_num_ratio': rat[len(rat) // 2][0],
            'iqr_lo': rat[len(rat) // 4][0], 'iqr_hi': rat[3 * len(rat) // 4][0]}


def r15():
    """R15 -- the shuffled exhaustive scan. Pre-registered kill: does the head ranking transfer?

    Thresholds committed BEFORE the run (R15_shuffled_scan/PREREGISTRATION.md): transfers at
    Spearman >= 0.7, does not at <= 0.3, in between "report it, claim neither".

        Spearman over the 168 band heads, shuffled vs unshuffled
            on |centred drop|   +0.6092      <- the statistic this repo RANKS BY. Middle band.
            on signed drop      +0.7175

    THE KILL DID NOT FIRE AND THE PASS WAS NOT EARNED. Two statistics straddle the threshold and
    picking the one that clears it is a narrative, so both are reported and neither is claimed.

    POPULATION CONFOUND, CHECKED AND CLEARED. R15 changed TWO things against R10: line order AND the
    correctness filter. A single contrast over two treatments cannot be decomposed -- except that the
    second treatment is a measured no-op. R14 measured A_orig = 1.000 over 120 items: the filter has
    never rejected a single item on the UNSHUFFLED task for this model, so filter-on and filter-off
    are the same population there. Verified directly: same draw_seed 20260727, same 120 items, same
    4 rooms, same sham band [0,7].

    THE FINDING IS THE THIRD READING, NOT THE FIRST. The pre-registration also asked for per-answer-
    line floors, on the grounds that "if the floor itself is position-dependent, a single number for
    the shuffled task is the same mistake one level up". IT IS POSITION-DEPENDENT:

        per-line floor spans 0.3011 to 0.4997 = 1.66x
        Spearman(per-line baseline margin, per-line floor) = +0.8810 over 8 lines

    SO THE FLOOR IS A FUNCTION OF TASK HEADROOM, not of the model and band alone. The repository has
    been quoting 0.4870 as though it were the latter. It was measured at baseline margin 4.477.

    BUT SUBLINEARLY, AND THAT MATTERS IN THE OTHER DIRECTION. Across lines the margin swings 7.54x
    (0.567 to 4.273) while the floor swings 1.66x. As a FRACTION, floor/margin runs 0.108 to 0.633 --
    a 5.84x spread. So the ABSOLUTE floor is comparatively robust, which is what a noise floor ought
    to be if it measures head-to-head variability rather than task headroom; but `x floor`, the unit
    this repository ranks published heads in, IS NOT PORTABLE ACROSS TASK CONFIGURATIONS.
    """
    f = HERE / 'R15_shuffled_scan' / 'results' / 'r15_shuffled_qwen2.5-1.5b.json'
    g = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    if not (f.exists() and g.exists()):
        return None
    a = json.load(open(f))
    b = json.load(open(g))
    LA = {int(k): v for k, v in a['layers'].items()}
    LB = {int(k): v for k, v in b['layers'].items()}
    NH = a['n_heads_per_layer']
    band = [(x, h) for x in range(14, 28) for h in range(NH)]
    va = [LA[x]['per_head'][str(h)] for x, h in band]
    vb = [LB[x]['per_head'][str(h)] for x, h in band]
    mua, mub = sum(va) / len(va), sum(vb) / len(vb)
    fa = 2 * math.sqrt(sum((v - mua) ** 2 for v in va) / (len(va) - 1))
    fb = 2 * math.sqrt(sum((v - mub) ** 2 for v in vb) / (len(vb) - 1))
    ca = [abs(v - mua) for v in va]
    cb = [abs(v - mub) for v in vb]
    pl = a['per_answer_line']
    ks = sorted(pl, key=int)
    marg = [pl[k]['baseline_margin'] for k in ks]
    flo = [pl[k]['floor_2sd'] for k in ks]
    return {'spearman_abs': _spearman(ca, cb), 'spearman_signed': _spearman(va, vb),
            'threshold_transfers': 0.7, 'threshold_does_not': 0.3,
            'floor_shuffled': fa, 'floor_unshuffled': fb, 'floor_ratio': fa / fb,
            'margin_shuffled': a['base_margin'], 'margin_unshuffled': b['base_margin'],
            'n_clear_shuffled': sum(1 for v in ca if v > fa),
            'n_clear_unshuffled': sum(1 for v in cb if v > fb),
            'same_draw_seed': a['draw_seed'] == b.get('draw_seed'),
            'same_n_items': a['n_items'] == b.get('n_items'),
            'per_line': [{'line': int(k), 'n': pl[k]['n_items'],
                          'margin': pl[k]['baseline_margin'],
                          'acc': pl[k]['accuracy'], 'floor': pl[k]['floor_2sd'],
                          'floor_over_margin': pl[k]['floor_2sd'] / pl[k]['baseline_margin']}
                         for k in ks],
            'line_floor_spread': max(flo) / min(flo),
            'line_margin_spread': max(marg) / min(marg),
            'spearman_margin_vs_floor': _spearman(marg, flo),
            'margin_ratio': b['base_margin'] / a['base_margin'],
            'ratio_spread': max(x / y for x, y in zip(flo, marg))
                            / min(x / y for x, y in zip(flo, marg))}


def depth_sensitivity():
    """THE INSTRUMENT'S SENSITIVITY IS NOT FLAT IN DEPTH, AND R12's VERDICT TURNS ON DEPTH.

    Every ablation in this repository zeroes head h's slice of the o_proj input AT THE FINAL
    POSITION ONLY -- `x[0, -1, h*HD:(h+1)*HD] = 0`, R10_exhaustive/run.py:213. That removes the
    head's direct write at the final position and everything downstream of it AT that position. It
    does NOT remove the head's writes at positions 0..n-2, which later layers' attention reads back.

    THE NUMBER OF LAYERS THAT CAN READ THOSE EARLIER WRITES IS (NL - 1 - L). At the last layer it is
    ZERO -- there is no downstream reader, so the measurement is COMPLETE there. At layer 0 it is
    NL-1. So the fraction of a head's causal influence this instrument can see is monotone
    non-decreasing in L and is exactly 1 only at the last layer. That is structural, not empirical.

    WHY IT MATTERS HERE AND NOWHERE ELSE IN THE REPO: (NL-1-L)/NL is a FRACTION OF DEPTH. An
    instrument whose blind spot scales with the fraction of network remaining downstream places its
    centroid at a fixed depth FRACTION in any model, whatever the truth is. That is the exact shape
    of R12's surviving hypothesis. So the confound MANUFACTURES `RELATIVE` OUT OF `ABSOLUTE`, and
    R12's two point predictions differ by 5.6 layers with the later one winning.

    POSITIVE CONTROL, AND IT FIRES AGAINST THE CONFOUND: a profile produced by the bias alone -- flat
    truth times monotone sensitivity -- must be MAXIMAL AT THE LAST LAYER. Both models are near
    minimal there. qwen2.5-3b's last layer clears at 0.000, its global minimum, while its peak is
    0.562 at L26; qwen2.5-1.5b's last layer is 0.167 against a peak of 0.833 at L16. So the bias does
    not dominate the SHAPE.

    WHAT THAT CONTROL DOES NOT DO IS RESCUE THE CENTROID. The centroid is a first moment, and a first
    moment of (truth x monotone sensitivity) is pulled late whatever the truth's shape. The control
    bounds the bias; it does not remove it, and it cannot separate "sensitivity is nearly flat" from
    "the last layers genuinely do nothing". Both explain a low last-layer rate.

    VERDICT ON R12: UNVERIFIED. Not OVERTURNED -- the shape control is real evidence the bias is not
    running the profile. Not CONFIRMED -- the confound was never controlled and points exactly the
    way the winning hypothesis points. UNVERIFIED is not an acquittal.
    """
    out = {}
    for m in ('qwen2.5-1.5b', 'qwen2.5-3b'):
        f = HERE / 'R10_exhaustive' / 'results' / f'r10_exhaustive_{m}.json'
        if not f.exists():
            return None
        t = json.load(open(f))
        L = {int(k): v for k, v in t['layers'].items()}
        NL = t.get('n_layers', len(L))
        slo, shi = t['sham_band']
        sham = [v for x in range(slo, shi + 1) for v in L[x]['per_head'].values()]
        mus = sum(sham) / len(sham)
        fs = 2 * math.sqrt(sum((v - mus) ** 2 for v in sham) / (len(sham) - 1))
        rate = {x: sum(1 for v in L[x]['per_head'].values() if abs(v - mus) > fs)
                / len(L[x]['per_head']) for x in range(NL)}
        tot = sum(rate.values())
        pk = max(rate, key=lambda x: rate[x])
        out[m] = {'NL': NL, 'centroid': sum(x * q for x, q in rate.items()) / tot,
                  'peak_layer': pk, 'peak_rate': rate[pk],
                  'last_layer_rate': rate[NL - 1],
                  'n_layers_above_last': sum(1 for x in range(NL) if rate[x] > rate[NL - 1]),
                  'downstream_readers_last': 0, 'downstream_readers_L0': NL - 1}
    # magnitude profile of the primary model, for the depth trend
    t = json.load(open(HERE / 'R10_exhaustive' / 'results' /
                       'r10_exhaustive_qwen2.5-1.5b.json'))
    L = {int(k): v for k, v in t['layers'].items()}
    NH = len(L[0]['per_head'])
    NL = len(L)
    allv = [L[x]['per_head'][str(h)] for x in L for h in range(NH)]
    mu = sum(allv) / len(allv)
    prof = [sum(abs(L[x]['per_head'][str(h)] - mu) for h in range(NH)) / NH for x in range(NL)]
    out['profile_1_5b'] = prof
    out['spearman_layer_vs_magnitude_all'] = _spearman(list(range(NL)), prof)
    out['spearman_layer_vs_magnitude_band'] = _spearman(list(range(14, NL)), prof[14:])
    out['early_L0_6'] = sum(prof[0:7]) / 7
    out['late_L21_27'] = sum(prof[21:28]) / 7
    out['late_over_early'] = (sum(prof[21:28]) / 7) / (sum(prof[0:7]) / 7)
    return out


def selection_vs_effect():
    """The eight audited heads were selected by ATTENTION and measured by ABLATION. Do those agree?

    Reading the source experiment rather than my own note about it: E132 scored `room_att` and
    `name_att` over ALL 336 heads and took the top by an attention ratio; E132b then causally tested
    seven of those plus L22H7, which ranked FIRST on room attention. So the audited set is
    "the heads attention picked", and the audit measures them with ablation.

    Over the 168 band heads, same model, same items, same vocabulary:

        Spearman(|centred ablation|, room attention) = -0.19
        Spearman(|centred ablation|, name attention) = -0.40

    BOTH NEGATIVE. The two instruments do not merely fail to agree; they mildly anti-correlate. The
    head ablation ranks 9th (L15H7) is 168th of 168 on BOTH attention criteria.

    THIS IS NOT A DISCOVERY AND THE PAGE SAYS SO. That attention is an unreliable proxy for causal
    importance is established background -- arXiv 2504.13752 (Cohen-Wang, Chuang, Madry) states it
    as such in its abstract. What is measured here is the MAGNITUDE on this task, and why it matters
    for this audit: the eight heads under audit were selected by exactly the proxy known to fail,
    which turns "the loudest heads were never identified" from a curiosity into a consequence with a
    named cause.

    POSITIVE CONTROL ON THAT LITERATURE QUERY: it returned one squarely relevant paper, so it was
    not silent -- but it also returned cloud removal and Boltzmann attention, so it is noisy and NO
    COMPLETENESS IS CLAIMED. The last time novelty was judged from memory here, one query refuted it.
    """
    a = HERE / 'R16_selection_vs_effect' / 'results' / 'e132_attention_scores.json'
    p10 = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    if not (a.exists() and p10.exists()):
        return None
    e = json.load(open(a))
    t = json.load(open(p10))
    L = {int(k): v for k, v in t['layers'].items()}
    NH = e['NH']
    band = [(x, h) for x in range(14, 28) for h in range(NH)]
    vals = [L[x]['per_head'][str(h)] for x, h in band]
    mu = sum(vals) / len(vals)
    abl = {k: abs(L[k[0]]['per_head'][str(k[1])] - mu) for k in band}
    ra = {k: e['room_att'][k[0]][k[1]] for k in band}
    na = {k: e['name_att'][k[0]][k[1]] for k in band}
    A = [abl[k] for k in band]
    r_abl = sorted(band, key=lambda k: -abl[k])
    r_room = sorted(band, key=lambda k: -ra[k])
    r_name = sorted(band, key=lambda k: -na[k])
    # SIGNED AS WELL AS ABSOLUTE, because |.| throws away the thing this project already showed
    # matters -- 100 positive against 68 negative in this band, and 7 of the 9 clearing heads
    # clearing by HELPING. A reader given only a negative number on |drop| will fill in "so
    # high-attention heads help when ablated". They do not. The signed correlation is THREE TIMES
    # weaker, so the anti-correlation is about MAGNITUDE: attention picks heads that do LESS, in
    # either direction.
    S = [d - mu for d in (L[x]['per_head'][str(h)] for x, h in band)]

    def quartiles(att):
        order = sorted(band, key=lambda k: att[k])
        q = len(order) // 4
        out = []
        for i in range(4):
            grp = order[i * q:(i + 1) * q] if i < 3 else order[3 * q:]
            sg = [L[k[0]]['per_head'][str(k[1])] - mu for k in grp]
            out.append({'q': i + 1, 'n': len(grp), 'mean_signed': sum(sg) / len(sg),
                        'n_pos': sum(1 for v in sg if v > 0),
                        'n_neg': sum(1 for v in sg if v < 0)})
        return out

    return {'n_band': len(band),
            'spearman_room': _spearman(A, [ra[k] for k in band]),
            'spearman_name': _spearman(A, [na[k] for k in band]),
            'spearman_room_signed': _spearman(S, [ra[k] for k in band]),
            'spearman_name_signed': _spearman(S, [na[k] for k in band]),
            'room_quartiles': quartiles(ra), 'name_quartiles': quartiles(na),
            'top_ablation': [{'head': f'L{x}H{h}', 'abl': abl[(x, h)],
                              'room_rank': r_room.index((x, h)) + 1,
                              'name_rank': r_name.index((x, h)) + 1}
                             for x, h in r_abl[:10]],
            'top5_room_ablation_ranks': [r_abl.index(k) + 1 for k in r_room[:5]],
            'top5_name_ablation_ranks': [r_abl.index(k) + 1 for k in r_name[:5]],
            'L22H7_room_rank_source': e['pc_L22H7_room_rank'],
            'n_selected_by_E132b': 7, 'n_added_externally': 1}


def r2_task_audit():
    """R2's task has R1's degeneracy, and its head-selection criterion is defined BY the degeneracy.

    R13 audited the room task and found it fixed-position. That lesson had never been transferred.
    R2's sequences are `core + core` with `len(core) = T = 64` fixed on every sequence, and the
    readout is the mean log-probability of the true next token across the second copy.

        At position T+i the correct next token is core[i+1], which sits at absolute position i+1.
        The distance back is (T+i) - (i+1) + 1 = T. THE ANSWER IS ALWAYS EXACTLY T POSITIONS BACK.

    A head that attends at a constant distance solves the task perfectly, with no content matching.
    The tokens are uniform random ids from a 39000-wide range, so there is no lexical shortcut --
    but there is a POSITIONAL one, and the task cannot distinguish it from prefix-matching because
    the two agree on every sequence it contains.

    AND THE SELECTION CRITERION IS THE SAME QUANTITY. `induction_scores` scores attention from
    position i to position i-T+1 -- a FIXED OFFSET -- and its own docstring calls that a
    "prefix-matching score". The name asserts content matching; the computation measures distance.
    A label carried where a derivation was needed, in the runner that selects the heads.

    WHAT THIS DOES NOT BREAK: every comparison between the top-k heads and random-k heads. They face
    the same task, so R2's floor, its 4-of-5 clearing count and its effect sizes are unaffected.

    WHAT IT BREAKS: calling them prefix-matching or induction heads as a claim about CONTENT. On
    this task that is not established, and the repair is the same shape as R14's -- vary T per
    sequence, so a constant-distance head fails and a content-matching head does not.
    """
    p = HERE / 'R2_inversion' / 'run.py'
    if not p.exists():
        return None
    src = p.read_text()
    import re as _re
    mT = _re.search(r'^T = (\d+)', src, _re.M)
    mN = _re.search(r'^N_SEQ = (\d+)', src, _re.M)
    mK = _re.search(r'^K = (\d+)', src, _re.M)
    lo_hi = _re.search(r'lo, hi = (\d+), min\(tok\.vocab_size - (\d+), (\d+)\)', src)
    return {'T': int(mT.group(1)) if mT else None,
            'n_seq': int(mN.group(1)) if mN else None,
            'k': int(mK.group(1)) if mK else None,
            'vocab_lo': int(lo_hi.group(1)) if lo_hi else None,
            'vocab_hi': int(lo_hi.group(3)) if lo_hi else None,
            'period_is_constant': bool(mT),
            'offset_to_answer': int(mT.group(1)) if mT else None,
            'selection_uses_fixed_offset': 'idx - T + 1' in src,
            'selection_called_prefix_matching': 'prefix-matching score' in src}


def r2_centred():
    """R2 has never been audited the way R1 has -- and the centring correction is the test.

    Every lesson of the last twenty steps was applied to R1's task and none to R2's. The one that
    flipped R1's headline count is the cheapest to transfer: is R2's null centred at zero?

    IT IS NOT, ON ANY OF THE FIVE, AND ALL IN THE SAME DIRECTION. The null mean is negative
    everywhere, from -0.19 to -0.62 standard deviations -- much further off-centre than R1's band
    at +0.20. It makes sense in the opposite direction too: ablating random heads HURTS induction
    logprob on average, while on the room task ablating random late heads HELPED the margin.

    AND `d_top` IS NEGATIVE TOO, so centring SHRINKS the distance and makes clearing HARDER. The
    count survives anyway: 4 of 5 either way, because the effects are 6.5x to 18.7x the floor and
    the correction moves them by hundredths.

    WHICH IS THE SHARPEST AVAILABLE STATEMENT OF WHY R1 AND R2 DISAGREED, and the repository has
    approached it three times without putting it this way:

        R1's eight, against the centred exhaustive floor:  1.06 0.37 0.18 0.17 0.07 0.02 0.02 0.01
        R2's four valid cells:                             1.20 6.50 14.79 18.68

    THE TWO DISTRIBUTIONS BARELY TOUCH. The rounds do not disagree about method; they disagree
    about effect size, by an order of magnitude. phi-3.5-mini is the exception in both -- 0.12 here,
    and refused outright in R10 for a readout that scores two of four answers on word fragments.
    """
    import glob as _g
    rows = []
    for f in sorted(_g.glob(str(HERE / 'R2_inversion' / 'results' / '*.json'))):
        d = json.load(open(f))
        nl = d.get('null')
        if not nl:
            continue
        mu, sd, dt = nl['mean'], nl['sd'], d['d_top']
        rows.append({'model': d['model'], 'd_top': dt, 'null_mean': mu, 'floor_2sd': 2 * sd,
                     'mean_over_sd': mu / sd,
                     'x_uncentred': abs(dt) / (2 * sd),
                     'x_centred': abs(dt - mu) / (2 * sd)})
    if not rows:
        return None
    pe = r1_prior_effects()
    r1x = []
    p10 = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    if pe and p10.exists():
        t = json.load(open(p10))
        L = {int(k): v for k, v in t['layers'].items()}
        band = [v for x in range(14, 28) for v in L[x]['per_head'].values()]
        m = sum(band) / len(band)
        sd = math.sqrt(sum((v - m) ** 2 for v in band) / (len(band) - 1))
        r1x = sorted((abs(e['drop'] - m) / (2 * sd) for e in pe['effects'].values()), reverse=True)
    valid = [r for r in rows if r['x_centred'] > 1]
    return {'rows': rows, 'n': len(rows),
            'n_clear_uncentred': sum(r['x_uncentred'] > 1 for r in rows),
            'n_clear_centred': sum(r['x_centred'] > 1 for r in rows),
            'all_nulls_negative': all(r['null_mean'] < 0 for r in rows),
            'mean_over_sd_min': min(r['mean_over_sd'] for r in rows),
            'mean_over_sd_max': max(r['mean_over_sd'] for r in rows),
            'r2_min_clearing': min(r['x_centred'] for r in valid) if valid else None,
            'r2_max_clearing': max(r['x_centred'] for r in valid) if valid else None,
            'r1_x_centred': r1x, 'r1_max': r1x[0] if r1x else None}


def taxonomy_power():
    """Does the pre-registered taxonomy VERDICT carry information, or only the row count?

    `ONE-JOINT-DOMINATES` fires when any bin reaches 8. That is an ABSOLUTE threshold on a ledger
    that grows every session, and the pre-registration said so at n=31 -- and then nobody measured
    how uninformative it had become.

    PERMUTATION TEST, labels assigned uniformly at random over the six bins:

        n= 22   the verdict fires 10.8% of the time     -- informative
        n= 31   67.0%                                   -- already mostly inevitable
        n>=45   100.0%                                  -- carries nothing

    At n=69 it fires on 20000 of 20000 random relabelings. THE VERDICT IS DEAD AS EVIDENCE and is
    reported as such rather than deleted, because a pre-registered gate that stops discriminating
    is a finding about the gate.

    WHAT REPLACES IT is the distribution, which IS informative: chi-square 20.65 against a uniform
    null gives a permutation p of 0.00055 (11 of 20000). The two SMALL bins carry it -- INTERVENTION
    at 2 and UNCLASSIFIED at 4 against an expected 11.5 -- not the large one the verdict watches.
    The right question was never "does a bin dominate" but "is the partition uneven", and the answer
    lives at the opposite end of the distribution from where the threshold was pointed.

    STILL SELF-REPORTED: the rows are the author's, the bins are the author's, and the classification
    is the author's. This measures whether the partition is uneven, not whether it is correct.
    """
    import random as _r
    from collections import Counter
    p = HERE / 'defects.json'
    if not p.exists():
        return None
    d = json.load(open(p))['defects']
    bins = sorted({r['bin'] for r in d})
    n = len(d)
    obs = Counter(r['bin'] for r in d)
    exp = n / len(bins)

    def verdict(c):
        big = [k for k, v in c.items() if v >= 2]
        unc = c.get('UNCLASSIFIED', 0)
        mx = max(c.values())
        if mx >= 8:
            return 'ONE-JOINT-DOMINATES'
        if unc >= 5 or not big:
            return 'THIRTEEN-ONE-OFFS'
        if len(big) >= 3 and unc <= 2:
            return 'TAXONOMY-EXISTS'
        return 'AMBIGUOUS'

    # THE VERDICT'S OWN TRAJECTORY, replayed row by row. It discriminated five ways in the first
    # 26 rows and has been frozen since -- the test worked, and then the ledger grew past it.
    hist, run = [], Counter()
    unreach_n = None
    for i, r in enumerate(d, 1):
        run[r['bin']] += 1
        v = verdict(run)
        if not hist or hist[-1]['verdict'] != v:
            hist.append({'n': i, 'verdict': v, 'unclassified': run.get('UNCLASSIFIED', 0),
                         'largest': max(run.values())})
        if unreach_n is None and run.get('UNCLASSIFIED', 0) > 2:
            unreach_n = i
    # Which verdicts can still be returned, given UNCLASSIFIED and the bin counts only GROW?
    reachable = ['ONE-JOINT-DOMINATES']          # fires now and cannot stop
    probe = Counter(obs)
    probe['UNCLASSIFIED'] += 1
    if verdict(probe) == 'THIRTEEN-ONE-OFFS':
        reachable.append('THIRTEEN-ONE-OFFS')
    chi = sum((obs.get(b, 0) - exp) ** 2 / exp for b in bins)
    rng = _r.Random(11)
    T = 20000
    fires = 0
    ge = 0
    for _ in range(T):
        c = Counter(rng.choice(bins) for _ in range(n))
        fires += verdict(c) == 'ONE-JOINT-DOMINATES'
        ge += sum((c.get(b, 0) - exp) ** 2 / exp for b in bins) >= chi
    # A SEPARATE, INDEPENDENTLY SEEDED RNG PER POINT. The first version continued the main loop's
    # generator, whose state depends on how many draws it consumed -- which is n -- so every added
    # defect row silently shifted this curve. A generated number that moves when UNRELATED data
    # moves is the same defect class as a hand-copied one: it cannot be checked against anything.
    curve = {}
    for m in (22, 31, 45, 69):
        c_rng = _r.Random(1000 + m)
        h = sum(1 for _ in range(4000)
                if verdict(Counter(c_rng.choice(bins) for _ in range(m)))
                == 'ONE-JOINT-DOMINATES')
        curve[m] = 100 * h / 4000
    return {'n': n, 'n_bins': len(bins), 'observed': dict(obs), 'expected_per_bin': exp,
            'verdict': verdict(obs), 'n_draws': T,
            'verdict_fires_under_random_labels_pct': 100 * fires / T,
            'chi_square': chi, 'chi_square_p': ge / T,
            'fires_by_n': curve,
            'smallest_bins': sorted(obs.items(), key=lambda kv: kv[1])[:2],
            # REACHABILITY, which is sharper than the permutation test above and was found by
            # asking what ELSE the verdict function can return. UNCLASSIFIED never decreases --
            # rows are never removed -- and TAXONOMY-EXISTS requires it <= 2, so that verdict
            # became PERMANENTLY UNREACHABLE the moment it hit 3. THIRTEEN-ONE-OFFS needs it >= 5,
            # but the >= 8 branch is tested first and masks it. The verdict space collapsed to ONE
            # reachable outcome at n=26, forty-four rows ago.
            'verdict_history': hist,
            'unclassified_now': obs.get('UNCLASSIFIED', 0),
            'taxonomy_exists_unreachable_from_n': unreach_n,
            'reachable_verdicts': reachable}


def r15_design():
    """The design defect in a run that has NOT happened, caught from an earlier run's records.

    R15 would re-run the exhaustive scan on R14's shuffled task. The runner keeps only items the
    model answers CORRECTLY -- and under shuffling 24 of 120 are wrong, position-dependently. The
    kept population would shift 10.2 points toward the ends of the list, i.e. toward exactly the
    positions the model already handles best, and the resulting floor would be the easy half's floor
    with nothing in the output to say so.

    THE FIX COSTS NOTHING. Drop the filter: a `drop` is a change in MARGIN, which is defined whether
    or not the argmax is correct. And the filter has never been load-bearing -- R14 measured
    accuracy 1.000 over 120 consecutive seeds on the original task, so IT HAS NEVER REJECTED A
    SINGLE ITEM there. Dropping it changes no existing number and prevents a 10.2-point selection
    effect on the new one.

    First time in this project a design was attacked BEFORE the compute rather than after.
    """
    p = HERE / 'R14_position_vs_binding' / 'results' / 'r14_probe_qwen2.5-1.5b.json'
    if not p.exists():
        return None
    d = json.load(open(p))
    rows = d['rows']
    offered, kept = {}, {}
    for r in rows:
        L = r['answer_line_shuffled']
        offered[L] = offered.get(L, 0) + 1
        if r['shuf_ok']:
            kept[L] = kept.get(L, 0) + 1
    n_all, n_kept = len(rows), sum(kept.values())
    ends = (0, 1, 6, 7)
    oe = 100 * sum(offered.get(L, 0) for L in ends) / n_all
    ke = 100 * sum(kept.get(L, 0) for L in ends) / n_kept
    return {'n_offered': n_all, 'n_kept': n_kept,
            'ends_offered_pct': oe, 'ends_kept_pct': ke, 'skew_points': ke - oe,
            'filter_ever_rejected_on_original': d['accuracy_original'] < 1.0,
            'accuracy_original': d['accuracy_original'],
            'middle_offered_pct': 100 - oe, 'middle_kept_pct': 100 - ke,
            'by_line': {L: {'offered': offered.get(L, 0), 'kept': kept.get(L, 0),
                            'offered_pct': 100 * offered.get(L, 0) / n_all,
                            'kept_pct': 100 * kept.get(L, 0) / n_kept,
                            'skew': (100 * kept.get(L, 0) / n_kept
                                     - 100 * offered.get(L, 0) / n_all)}
                        for L in sorted(offered)}}


def r12():
    """The cross-model separator: is the hump at a fixed LAYER or a fixed DEPTH FRACTION?

    28 layers versus 36. At 28 the two coincide; at 36 they are five layers apart, which is the
    whole reason a second model separates worlds the first cannot. Thresholds were committed while
    the run was still executing and re-derived under the corrected centring rule before it produced
    a file.

        observed centroid   22.833   bootstrap 95% CI [21.52, 24.01] over 2000 head resamples
        ABSOLUTE predicted  17.23    OUTSIDE the interval
        RELATIVE predicted  22.34    INSIDE  the interval

    RELATIVE. The centroid sits at 0.6383 of the way through qwen2.5-1.5b and 0.6524 through
    qwen2.5-3b. An interval that EXCLUDES the rival is stronger than a point crossing a threshold,
    and the pre-registration asked only for the point.

    WHAT DOES NOT TRANSFER IS THE SHAPE, and that is the more useful half. qwen2.5-1.5b's profile is
    a clean unimodal hump peaking at 83%; qwen2.5-3b's has three near-equal local maxima (56, 50,
    50%) and a dead zone across L1-L11. With 16 heads per layer a rate carries about +-12 points, so
    THE PEAK LOCATION IS NOT RESOLVED -- the four highest layers are statistically indistinguishable.
    The verdict rests on the centroid, which averages over all 36 layers; no peak-layer claim is made
    for this model.
    """
    import random as _r
    p = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-3b.json'
    if not p.exists():
        return None
    t = json.load(open(p))
    L = {int(k): v for k, v in t['layers'].items()}
    NL = t['n_layers']
    slo, shi = t['sham_band']
    sham = [v for x in range(slo, shi + 1) for v in L[x]['per_head'].values()]
    mus = sum(sham) / len(sham)
    fs = 2 * math.sqrt(sum((v - mus) ** 2 for v in sham) / (len(sham) - 1))

    def cent(pick=None):
        r = {}
        for x in range(NL):
            vals = list(L[x]['per_head'].values())
            if pick:
                vals = [vals[i] for i in pick(len(vals))]
            r[x] = sum(1 for v in vals if abs(v - mus) > fs) / len(vals)
        tot = sum(r.values())
        return (sum(x * q for x, q in r.items()) / tot if tot else float('nan')), r

    c, rate = cent()
    rng = _r.Random(7)
    boot = sorted(x for x in (cent(lambda n: [rng.randrange(n) for _ in range(n)])[0]
                              for _ in range(2000)) if x == x)
    lo95, hi95 = boot[int(.025 * len(boot))], boot[int(.975 * len(boot))]
    nz = [q for q in rate.values() if q > 0]
    mx = max(rate.values())
    peak = [x for x, q in rate.items() if q == mx]
    n_per = len(L[0]['per_head'])
    top = sorted(rate.items(), key=lambda kv: -kv[1])[:4]
    return {'model': t['model'], 'n_layers': NL, 'n_heads_per_layer': n_per,
            'sham_band': [slo, shi], 'sham_floor': fs,
            'centroid': c, 'centroid_ci95_lo': lo95, 'centroid_ci95_hi': hi95,
            # R18's 1.0-layer deadband is justified against this half-width, so it must
            # be emitted rather than computed by a reader from two rounded endpoints.
            'centroid_ci95_halfwidth': (hi95 - lo95) / 2,
            'depth_fraction': c / (NL - 1),
            'absolute_prediction': 17.2347, 'relative_prediction': 22.3413,
            'absolute_inside_ci': lo95 <= 17.2347 <= hi95,
            'relative_inside_ci': lo95 <= 22.3413 <= hi95,
            'verdict': 'ABSOLUTE' if c < 19.5 else 'RELATIVE' if c > 20.5 else 'AMBIGUOUS',
            'peak_layers': peak, 'peak_rate': mx,
            'max_over_min_nonzero': mx / min(nz),
            'kill_fired': not (mx / min(nz) >= 2 and peak[0] not in (0, NL - 1)),
            'rate_se_at_half': math.sqrt(0.25 / n_per),
            'top4': [{'layer': x, 'rate': q, 'ci95': 1.96 * math.sqrt(q * (1 - q) / n_per)}
                     for x, q in top],
            'rate_by_layer': {x: q for x, q in sorted(rate.items())}}


def r14():
    """Does the model bind the name, or copy line 0? Pre-registered before the probe ran.

    R13 showed the task cannot tell those apart. R14 shuffles the fact lines so it can. The
    pre-registered verdict is MIXED -- accuracy 1.000 unshuffled, 0.800 shuffled, against
    thresholds of 0.900 for BINDING and 0.350 for POSITION -- and the CONFOUND CONTROL is the
    result, because it was built to separate two shapes and returned a third.

        position-copying predicted a STEP: line 0 perfect, the rest at chance 0.25
        a primacy effect predicted a SMOOTH DECAY with distance from the start
        what came back is a U -- primacy AND recency, a serial-position curve

    Every line is above chance; the worst is 0.57, which is 2.3x chance with a lower 95% bound of
    0.31. THE MODEL IS NOT COPYING POSITION 0, and across two earlier steps I let R13's finding
    hang as an implication that it might be. The pre-registration named that outcome as a kill
    pointing at my own steps and required it be reported as loudly as the other. It fired.
    """
    p = HERE / 'R14_position_vs_binding' / 'results' / 'r14_probe_qwen2.5-1.5b.json'
    if not p.exists():
        return None
    d = json.load(open(p))
    bl = {int(k): v for k, v in d['accuracy_by_answer_line'].items()}
    ends, mid = (0, 1, 6, 7), (2, 3, 4, 5)

    def agg(ks):
        n = sum(bl[k]['n'] for k in ks if k in bl)
        c = sum(round(bl[k]['acc'] * bl[k]['n']) for k in ks if k in bl)
        q = c / n
        return {'n': n, 'correct': c, 'acc': q, 'ci95': 1.96 * math.sqrt(q * (1 - q) / n)}

    e, m = agg(ends), agg(mid)
    sed = math.sqrt((e['ci95'] / 1.96) ** 2 + (m['ci95'] / 1.96) ** 2)
    worst = min(bl.items(), key=lambda kv: kv[1]['acc'])
    return {'model': d['model'], 'n_items': d['n_items'], 'chance': d['chance'],
            'accuracy_original': d['accuracy_original'],
            'accuracy_shuffled': d['accuracy_shuffled'],
            'binding_ratio_threshold': d['binding_ratio_threshold'],
            'position_ceiling': d['position_ceiling'], 'verdict': d['verdict'],
            'by_line': {k: v['acc'] for k, v in sorted(bl.items())},
            'ends': e, 'middle': m,
            'ends_minus_middle': e['acc'] - m['acc'],
            'ends_minus_middle_z': (e['acc'] - m['acc']) / sed,
            'worst_line': worst[0], 'worst_acc': worst[1]['acc'],
            'worst_over_chance': worst[1]['acc'] / d['chance'],
            'all_lines_above_chance': all(v['acc'] > d['chance'] for v in bl.values())}


def task_audit():
    """WHAT DOES THE TASK ACTUALLY REQUIRE? Twelve rounds audited the measurement and none audited this.

    Every runner picks its query with

        single = [p for p in PERSONS if p is one token under this tokenizer]
        q      = next(p for p in single if p in bindings)

    and `bindings` assigns EVERY person, so `q == single[0]` on every item. For qwen2.5 all eight
    persons are single-token, so the query is always `Alice`. The prompt's fact lines are built in
    module-level `PERSONS` order, so Alice's fact is always line 0.

        THE CORRECT ANSWER IS ALWAYS THE ROOM NAMED IN THE FIRST SENTENCE.

    The answer itself varies -- Alice's room is near-uniform over the four across 400 seeds -- so
    the task is not degenerate in its LABEL. It is degenerate in its STRUCTURE: a model that learned
    "copy the room from line 0" scores 100% without ever matching a name.

    WHAT THIS DOES NOT BREAK. Every comparison BETWEEN heads: all of them face the same task, so the
    floor, the ranking, the counts, the item-noise and the centring are unaffected as statements
    about this task. The methodological findings stand entirely.

    WHAT IT BREAKS. The description. This is a FIXED-POSITION RETRIEVAL task, not a binding task,
    and the eight published effects were identified on it. L22H7 may be copying from position 0
    rather than resolving a name -- and this task cannot tell those apart, because the two
    strategies agree on every item it contains.

    THE META-LESSON, which is the part worth keeping: an elaborate apparatus was built to audit
    MEASUREMENTS, and none of it was ever pointed at the thing being measured. Sixty-one logged
    defects, four detectors, twelve rounds -- and the task's own structure was read for the first
    time in the thirteenth.
    """
    import random as _r
    # NARROW AND LOUD. The first version wrapped this in `except Exception` and returned None --
    # and swallowed a NameError (headline.py had no `import sys`), so the whole section vanished
    # from the output with no error. A guard that turns a bug into an absence is the exact pattern
    # this repository keeps finding in other people's checks, and it hid mine for one run.
    sys.path.insert(0, str(HERE))
    try:
        from task import PERSONS, ROOMS, OBJECTS
    except ImportError as e:
        raise SystemExit(f"REFUSED: task.py is not importable ({e}). The task audit cannot run, "
                         f"and reporting nothing would look identical to reporting no problem.")

    def bind(seed, rooms):
        r = _r.Random(seed)
        ps, obs = list(PERSONS), list(OBJECTS)
        assigned = (list(rooms) * 4)[:len(ps)]
        r.shuffle(ps)
        r.shuffle(obs)
        r.shuffle(assigned)
        return {ps[i]: (obs[i], assigned[i]) for i in range(len(ps))}

    counts = {}
    for s in range(3000, 3400):
        rm = bind(s, ROOMS)[PERSONS[0]][1]
        counts[rm] = counts.get(rm, 0) + 1
    return {'query_person': PERSONS[0], 'query_line_index': PERSONS.index(PERSONS[0]),
            'n_persons': len(PERSONS), 'n_rooms': len(ROOMS),
            'answer_room_counts_over_400_seeds': counts,
            'answer_min_share_pct': 100 * min(counts.values()) / sum(counts.values()),
            'answer_max_share_pct': 100 * max(counts.values()) / sum(counts.values()),
            'trivial_strategy_accuracy_pct': 100.0,
            # IS THE DEGENERACY UNIFORM ACROSS MODELS? The query is `single[0]`, which depends on
            # the TOKENIZER -- so a model where Alice is not a single content token would be asked
            # about a different person at a different LINE, and R1's cross-model ratio would be
            # comparing two different fixed-position tasks. Probed with the runners' own convention
            # (R13_task_audit/probe_query_position.py, tokenizers only, no weights): all four
            # models, both vocabularies, query Alice at line 0. The degeneracy is UNIFORM, so the
            # cross-model comparisons stay commensurable -- and the degeneracy is everywhere.
            'cross_model': _query_positions()}


def _query_positions():
    p = HERE / 'R13_task_audit' / 'results' / 'tokenizer_query_positions.json'
    if not p.exists():
        return None
    d = json.load(open(p))
    return {'n_cells': d['n_cells'], 'distinct_query_lines': d['distinct_query_lines'],
            'uniform_across_models': d['uniform_across_models'], 'the_line': d['the_line'],
            'n_single_by_model': {r['model']: r['n_single_token_persons']
                                  for r in d['rows'] if r['vocabulary'] == 'original'},
            'rows': d['rows']}


def input_replication():
    """Do the eight numbers this whole project is ABOUT reproduce under a different runner?

    Never checked. The eight were lifted from experiment E132b's `drop` field and every round since
    has ranked, floored and scoped them without once asking whether a second implementation returns
    the same values. R10 measured ALL 336 heads on the same items in the same vocabulary, so the
    comparison was free the moment R10 existed.

    They agree to 3.6e-06 -- float32 nondeterminism. Two separately written runners agree on the
    hook, the item filter, the margin definition and the drop definition, so the quantities this
    repository compares are commensurable. That is Closure, it had never been done, and it could
    have failed.

    THE METHODOLOGICAL POINT IS IN THE SAME COMPARISON. E132b asked about 8 heads; R10 asked about
    336, using the same code path and the same items. The ONLY difference is how many heads were
    asked about -- and asking about all of them is what produced every finding of the last four
    steps, including that the eight were not the interesting ones. Cost: one 16-minute job on a
    consumer GPU for a 1.5B model.
    """
    import re as _re
    pe = r1_prior_effects()
    p = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    if not (pe and p.exists()):
        return None
    t = json.load(open(p))
    L = {int(k): v for k, v in t['layers'].items()}
    rows = []
    for h, e in sorted(pe['effects'].items(), key=lambda kv: -kv[1]['abs']):
        m = _re.match(r'L(\d+)H(\d+)', h)
        x, hh = int(m.group(1)), int(m.group(2))
        r = L[x]['per_head'][str(hh)]
        rows.append({'head': h, 'e132b': e['drop'], 'r10': r, 'abs_diff': abs(e['drop'] - r)})
    n_heads_exhaustive = sum(len(v['per_head']) for v in L.values())
    return {'n': len(rows), 'max_abs_diff': max(r['abs_diff'] for r in rows),
            'margin_e132b': abs(pe['base_margin']), 'margin_r10': abs(t['base_margin']),
            'margin_abs_diff': abs(abs(pe['base_margin']) - abs(t['base_margin'])),
            'n_items': pe['n_items'], 'rows': rows,
            'n_heads_hypothesis_driven': len(rows),
            'n_heads_exhaustive': n_heads_exhaustive,
            'exhaustive_over_hypothesis': n_heads_exhaustive / len(rows)}


def rank_vs_role():
    """Where do the hypothesis-identified heads sit in the EXHAUSTIVE ablation ranking?

    Nine rounds compared each published effect against a floor and asked "does it clear?". None
    asked the cheaper question the exhaustive scan makes free: **of all 168 band heads, which ones
    clear, and are the published ones among them?**

    They are not. Nine heads clear the exhaustive floor at k=1, up to 2.54x, and ZERO of the eight
    published heads is one of them. The independently proven copy head ranks 56 of 168.

    SO THE PREVIOUS LEAD -- "the single head is the wrong unit" -- IS WRONG TOO. Single-head
    ablation resolves effects on this task perfectly well. What it does not do is rank the heads an
    interpretability hypothesis picked anywhere near the top.

    AND THE SYMMETRIC ERROR MUST NOT BE COMMITTED HERE. Five of the nine have POSITIVE drop:
    removing them IMPROVES the margin, L18H0 by +1.2361. A large ablation effect is not evidence of
    a role -- it is evidence that removal matters, in either direction. The exhaustive scan yields a
    list of heads whose removal moves the answer, NOT a list of heads that implement the task.
    Reading it as the second would be exactly the inference this repository exists to refuse.
    """
    import re as _re
    p = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    pe = r1_prior_effects()
    if not (p.exists() and pe):
        return None
    t = json.load(open(p))
    L = {int(k): v for k, v in t['layers'].items()}
    lo, hi = 14, 27
    band = [(x, int(h), v) for x in range(lo, hi + 1) for h, v in L[x]['per_head'].items()]

    def sd(xs):
        m = sum(xs) / len(xs)
        return math.sqrt(sum((y - m) ** 2 for y in xs) / (len(xs) - 1))

    vals = [v for _, _, v in band]
    floor = 2 * sd(vals)
    # CENTRED ON THE NULL'S OWN MEAN (+0.0479). The uncentred form is kept beside it because
    # correcting the k=1 centring moved this count 9 -> 10 AND put a published head (L16H3) into
    # the clearing set for the first time -- which contradicts the sentence this section led with.
    mu_band = sum(vals) / len(vals)
    order = sorted(band, key=lambda x: -abs(x[2] - mu_band))
    clear = [x for x in order if abs(x[2] - mu_band) > floor]
    clear_uncentred = [x for x in band if abs(x[2]) > floor]
    eight = {(int(m.group(1)), int(m.group(2))): h
             for h in pe['effects'] if (m := _re.match(r'L(\d+)H(\d+)', h))}
    ranks = [{'head': eight[(x, h)], 'rank': i, 'drop': v,
              'x_floor': abs(v - mu_band) / floor}
             for i, (x, h, v) in enumerate(order, 1) if (x, h) in eight]
    return {
        'n_band_heads': len(band), 'floor_2sd': floor,
        'n_clear': len(clear), 'pct_clear': 100 * len(clear) / len(band),
        'n_clear_UNCENTRED': len(clear_uncentred),
        # IS THE COUNT ITSELF INFORMATIVE? No. Beyond 2sd a normal gives 4.55% and a Laplace 5.91%;
        # the observed 5.36% sits between them. Nine heads in the tail is what a heavy-tailed
        # distribution of 168 numbers gives for free, and the excess kurtosis is +7.43, so `2*sd`
        # is a normal-theory cut on a distribution that is nothing like normal. The COUNT
        # establishes nothing; the RANKING below needs no threshold and survives untouched.
        'expected_beyond_2sd_normal': len(band) * math.erfc(2 / math.sqrt(2)),
        'expected_beyond_2sd_laplace': len(band) * math.exp(-2 * math.sqrt(2)),
        'excess_kurtosis': (sum((v - sum(w for _, _, w in band) / len(band)) ** 4
                                for _, _, v in band) / len(band)) /
                           ((sum((v - sum(w for _, _, w in band) / len(band)) ** 2
                                 for _, _, v in band) / len(band)) ** 2) - 3,
        # LEAVE-ONE-OUT: each head judged by a null that excludes it. It changes nothing at n=168 --
        # reported because a null containing its own test point is the defect this repository found
        # at k=1, and a check that came back clean is still a check that ran.
        'n_clear_leave_one_out': sum(
            1 for x, h, v in band
            if abs(v) > 2 * sd([w for a, b, w in band if not (a == x and b == h)])),
        'clearing_heads': [{'head': f'L{x}H{h}', 'drop': v,
                            'x_floor': abs(v - mu_band) / floor,
                            'direction': 'ablation HELPS' if v > 0 else 'ablation hurts'}
                           for x, h, v in clear],
        'n_clear_positive': sum(v > 0 for _, _, v in clear),
        'n_published_among_clearing': sum((x, h) in eight for x, h, _ in clear),
        'published_ranks': sorted(ranks, key=lambda r: r['rank']),
        # THE DEPTH CONTROL, run because R9 established the floor GROWS with depth (rho +0.51 to
        # +0.73), so a ranking by RAW |drop| systematically favours deep heads -- and the eight
        # published heads sit at mean layer 18.1 while the raw top nine sit at 21.0. Ranking each
        # head against its OWN LAYER's sd removes that. It does not rescue them: the normalised top
        # nine are DEEPER still (21.8), and the published count among them is unchanged.
        # THE INVARIANCE IS THE RESULT. Which heads are "top" is normalisation-dependent -- the two
        # top-nines share only six members. That the published heads are in NEITHER is not.
        'ranks_by_layer_sd': sorted(
            [{'head': eight[(x, h)], 'rank': i, 'layer_sd_units': abs(v) / L[x]['sd']}
             for i, (x, h, v) in enumerate(
                 sorted(band, key=lambda r: -abs(r[2]) / L[r[0]]['sd']), 1)
             if (x, h) in eight], key=lambda r: r['rank']),
        'published_in_top9_by_layer_sd': sum(
            1 for x, h, _ in sorted(band, key=lambda r: -abs(r[2]) / L[r[0]]['sd'])[:9]
            if (x, h) in eight),
        'top9_overlap_between_normalisations': len(
            {(x, h) for x, h, _ in order[:9]} &
            {(x, h) for x, h, _ in sorted(band, key=lambda r: -abs(r[2]) / L[r[0]]['sd'])[:9]}),
        'mean_layer_published': sum(x for x, _ in eight) / len(eight),
        'mean_layer_top9_raw': sum(x for x, _, _ in order[:9]) / 9,
        'mean_layer_top9_norm': sum(
            x for x, _, _ in sorted(band, key=lambda r: -abs(r[2]) / L[r[0]]['sd'])[:9]) / 9,
        'copy_head_rank': next((r['rank'] for r in ranks if r['head'] == 'L22H7'), None),
        # PARTICIPATION RATIO per layer: 1 = one head carries everything, NH = all equal. It
        # separates "a layer with a dominant head" from "a layer whose effect is spread", and the
        # answer is layer-dependent, which is why a single global statement about "the right unit"
        # was always going to be wrong.
        'participation_ratio': {x: (sum(v * v for v in L[x]['per_head'].values()) ** 2 /
                                    sum((v * v) ** 2 for v in L[x]['per_head'].values()))
                                for x in range(lo, hi + 1)},
    }


def set_level_scale():
    """The circuit result on the SAME statistic as the head result -- because a percentile hides size.

    The front page's new lead says the k=5 COPY circuit is at the "0.0th percentile" of the null.
    With n=30 draws a percentile has 3.3% resolution: "0.0th" means "below all thirty" and nothing
    finer. It says the effect is extreme; it does not say by how much, and the sentence written
    beside it -- "Not marginal. Not inside anything." -- asserted a magnitude the percentile cannot
    carry. Committed one step after a step whose subject was overstatement.

    Put both on `|effect| / (2*sd of its own null)`, the statistic k=1 already uses:

        L22H7,  k=1 :  0.27x its floor
        COPY,   k=5 :  1.45x its floor

    That is the finding, and it survives -- but by 45%, not by an order of magnitude. The k=5 null
    sd is 2.02x the k=1 sd, so moving to five heads roughly DOUBLES the floor, and the circuit
    clears the larger floor anyway. Stated in numbers the claim is smaller and checkable; stated as
    "not inside anything" it was neither.
    """
    p = HERE / 'R1_noise_floor' / 'results' / 'prior_effects' / 'e132d_set_null.json'
    if not p.exists():
        return None
    d = json.load(open(p))
    n, out = d['null'], {}
    sd, mu, mn = n['sd'], n['mean'], n['min']
    for name, v in d['sets'].items():
        out[name] = {'drop': v['drop'], 'pct_in_null': v['pct_in_null'],
                     # UNCENTRED, kept only so the correction can be read against what it corrects.
                     'x_floor_2sd_UNCENTRED': abs(v['drop']) / (2 * sd),
                     # THE ONE CONVENTION. Centring this null (mean +0.1882) moves COPY from 1.45x
                     # to 1.65x, and the centred ratio is exactly |z|/2 -- so "x floor" and "z" were
                     # two names for the same quantity, one of them mis-centred. The page showed
                     # both side by side until 2026-07-28.
                     'x_floor_2sd': abs(v['drop'] - mu) / (2 * sd),
                     'z_from_null_mean': (v['drop'] - mu) / sd,
                     'sd_beyond_null_min': (mn - v['drop']) / sd}
    ib = item_noise_bound()
    k1_sd = (ib['band_floor_raw'] / 2) if ib else None
    return {'n_draws': d['n_draws'], 'percentile_resolution_pct': 100.0 / d['n_draws'],
            'null_mean': mu, 'null_sd': sd, 'null_min': mn, 'null_max': n['max'],
            # EMITTED because the prose quotes it. Computing 2*sd by hand in a sentence is how a
            # number reaches a page with no generator behind it -- the defect this file exists for.
            'floor_2sd': 2 * sd,
            'base_margin': abs(d['base_margin']), 'sets': out,
            'k1_exhaustive_sd': k1_sd,
            'k5_over_k1_sd': (sd / k1_sd) if k1_sd else None}


def item_noise_bound():
    """Is the floor HEAD CHOICE, or is it the finite item sample? And the distinction it forces.

    Every head's drop is a mean over the SAME 120 items, so between-head spread is
    `var(true head effects) + var(head-specific item-sampling deviations)`. The second term is
    present in EVERY layer. A layer whose heads all do nearly nothing therefore exhibits close to
    the item-sampling term alone, and since the first term can only ADD, **the quietest layer's
    spread is an upper bound on the item-noise floor.** No re-run, no GPU: R10 measured all 28
    layers exhaustively on one item set.

    THE SELECTION EFFECT IS REAL AND IS HANDLED, NOT IGNORED. Taking the minimum of 28 noisy sd
    estimates biases it downward, so the p10 layer is reported as the operative bound and the
    strict minimum beside it. Both are quoted; neither is chosen after the fact.

    ### RETRACTED 2026-07-28, ONE STEP AFTER IT WAS PUBLISHED. The confound written down before the
    run was the wrong one. It named the covariance between a head's true effect and its
    item-sampling deviation. The fatal assumption was cruder and unstated: **that item noise is
    roughly CONSTANT across layers.** It cannot be. A head's item-sampling deviation has variance
    `var_over_items(drop_h)/n`, and a head that contributes nothing has `drop == 0` on EVERY item,
    so its item-to-item variance is ~0 too.

    **A quiet layer has small item noise BECAUSE it is quiet.** Measured, and it is not marginal:
    Spearman between a layer's mean |drop| and its spread is **+0.962 over 28 layers**. The quiet
    layers are quiet in both terms, so their spread bounds the item noise only of heads that are
    equally quiet -- and the eight published effects, at 0.0154 to 0.4668, are not.

    So `bound_pct_of_floor_variance` is a measurement of the item-noise contribution IN A QUIET
    LAYER, extrapolated to the band, where the quantity is larger. That is an uncertainty compared
    against a differently-paired uncertainty: the first entry on this project's own overshoot list.

    WHAT SURVIVES AND WHAT DOES NOT:
      SURVIVES   the raw numbers -- quietest layer 0.00474, band floor 0.10879 -- and the
                 `distinctive` column, which compares each effect to the EXHAUSTIVE floor and needs
                 no item-noise argument at all. Still 0 of 8.
      UNVERIFIED the `measurable` column and `n_measurable`. Its threshold (2x the quiet-layer
                 bound) has no established relation to the item noise of a LIVE head. It is not
                 overturned -- the three may well be measurable -- the check was unfit.
      DEAD       "at most 0.66% of the floor's variance can be item sampling."

    THE DIRECT TEST IS NOW THE ONLY ROUTE, and it is cheap: re-run the same heads on a DISJOINT
    item set and store `sd_over_items/sqrt(n)` per head. The runner already computes the per-item
    drops and throws them away.

    WHAT FALLS OUT IS SHARPER THAN THE FLOOR ITSELF. Placing the eight published effects against
    the item-noise bound rather than against the floor separates two things the phrase "inside the
    noise floor" had been conflating: NOT MEASURABLE (below the instrument's precision) and NOT
    DISTINCTIVE (indistinguishable from a random head of the same size). The top three are many
    times the measurement bound and still inside the floor. **They are real measurements. They are
    simply not special.**
    """
    p = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    pe = r1_prior_effects()
    if not (p.exists() and pe):
        return None
    t = json.load(open(p))
    bm = abs(t['base_margin'])
    L = {int(k): v for k, v in t['layers'].items()}
    lo, hi = 14, 27

    def sd(xs):
        m = sum(xs) / len(xs)
        return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))

    band = [d for k in range(lo, hi + 1) for d in L[k]['per_head'].values()]
    band_floor = 2 * sd(band)
    per_layer = sorted((2 * v['sd'] / bm, k) for k, v in L.items())
    strict, p10 = per_layer[0], per_layer[int(0.10 * len(per_layer))]
    nb = band_floor / bm
    return {
        'model': t['model'], 'n_layers': len(L), 'n_items': t['n_items'],
        'base_margin': bm, 'band': [lo, hi],
        'band_floor_raw': band_floor, 'band_floor_normalised': nb,
        'quietest_layer': strict[1], 'quietest_bound': strict[0],
        'p10_layer': p10[1], 'p10_bound': p10[0],
        'bound_pct_of_floor_sd': 100 * p10[0] / nb,
        'bound_pct_of_floor_variance': 100 * (p10[0] / nb) ** 2,
        'strict_pct_of_floor_variance': 100 * (strict[0] / nb) ** 2,
        # THE EVIDENCE FOR THE RETRACTION, generated rather than asserted: if a layer's spread
        # tracks its effect scale, then a quiet layer is quiet in BOTH terms and cannot bound the
        # item noise of a live head.
        'spearman_scale_vs_spread': _spearman(
            [sum(abs(x) for x in L[k]['per_head'].values()) / len(L[k]['per_head'])
             for k in sorted(L)],
            [2 * L[k]['sd'] / bm for k in sorted(L)]),
        'effects': [{'head': h, 'drop': e['drop'],
                     'x_item_noise': e['abs'] / (p10[0] * bm),
                     'x_floor': e['abs'] / band_floor,
                     'measurable': e['abs'] / (p10[0] * bm) > 2.0,
                     'distinctive': e['abs'] > band_floor}
                    for h, e in sorted(pe['effects'].items(), key=lambda kv: -kv[1]['abs'])],
        # THE PRE-REGISTERED READING: >2x the bound = resolvable by this instrument; > the floor =
        # distinguishable from a random head. Two independent predicates, and the whole point is
        # that they DISAGREE on three of the eight.
        # UNVERIFIED, not a count. Kept so the retraction on the front page can be checked
        # against the number it retracts; renamed so no caller can read it as a finding.
        'n_measurable_UNVERIFIED': sum(e['abs'] / (p10[0] * bm) > 2.0
                                       for e in pe['effects'].values()),
        'n_distinctive': sum(e['abs'] > band_floor for e in pe['effects'].values()),
        'n_total': len(pe['effects']),
    }


def defect_ledger():
    """The defect table's own counts, GENERATED -- because every step adds a row and the prose drifts.

    The front page carried a cross-tabulation, an outside-reader fraction and a `n=NN` in four
    sentences, all maintained by hand. Every one of them was correct when written and wrong one
    commit later, which is the same failure the provenance stamp exists for, one level up. This
    reads `defects.json` and emits what the prose asserts.
    """
    p = HERE / 'defects.json'
    if not p.exists():
        return None
    d = json.load(open(p))['defects']
    bins, by = {}, {}
    for r in d:
        bins[r['bin']] = bins.get(r['bin'], 0) + 1
        by[r['found_by']] = by.get(r['found_by'], 0) + 1
    outside = sum(1 for r in d if r['found_by'] == 'outside_reader')
    inst = {}
    for r in d:
        # An "instrument" find is any found_by naming a detector or the gate, as opposed to the
        # author reading, or another mind. Grouped by prefix so a new detector does not need a
        # new branch here -- the failure mode this whole function exists to remove.
        # PREFIX, NOT SUBSTRING, AND THE SUBSTRING VERSION WAS CAUGHT BY THE ASSERTION IT BROKE.
        # `author_attacking_own_detector` contains the substring `detector`, so a defect the AUTHOR
        # found by attacking an instrument was credited to the instrument -- and the --check line
        # written specifically to fire if an instrument ever caught a SCOPE defect duly fired, for
        # the wrong reason. A finder is an instrument only if it IS one; anything beginning
        # `author_` is the author, whatever the author was pointing at.
        fb = r['found_by']
        who = ('outside' if fb == 'outside_reader'
               else 'author' if fb.startswith('author')
               else 'instrument' if fb.startswith(('instrument', 'detector', 'gate'))
               else 'author')
        inst.setdefault(r['bin'], {'author': 0, 'instrument': 0, 'outside': 0})[who] += 1
    largest = max(bins.values())
    return {'n': len(d), 'bins': dict(sorted(bins.items(), key=lambda kv: -kv[1])),
            'found_by': dict(sorted(by.items(), key=lambda kv: -kv[1])),
            'n_outside_reader': outside, 'outside_reader_pct': 100 * outside / len(d),
            'largest_bin': largest, 'largest_bin_pct': 100 * largest / len(d),
            'largest_bin_name': max(bins, key=bins.get),
            'n_unclassified': bins.get('UNCLASSIFIED', 0),
            'cross_tab': inst}


def variance_decomposition():
    """Across R1 and R2, does the FLOOR or the EFFECT carry more of the variation?

    `log(effect/floor)` splits into `log effect - log floor`, so the two variances say which term
    drives the ratio. On the six cross-round cells the floor carries most of it -- that is the
    front page's claim and it reproduces exactly.

    THE HELD-OUT HALF OF THAT CLAIM DID NOT. The page also reported that on R5's six margin cells
    the floor carries "52% -- a coin flip", with effects spanning 3.8x and floors 5.2x. No pairing
    of R5's checked-in fields reproduces any of those three numbers. Twenty-six admissible pairings
    -- {margin, kl} x {final, all, change, stacked} x {2sd_final, 2sd_all, w_final, w_all} -- span
    4.3% to 90.8%, and none lands near 52. The estimator was free, exactly as in R4, and the swept
    range is so wide that the CHOICE is the result. The sweep is emitted here so the retraction
    carries its own evidence rather than a promise.
    """
    import itertools
    cr = cross_round_scale()
    rows = [r for r in cr['r1'] + cr['r2'] if 'effect_pct' in r]
    le = [math.log(r['effect_pct']) for r in rows]
    lf = [math.log(r['noise_pct']) for r in rows]

    def var(xs):
        m = sum(xs) / len(xs)
        return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)

    ve, vf = var(le), var(lf)
    out = {'in_sample': {
        'n_cells': len(rows), 'var_log_effect': ve, 'var_log_floor': vf,
        'floor_share_pct': 100 * vf / (ve + vf),
        'n_distinct_floors': len({round(r['noise_pct'], 6) for r in rows})}}

    R5 = r5()
    sweep = []
    EFF = {'final': lambda r: abs(r['effect_final']), 'all': lambda r: abs(r['effect_all']),
           'change': lambda r: abs(r['effect_change'])}
    FL = ('read_2sd_final', 'read_2sd_all', 'read_w_final', 'read_w_all')
    if R5:
        for ro, (en, ef), fk in itertools.product(('margin', 'kl'), EFF.items(), FL):
            rs = [r for r in R5['rows'] if r['readout'] == ro]
            cells = [(ef(r), r[fk]) for r in rs]
            if len(cells) < 2 or any(e <= 0 or f <= 0 for e, f in cells):
                continue
            a, b = var([math.log(e) for e, _ in cells]), var([math.log(f) for _, f in cells])
            sweep.append({'readout': ro, 'effect': en, 'floor': fk,
                          'floor_share_pct': 100 * b / (a + b)})
        for ro, lbl in itertools.product(('margin', 'kl'), ('2sd', 'w')):
            rs = [r for r in R5['rows'] if r['readout'] == ro]
            cells = ([(abs(r['effect_final']), r[f'read_{lbl}_final']) for r in rs] +
                     [(abs(r['effect_all']), r[f'read_{lbl}_all']) for r in rs])
            if any(e <= 0 or f <= 0 for e, f in cells):
                continue
            a, b = var([math.log(e) for e, _ in cells]), var([math.log(f) for _, f in cells])
            sweep.append({'readout': ro, 'effect': 'stacked', 'floor': lbl,
                          'floor_share_pct': 100 * b / (a + b)})
    shares = [s['floor_share_pct'] for s in sweep]
    out['held_out_sweep'] = {
        'n_pairings': len(sweep), 'min_pct': min(shares) if shares else None,
        'max_pct': max(shares) if shares else None,
        'n_within_3pp_of_52': sum(abs(s - 52) < 3 for s in shares),
        'rows': sweep}
    return out


def r1_floor_audit():
    """THE FLOOR HAS ITS OWN NOISE FLOOR, and nobody measured it until the floor was audited.

    R1's pooled floor -- the reference class for this repository's headline -- is `2 x sd` of
    THIRTY RANDOM DRAWS from a band of 168 heads. R10 later measured ALL 168 exhaustively in the
    same vocabulary at the same baseline margin. Two facts follow, and neither was noticed:

    1. THE 30-DRAW FLOOR IS RECOMPUTABLE WITHOUT A GPU. The draw is `random.Random(draw_seed)`
       over an index list, so which heads were drawn depends on nothing but the seed. Replay the
       seed, look each head up in R10's exhaustive table, and the sd comes back BIT-IDENTICAL to
       the recorded one. Until this function existed, `0.4418` reached the front page as a stored
       constant that the gate could only echo -- it passed `prose_numbers` because it was WRITTEN
       DOWN, not because anything recomputed it.

    2. TWO OF THE EIGHT PUBLISHED EFFECTS ARE INSIDE THE NULL THAT JUDGES THEM. L16H3 -- the
       largest of the eight, and the only one that cleared -- is one of the thirty draws, and it
       is that sample's extreme value. That is textbook circularity. It is reported here WITH its
       leave-two-out control because the direction turns out to be CONSERVATIVE: removing them
       SHRINKS the null, so L16H3 clears by more, not less. A defect whose sign helps the
       conclusion is still a defect, and it is still the reader's to check.

    The consequential number is neither of those. It is that a 30-draw floor drawn from this
    population has a p05-p95 range of roughly 2.7x -- so `0.4418` and the exhaustive `0.4870` are
    the same measurement to within its own resolution, and the headline should never have rested
    on the sampled one when the exhaustive one was sitting in the next directory.
    """
    import random
    import re as _re
    import statistics as _st
    p = HERE / 'R1_noise_floor' / 'results' / 'original_vocabulary' / \
        'r1v1_atlas_qwen2.5-1.5b.json'
    q = HERE / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    pe = r1_prior_effects()
    if not (p.exists() and q.exists() and pe):
        return None
    v1, t = json.load(open(p)), json.load(open(q))
    NH, (lo, hi), (slo, shi) = v1['n_heads'], v1['band'], v1['sham_band']
    # int(L), NOT L. The JSON keys are strings, so `(L, int(h))` builds ('14', 0) and every
    # lookup misses. The guard below caught it by returning None instead of a plausible number --
    # which is the only reason this comment is a note rather than a retraction.
    per = {(int(L), int(h)): d
           for L, v in t['layers'].items() for h, d in v['per_head'].items()}
    if not all((L, h) in per for L in range(lo, hi + 1) for h in range(NH)):
        return None

    # Replay the runner's draw EXACTLY: same seed, same pools, same call order. The sham draws
    # are consumed too -- skipping them would leave the RNG in a different state and silently
    # produce a different, plausible-looking set of heads.
    rng = random.Random(v1['draw_seed'])
    bp = [(L, h) for L in range(lo, hi + 1) for h in range(NH)]
    sp = [(L, h) for L in range(slo, shi + 1) for h in range(NH)]
    drawn = []
    for k in (1, 2, 5, 10, 20):
        if k > len(bp):
            continue
        d = [rng.sample(bp, k) for _ in range(v1['n_draws'])]
        [rng.sample(sp, min(k, len(sp))) for _ in range(v1['n_draws'])]
        if k == 1:
            drawn = [x[0] for x in d]

    samp = 2 * _st.stdev([per[x] for x in drawn])
    pool = [per[(L, h)] for L in range(lo, hi + 1) for h in range(NH)]
    exh = 2 * _st.stdev(pool)

    eight = {h: e['drop'] for h, e in pe['effects'].items()}
    hd = {h: (int(m.group(1)), int(m.group(2)))
          for h in eight if (m := _re.match(r'L(\d+)H(\d+)', h))}
    contaminating = sorted(h for h, x in hd.items() if x in drawn)
    loo_pts = [per[x] for x in drawn if x not in {hd[h] for h in contaminating}]
    loo = 2 * _st.stdev(loo_pts)

    # The sampling distribution of the FLOOR ITSELF -- 30 independent single draws, repeats
    # allowed, exactly as the runner does it. Fixed seed so the interval is reproducible.
    rs = random.Random(11)
    boot = sorted(2 * _st.stdev([rs.choice(pool) for _ in range(len(drawn))])
                  for _ in range(4000))
    def pct(v):
        return 100.0 * sum(b < v for b in boot) / len(boot)

    ins = lambda f: sum(abs(d) < f for d in eight.values())  # noqa: E731
    return {
        'model': v1['model'], 'band': [lo, hi], 'n_band_heads': len(pool),
        'n_draws': len(drawn), 'draw_seed': v1['draw_seed'],
        'base_margin': abs(v1['base_margin']),
        'sampled_floor': samp, 'recorded_floor': 2 * v1['cells']['band_k1']['sd'],
        'reconstruction_error': abs(samp - 2 * v1['cells']['band_k1']['sd']),
        'exhaustive_floor': exh,
        'divergence_pct': 100 * abs(exh - samp) / samp,
        'boot_p05': boot[200], 'boot_median': boot[2000], 'boot_p95': boot[3800],
        'boot_spread_x': boot[3800] / boot[200],
        'sampled_floor_percentile': pct(samp),
        'contaminating_heads': contaminating,
        'leave_out_floor': loo,
        'n_inside_sampled': ins(samp), 'n_inside_leave_out': ins(loo),
        'n_inside_exhaustive': ins(exh), 'n_total': len(eight),
        'per_effect': [{'head': h, 'drop': d, 'x_sampled': abs(d) / samp,
                        'x_leave_out': abs(d) / loo, 'x_exhaustive': abs(d) / exh,
                        'in_the_null': h in contaminating}
                       for h, d in sorted(eight.items(), key=lambda kv: -abs(kv[1]))],
    }


def r9():
    """Is R1's headline a DEPTH artifact? The per-layer floor, and the estimator that failed twice.

    R1 compares a LATE band against an EARLY sham band and reports the ratio between their floors.
    If the floor simply grows with depth, that ratio is a fact about where the two pools sit in the
    stack, not about the heads inside them. R9 measures the floor at EVERY layer so the curve can
    be read directly instead of inferred.

    THE GATE IS REFUSED AND ITS NUMBERS ARE STILL EMITTED. The gate predicted the band's floor by
    extrapolating the sham half's trend to the band's depth. The band IS the upper half of the
    stack, so there is no data at the band's depth except the band -- every such prediction is
    extrapolation, and it shows: the linear form returns a NEGATIVE standard deviation on two of
    four models, and the log form returned 0.0016 and 16.18 for the same quantity. A refused
    verdict still has to carry its number or the refusal cannot be checked.
    """
    out = {}
    for name, d in load('R9_depth_profile/results/*.json').items():
        fl = {int(k): v['floor'] for k, v in d['layers'].items()}
        nz = {k: v for k, v in fl.items() if v > 0}
        if not nz:
            continue
        mn, mx = min(nz, key=nz.get), max(nz, key=nz.get)
        adj = [(max(nz[a], nz[a + 1]) / min(nz[a], nz[a + 1]), a)
               for a in sorted(nz) if a + 1 in nz]
        r_adj, l_adj = max(adj) if adj else (float('nan'), -1)
        lo, hi = d['band']
        slo, shi = d['sham_band']
        band = [fl[k] for k in range(lo, hi + 1) if k in fl]
        sham = [fl[k] for k in range(slo, shi + 1) if k in fl]
        bm, sm = sum(band) / len(band), sum(sham) / len(sham)
        pred = d['band_sd_predicted_from_sham_trend']
        out[name] = {
            'n_layers': d['n_layers'], 'n_heads': d['n_heads'], 'n_items': d['n_items'],
            'n_draws': d['n_draws'], 'band': d['band'], 'sham_band': d['sham_band'],
            'base_margin': abs(d['base_margin']),
            'quietest_layer': mn, 'quietest_floor': nz[mn],
            'noisiest_layer': mx, 'noisiest_floor': nz[mx],
            'stack_spread': nz[mx] / nz[mn],
            # THE SCOPE THAT WAS WRONG ON TWO PAGES. "neighbouring layers differ tenfold" is the
            # whole-stack number wearing the adjacent-layer label; the largest adjacent jump is
            # ~5x on three of four models. Emitted separately so the two can never merge again.
            'largest_adjacent_ratio': r_adj, 'largest_adjacent_at_layer': l_adj,
            'band_mean_floor': bm, 'sham_mean_floor': sm, 'band_over_sham': bm / sm,
            'spearman_rho_layer_sd': d['spearman_rho_layer_sd'],
            'refused_gate_predicted_sd': pred,
            'refused_gate_prediction_is_negative': pred < 0,
            'refused_gate_verdict': d['verdict'],
        }
    if not out:
        return None
    neg = sum(v['refused_gate_prediction_is_negative'] for v in out.values())
    return {'models': out, 'n_models': len(out), 'n_negative_predicted_sd': neg,
            'stack_spread_min': min(v['stack_spread'] for v in out.values()),
            'stack_spread_max': max(v['stack_spread'] for v in out.values()),
            'adjacent_ratio_min': min(v['largest_adjacent_ratio'] for v in out.values()),
            'adjacent_ratio_max': max(v['largest_adjacent_ratio'] for v in out.values()),
            'n_rho_positive': sum(v['spearman_rho_layer_sd'] > 0 for v in out.values())}


def r1_set_null_range():
    """The k=5 null's FULL RANGE, and the COPY set, as fractions of the flip distance.

    Hand-computed in a shell and quoted on the front page inside a fence, where the fence
    exemption hid them. Emitted so they are checked like everything else.
    """
    sn = r1_set_null()
    if not sn:
        return None
    n = sn['null']
    rng = n['max'] - n['min']
    return {'null_full_range': rng, 'base_margin': sn['base_margin'],
            'pct_of_flip_distance': 100 * rng / sn['base_margin'],
            'copy_pct_of_flip_distance':
                100 * abs(sn['sets']['COPY']['drop']) / sn['base_margin']}


def r1_behavioural_scale():
    """How far is any of this from the model actually answering differently?

    The readout is margin = correct-room logit minus the best wrong one, so the answer flips
    exactly when the margin reaches zero. The distance to a behavioural change is therefore the
    BASELINE MARGIN itself -- and nothing in this repository had ever expressed the floor, or the
    effects, against it. Four scopes are required of every claim here (population, instrument,
    baseline, REGIME) and the fourth was never answered for the headline.
    """
    rows = []
    for name, d in load('R1_noise_floor/results/*.json').items():
        bm = abs(d['base_margin']); c = d['cells']
        r = {'model': name, 'baseline_margin': bm}
        for k in (1, 5):
            cell = c.get(f'band_k{k}')
            r[f'floor2sd_k{k}'] = 2 * cell['sd'] if cell else None
            r[f'pct_to_flip_k{k}'] = 100 * 2 * cell['sd'] / bm if cell else None
        c5 = c.get('band_k5')
        r['p2p_k5_pct_to_flip'] = 100 * (c5['max'] - c5['min']) / bm if c5 else None
        rows.append(r)
    pe = r1_prior_effects()
    orig = None
    if pe:
        bm = pe['base_margin']
        orig = {'baseline_margin': bm,
                'floor_pct_to_flip': 100 * pe['floor_2sd_same_vocabulary'] / bm,
                'largest_effect_pct_to_flip': 100 * max(e['abs'] for e in pe['effects'].values()) / bm,
                'copy_head_pct_to_flip': 100 * pe['effects']['L22H7']['abs'] / bm}
    return {'rows': rows, 'original_vocabulary': orig,
            'max_pct_to_flip_k1': max(r['pct_to_flip_k1'] for r in rows)}


def r1_set_null():
    """The k=5 set-level null that splits "inside the floor" into its two causes.

    A single-head effect inside the k=1 floor is UNVERIFIED, not unreadable -- and the cheap way to
    tell which is to ablate the SET. E132d did exactly that with a 30-draw null and the answer is
    opposite for two head sets the repository's headline sentence used to cover together.
    """
    p = HERE / 'R1_noise_floor' / 'results' / 'prior_effects' / 'e132d_set_null.json'
    return json.load(open(p)) if p.exists() else None


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
    # NOT `*.json`. That glob's population was IMPLICIT: it matched whatever happened to be in
    # the directory, so adding wo_block_conditioning_*.json -- a file about a different
    # question entirely -- crashed this function on a missing 'arms' key. A loader whose
    # population is 'everything here' silently changes meaning every time a sibling is added.
    for name, d in load('R6_intervention/results/r6_intervention_*.json').items():
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
            r[f'pcsign_{arm}'] = 1 if a[arm]['positive_control'] >= 0 else -1
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
        # THE STOPPING RULE IS PART OF THE GATE, and this code did not implement it. R7's
        # pre-registration says: "If fewer than 3 models satisfy both inclusion criteria, R7
        # reports what it has and returns NOT MET." headline.py evaluated the bands anyway and
        # printed DIRECTION-MATTERS on 2 cells, while the shipped README said NOT MET -- the
        # machine and the page contradicting each other, in the repository whose entire subject
        # is numbers that drift from their source. Found by an adversarial reader, not by
        # `make verify`: --check asserts 11 hard-coded NUMBERS and prose_numbers.py checks
        # decimals, so neither can see a wrong VERDICT STRING. That blind spot is now closed by
        # asserting the verdict itself (see the claims list below).
        if len(inc) < 3:
            out['gate'] = 'NOT MET'
            out['gate_reason'] = (f"pre-registered stopping rule: {len(inc)} of "
                                  f"{len(rows)} cells included AND valid, needs 3")
        else:
            s_ok = (0.67 <= out['median_rr_shrink'] <= 1.5 and
                    0.67 <= out['median_rr_randdir'] <= 1.5)
            d_ok = (not (0.5 <= out['median_rr_shrink'] <= 2.0) or
                    not (0.5 <= out['median_rr_randdir'] <= 2.0))
            out['gate'] = ('SIZE-IS-ALL' if s_ok else
                           'DIRECTION-MATTERS' if d_ok else 'AMBIGUOUS')
            out['gate_reason'] = f"{len(inc)} included and valid cells"
        # FIX 4: THE SIGN OF EVERY POSITIVE CONTROL, compared to the zero arm's. The runners'
        # pc_clears_own_floor is |PC| > sd -- magnitude only -- so an INVERTED control passes it.
        # detectors/control_fitness.py exists precisely for this and was never called by anything;
        # meanwhile R8's randdir arm carries PC = -0.0096 against four positive arms and reports
        # clears=True. Surfaced here rather than left to a detector nobody invokes.
        out['sign_inverted_arms'] = [
            f"{r['model']}/{a}" for r in rows for a in ('mean', 'shrink', 'randdir')
            if r.get(f'pcsign_{a}') is not None and r.get('pcsign_zero') is not None
            and r[f'pcsign_{a}'] != r['pcsign_zero']]
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


def r8():
    """R8's admissible comparisons — arms whose positive control agrees in sign with `zero`."""
    rows = []
    for name, d in load('R8_component/results/r8_component_*.json').items():
        a = d['arms']
        z = 1 if a['zero']['positive_control'] >= 0 else -1
        r = {'model': name, 'order': d['order_low_to_high'],
             'order_eligible': d['order_eligible'], 'overshoot': d['overshoot_total'],
             'why_ineligible': d['order_ineligible_because']}
        for k in ('zero', 'mean', 'constant_only', 'shrink', 'randdir'):
            r[f'read_{k}'] = a[k]['readability']
            r[f'ok_{k}'] = bool((1 if a[k]['positive_control'] >= 0 else -1) == z)
            r[f'pc_{k}'] = a[k]['positive_control']
        rows.append(r)
    if not rows:
        return None
    cs = [r for r in rows if r['ok_constant_only'] and r['ok_shrink']]
    cm = [r for r in rows if r['ok_constant_only'] and r['ok_mean']]
    return {'rows': rows,
            # Emitted because the front page quotes them inside a code fence, where Detector 6's
            # fence exemption could not see them. That exemption is now gone; these are why.
            'const_over_shrink': [r['read_constant_only'] / r['read_shrink'] for r in rows],
            'n_order_eligible': sum(r['order_eligible'] for r in rows),
            'n_const_approx_shrink': sum(0.7 <= r['read_constant_only'] / r['read_shrink'] <= 1.43
                                         for r in cs), 'n_cs': len(cs),
            'n_mean_lowest': sum(r['read_mean'] < min(r['read_constant_only'], r['read_shrink'])
                                 for r in cm), 'n_cm': len(cm),
            'inverted': [f"{r['model']}/{k}" for r in rows
                         for k in ('mean', 'constant_only', 'shrink', 'randdir')
                         if not r[f'ok_{k}']]}


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
    D, V, S, G, R, E8 = r4(), r1_vocabulary(), r6(), r6_diag(), r7(), r8()
    PE, SN = r1_prior_effects(), r1_set_null()
    BS, CR = r1_behavioural_scale(), cross_round_scale()
    SR, TEN, NINE = r1_set_null_range(), r10(), r9()
    FA, VD, DL = r1_floor_audit(), variance_decomposition(), defect_ledger()
    IN = item_noise_bound()
    SL = set_level_scale()
    RV = rank_vs_role()
    IR = input_replication()
    TA = task_audit()
    FT = r14()
    TW = r12()
    FD = r15_design()
    TP = taxonomy_power()
    TC = r2_centred()
    TA2 = r2_task_audit()
    SV = selection_vs_effect()
    DS = depth_sensitivity()
    R15 = r15()
    R17 = r17()
    R18 = r18()
    SE = set_enrichment()
    SO = selection_overlap()
    # NOT `FT` -- that name is already bound to R14's result 120 lines below, and this
    # assignment shadowed it. It failed loudly only because the two dicts share no key;
    # had they shared one, the wrong number would have printed silently.
    TRI = instrument_triangle()
    OVC = ov_copying()
    RSL = resolution_limit()
    WOC = wo_conditioning()
    FTR = floor_transport()
    AS = adversary_scoring()
    EL = r11()
    PW = power()
    RC = reference_class()
    CN = centred_null()

    if args.json:
        print(json.dumps({'r1': A, 'r1_vocabulary': V, 'r2': B, 'r4': D, 'r5': E, 'r6': S, 'r6_diag': G, 'r7': R, 'r8': E8,
                          'r1_prior_effects': PE, 'r1_set_null': SN, 'r1_set_null_range': SR,
                          'r9': NINE, 'r10': TEN, 'r1_floor_audit': FA, 'variance_decomposition': VD, 'defect_ledger': DL, 'item_noise_bound': IN, 'set_level_scale': SL, 'rank_vs_role': RV, 'input_replication': IR, 'task_audit': TA, 'r14': FT, 'r12': TW, 'r15_design': FD, 'taxonomy_power': TP, 'r2_centred': TC, 'r2_task_audit': TA2, 'selection_vs_effect': SV, 'depth_sensitivity': DS, 'r15': R15, 'r17': R17, 'r18': R18, 'set_enrichment': SE, 'selection_overlap': SO, 'floor_transport': FTR, 'wo_conditioning': WOC, 'resolution_limit': RSL, 'ov_copying': OVC, 'instrument_triangle': TRI, 'adversary_scoring': AS, 'r11': EL, 'power': PW, 'reference_class': RC, 'centred_null': CN,
                          'r1_behavioural_scale': BS, 'cross_round_scale': CR},
                         indent=2, default=float))
        return 0

    if REFUSALS:
        print("REFUSED CELLS -- runs that produced an artifact but no measurement:")
        for pat, rs in sorted(REFUSALS.items()):
            for r in rs:
                print(f"      {r}")
        print("      a refusal is a fact about the model/task pairing, not a missing data point\n")

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
    if PE:
        print(f"R1' the eight prior single-head effects, against the floor of the SAME vocabulary")
        for h, e in sorted(PE['effects'].items(), key=lambda kv: -kv[1]['abs']):
            print(f"      {h:<8}{e['drop']:>+9.4f}   {e['frac_of_floor']:>6.3f} of the floor   "
                  f"{'CLEARS' if not e['inside_floor'] else ''}")
        print(f"      -> {PE['n_inside']} of {PE['n_total']} inside a floor of "
              f"{PE['floor_2sd_same_vocabulary']:.4f}; the largest clears by "
              f"{PE['largest']['clears_floor_by_pct']:.1f}%\n")

    if CR:
        print("R1+R2  on ONE scale, matched at k=5 -- why the two rounds disagreed")
        print(f"      {'round / model':<34}{'range':>9}{'effect%':>9}{'2sd%':>8}{'eff/noise':>11}")
        for tag, rows_ in (('R1', CR['r1']), ('R2', CR['r2'])):
            for r in rows_:
                e = f"{r['effect_pct']:>8.1f}%" if 'effect_pct' in r else f"{'-':>9}"
                q = f"{r['eff_over_noise']:>11.2f}" if 'eff_over_noise' in r else f"{'-':>11}"
                print(f"      {tag + ' ' + r['model']:<34}{r['range']:>9.3f}{e}"
                      f"{r['noise_pct']:>7.1f}%{q}")
        print(f"      effects span {CR['effect_pct_range'][0]:.1f}-{CR['effect_pct_range'][1]:.1f}% "
              f"of range; FLOORS span {CR['noise_pct_range'][0]:.1f}-"
              f"{CR['noise_pct_range'][1]:.1f}%, a {CR['noise_spread_x']:.0f}x spread")
        print(f"      -> the rounds differ in the FLOOR, not in the effect\n")

    if BS and BS['original_vocabulary']:
        o = BS['original_vocabulary']
        print(f"R1''' how far is ANY of this from the model answering differently?")
        print(f"      the answer flips when the margin reaches 0, so the distance IS the baseline")
        print(f"      baseline margin {o['baseline_margin']:.3f}  = the whole distance")
        print(f"        the floor (2 sd, k=1)  {o['floor_pct_to_flip']:>5.1f}% of it")
        print(f"        the largest of the 8   {o['largest_effect_pct_to_flip']:>5.1f}%")
        print(f"        the copy head L22H7    {o['copy_head_pct_to_flip']:>5.1f}%")
        print(f"      across models the k=1 floor is at most "
              f"{BS['max_pct_to_flip_k1']:.1f}% of the distance to a flip")
        print(f"      -> at k=1 the SIGNAL AND THE NOISE ARE BOTH SUB-BEHAVIOURAL\n")

    if DL:
        print(f"LDG the defect ledger, generated: n={DL['n']}  "
              f"largest bin {DL['largest_bin_name']} {DL['largest_bin']} "
              f"({DL['largest_bin_pct']:.1f}%)  unclassified {DL['n_unclassified']}")
        print(f"      found by an outside reader: {DL['n_outside_reader']} "
              f"({DL['outside_reader_pct']:.1f}%)")
        print(f"      {'joint':<15}{'author':>8}{'instrument':>12}{'outside':>9}")
        for b, c in sorted(DL['cross_tab'].items(), key=lambda kv: -sum(kv[1].values())):
            print(f"      {b:<15}{c['author']:>8}{c['instrument']:>12}{c['outside']:>9}")
        print()

    if VD:
        i, h = VD['in_sample'], VD['held_out_sweep']
        print("VAR does the FLOOR or the EFFECT carry the variation in log(effect/floor)?")
        print(f"      in-sample, {i['n_cells']} cross-round cells: var log effect "
              f"{i['var_log_effect']:.4f}  var log floor {i['var_log_floor']:.4f}"
              f"  -> floor carries {i['floor_share_pct']:.1f}%"
              f"   ({i['n_distinct_floors']} distinct floor values)")
        print(f"      held-out on R5: {h['n_pairings']} admissible pairings span "
              f"{h['min_pct']:.1f}%-{h['max_pct']:.1f}%, and "
              f"{h['n_within_3pp_of_52']} land within 3pp of the retracted 52%")
        print(f"      -> the ESTIMATOR was free, so the held-out claim is WITHDRAWN, not weakened\n")

    if CN:
        print("CTR the null is NOT centred at zero, and every verdict here assumed it was")
        print(f"      {'band':<16}{'n':>5}{'mean drop':>12}{'sd':>10}{'mean/sd':>9}{'pos/neg':>12}")
        for k, v in CN['bands'].items():
            print(f"      {k:<16}{v['n']:>5}{v['mean']:>+12.4f}{v['sd']:>10.4f}"
                  f"{v['mean_over_sd']:>9.2f}{f'{v["n_positive"]}/{v["n_negative"]}':>12}")
        print(f"      the SHAM band is centred (0.10 sd, near coin-flip signs); the studied band is "
              f"not -- so the offset is a fact about the LATE BAND, not about zero-ablation")
        print(f"      {'head':<9}{'drop':>10}{'|d|/2sd':>10}{'|d-mu|/2sd':>13}")
        for r in CN['effects']:
            print(f"      {r['head']:<9}{r['drop']:>+10.4f}{r['x_uncentred']:>10.2f}"
                  f"{r['x_centred']:>13.2f}"
                  f"{'   CLEARS once centred' if r['x_centred'] > 1 >= r['x_uncentred'] else ''}")
        print(f"      -> clears UNCENTRED {CN['n_clear_uncentred']} of 8   |   "
              f"CENTRED {CN['n_clear_centred']} of 8   (168 band heads: "
              f"{CN['band_heads_clear_uncentred']} -> {CN['band_heads_clear_centred']})\n")

    if RC:
        print("REF does the CHOICE of null decide the verdict? (pre-registered: >=4 of 8 would say yes)")
        print(f"      studied band L14-27  n={RC['n_band']}  floor {RC['band_floor']:.4f}")
        print(f"      SHAM band     L0-7   n={RC['n_sham']}   floor {RC['sham_floor']:.4f}"
              f"   = {RC['ratio']:.2f}x apart, from reference class alone")
        print(f"      {'head':<9}{'drop':>10}{'x band':>9}{'x sham':>9}")
        for r in RC['rows']:
            print(f"      {r['head']:<9}{r['drop']:>+10.4f}{r['x_band']:>9.2f}{r['x_sham']:>9.2f}"
                  f"{'   clears sham' if r['clears_sham'] else ''}")
        print(f"      clears band floor {RC['n_clear_band']} of 8   |   clears SHAM floor "
              f"{RC['n_clear_sham']} of 8   -> threshold "
              f"{'FIRED' if RC['fired'] else 'DID NOT FIRE'}")
        print(f"      but {RC['band_heads_clearing_sham']} of {RC['n_band']} band heads "
              f"({RC['pct_band_clearing_sham']:.0f}%) also clear the sham floor -- clearing it is "
              f"not distinction, it is being in the second half of the network")
        pk = ', '.join(f"L{x}" for x in RC['peak_layers'])
        print(f"      the clearing rate rises with depth -- Spearman "
              f"{RC['spearman_layer_vs_clearing_rate']:+.3f} over 28 layers -- but NOT monotonically:")
        print(f"        peak {pk} at "
              f"{100*max(RC['clearing_rate_by_layer'].values()):.0f}%, falling to "
              f"{100*RC['clearing_rate_by_layer'][25]:.0f}% by L25. A HUMP, not a half")
        print(f"        L22's own rate {100*RC['clearing_rate_by_layer'][22]:.0f}% -- at the band "
              f"average -- and within it the copy head is #"
              f"{RC['copy_head_rank_in_its_layer_clearing_set']} of "
              f"{len(RC['L22_clearing'])}, the SMALLEST that clears")
        print(f"        and {RC['n_published_in_peak_layers']} of the 8 published heads live in the "
              f"PEAK layers, where 83% of heads clear -- which is why they clear, and why it means "
              f"nothing")
        print(f"      -> the copy head's ablation number carries DEPTH information, not ROLE "
              f"information\n")

    if PW:
        print("PWR the POSITIVE CONTROL for the project's central null -- never previously stated")
        print(f"      floor {PW['floor']:.4f};  2*SEM over {PW['n_heads']} heads: "
              f"min {PW['two_sem_min']:.4f}  median {PW['two_sem_median']:.4f}  "
              f"max {PW['two_sem_max']:.4f}")
        print(f"      the floor exceeds a head's own measurement noise for "
              f"{PW['n_with_room']} of {PW['n_heads']} ({PW['pct_with_room']:.1f}%) -- the design "
              f"CAN produce 'measurable and distinguishable'")
        for u in PW['undecidable']:
            print(f"        except {u['head']}: 2*SEM {u['two_sem']:.4f} >= floor -- its own "
                  f"item variance exceeds the whole between-head spread, NO VERDICT POSSIBLE")
        print(f"      and {PW['n_positive_control']} heads ARE both, same run, same instrument:")
        for c in PW['positive_control'][:3]:
            print(f"        {c['head']:<8}{c['drop']:>+9.4f}  {c['x_floor']:.2f}x floor  "
                  f"{c['x_own_sem']:.1f}x its own 2*SEM")
        print(f"        ... {PW['n_positive_control']} in total -- SO THE MEASURED ZERO FOR THE "
              f"EIGHT IS ADMISSIBLE")
        print(f"      and it is not a landslide: the largest published effect reaches "
              f"{PW['largest_published_pct_of_threshold']:.0f}% of the threshold, the second "
              f"{PW['second_largest_x_floor']:.2f}x\n")

    if EL:
        print("R11 the instrument's own noise, MEASURED -- two exhaustive runs, disjoint item sets")
        print(f"      {'head':<9}{'drop':>9}{'2*SEM':>9}{'ratio':>8}{'rank A':>9}{'rank B':>8}{'move':>7}")
        for e in EL['effects']:
            print(f"      {e['head']:<9}{e['drop']:>+9.4f}{e['two_sem']:>9.4f}{e['ratio']:>8.2f}"
                  f"{e['rank_A']:>9}{e['rank_B']:>8}{e['rank_move']:>+7}")
        print(f"      1| RESOLVABLE at 2 sigma: {EL['n_resolvable']} of {EL['n_defined']} on the "
              f"PUBLISHED item set, {EL['n_resolvable_B']} of {EL['n_defined']} on the disjoint one "
              f"-- verdicts agree on {EL['resolvable_verdicts_agree']} of {EL['n_defined']}")
        print(f"         the one that flips is L22H7, 1.27 -> 0.57. Across all "
              f"{EL['n_band_heads']} band heads the runs agree on {EL['band_verdicts_agree']} "
              f"verdicts, Spearman {EL['band_ratio_spearman']:+.4f} -- the instrument replicates, "
              f"this HEAD does not")
        print(f"      2| run-to-run disagreement inside the SEM band: {EL['agree_within_sem']} of "
              f"{EL['n_band_pairs']} ({EL['agree_pct']:.1f}%), nominal "
              f"{EL['nominal_coverage_2sigma_pct']:.2f}% -- the SEM is the whole "
              f"story, so the denominator above is trustworthy")
        print(f"      3| KILL: exhaustive floor A {EL['floor_A']:.4f} vs B {EL['floor_B']:.4f} = "
              f"{EL['floor_divergence_pct']:.1f}% against a {EL['kill_threshold_pct']:.0f}% "
              f"threshold -> {EL['verdict']}")
        print(f"      rank stability across disjoint item sets: Spearman "
              f"{EL['rank_spearman_A_vs_B']:+.4f}, top-9 overlap "
              f"{EL['top9_overlap_across_item_sets']} of 9, published in B's top nine "
              f"{EL['published_in_B_top9']}")
        print(f"      the one exception is {EL['least_stable_published_head']}, moving "
              f"{abs(EL['least_stable_rank_move'])} places while every other published head moves "
              f"<=5 -- and it is the proven copy head")
        print("      ^ THAT LINE IS COMPUTED ON A RANKING THE FRONT PAGE DOES NOT USE -- it placed")
        print(f"        the null at zero; the published ranks are CENTRED on the band mean "
              f"({EL['centring_muA']:+.4f}). Recomputed:")
        print(f"          {'':<24}{'Spearman':>10}{'RMS disp':>10}{'largest mover':>20}")
        print(f"          {'uncentred (this round)':<24}{EL['rank_spearman_uncentred']:>+10.4f}"
              f"{EL['rms_disp_uncentred']:>10.2f}"
              f"{EL['worst_mover_uncentred']['head']:>14}{EL['worst_mover_uncentred']['move']:>6}")
        print(f"          {'CENTRED (front page)':<24}{EL['rank_spearman_A_vs_B']:>+10.4f}"
              f"{EL['rms_disp_centred']:>10.2f}"
              f"{EL['worst_mover_centred']['head']:>14}{EL['worst_mover_centred']['move']:>6}")
        print(f"        L22H7: uncentred {EL['L22H7_uncentred_A']} -> {EL['L22H7_uncentred_B']}, "
              f"CENTRED {EL['L22H7_centred_A']} -> {EL['L22H7_centred_B']} -- the LARGEST move of 168")
        print("        SO 'the copy head ranks 41 of 168' DOES NOT REPLICATE. On a disjoint item")
        print("        draw of the same task it is 160th. The direction STRENGTHENS the qualitative")
        print("        claim -- 160 is further inside the floor -- but 41 is not a property of the")
        print("        head, and the front page reported it as one\n")

    if AS:
        print("ADV  scoring the adversary-prediction file against what was found AFTER it")
        print(f"      written at {AS['baseline_rows']} ledger rows; the ledger is now "
              f"{AS['current_rows']}, so {AS['n_after']} of my own later findings can score it")
        print(f"      clean hit {AS['n_clean_hit']} (D79 <- A1) . class-level {AS['n_class']} "
              f"(D71 <- A7) . partial {AS['n_partial']} (D76 <- A2) . MISS {AS['n_miss']}")
        print(f"      {AS['pct_clean']:.1f}% clean, {AS['pct_generous']:.1f}% counting class-level "
              f"and partial -- BOTH emitted, because the generosity of matching is a CHOICE")
        print(f"      not on the page in any form: {' '.join(AS['miss_ids'])}")
        print(f"      WINDOW FROZEN at {AS['window'][0]}..{AS['window'][1]}: scoring 'every later "
              f"defect' makes the denominator grow forever, so the rate")
        print("      would decay without the file getting worse. Later rows face the file EXTENDED "
              "with A9-A13 -- a different object")
        print(f"      it covered {' '.join(AS['rounds_covered'])} and NOT "
              f"{' '.join(AS['rounds_uncovered_before_this_step'])} -- now extended, A9-A13")
        print("      and its A1 row carried the composition error R16 fixed 4 rounds ago as D80,")
        print("      which had landed on the prior-effects note ONLY\n")

        if R18.get('r12_rule'):
            q = R18['r12_rule']
            print(f"      THE 3b ARM LANDED, and R18's pre-registered rule for R12 says:")
            print(f"        qwen2.5-1.5b  {R18['centroid_final']:.3f} -> {R18['centroid_all']:.3f}"
                  f"   shift {q['shift_layers_1_5b']:+.3f} layers  ({q['shift_frac_1_5b']:+.4f} "
                  f"of depth)")
            print(f"        qwen2.5-3b    {q['centroid_final_3b']:.3f} -> "
                  f"{q['centroid_all_3b']:.3f}   shift {q['shift_layers_3b']:+.3f} layers  "
                  f"({q['shift_frac_3b']:+.4f} of depth)")
            print(f"        positive control 3b: last-layer max|eta| "
                  f"{q['pc_last_layer_max_eta_3b']:.6f}   saturation "
                  f"{100 * q['flip_rate_3b']:.2f}%")
            print(f"        A (fraction-shaped) {q['A_fraction_shaped']:.3f}   "
                  f"B (layer-shaped) {q['B_layer_shaped']:.3f}   "
                  f"B must be <= {q['B_threshold']:.3f}")
            print(f"        -> {q['verdict']}, missed by {q['miss_by']:.3f}. R12 stays UNVERIFIED.")
            print(f"        Chosen after the fact it would have been called layer-shaped; the rule")
            print(f"        is honoured at a 3% miss rather than renegotiated. Both centroids move")
            print(f"        EARLIER -- the direction replicates, the SHAPE does not resolve at n=2\n")

    if TRI:
        print("TRI  ALL THREE EDGES between the three instrument classes, with a LAYER control")
        print(f"     {'edge':<42}{'pooled':>10}{'within-layer':>14}")
        for k in sorted(TRI['edges']):
            v = TRI['edges'][k]
            po = v.get('pooled', v.get('pooled_abs'))
            wl = v.get('within_layer', v.get('within_layer_abs'))
            print(f"     {k:<42}{po:>+10.4f}{wl:>+14.4f}")
        print(f"     -> R16 IS NARROWED BY HALF: the ROOM-attention edge does not survive the layer")
        print(f"     control ({TRI['edges']['attention.room_att x ablation.I_final']['within_layer_abs']:+.4f}, "
              f"{TRI['edges']['attention.room_att x ablation.I_all']['within_layer_abs']:+.4f}); only the NAME edge holds")
        print(f"     -> attention to the room token ANTI-correlates with the OV circuit's ability to")
        print(f"     copy the room token, and that one DOES survive the layer control")
        print(f"     NOT 'all three are wrong': a head can attend to X, not copy X directly, and")
        print(f"     still matter through composition. Only 'none of them ALONE licenses the copy")
        print(f"     head' follows\n")

    if OVC:
        print("OV   A THIRD INSTRUMENT -- the weights. Independent of BOTH attention and ablation.")
        print(f"     M[t,s] = W_E[t] . W_O_h . W_V_kv . W_E[s] over the {len(OVC['rooms'])} room "
              f"tokens, {OVC['n_heads']} band heads, DIRECT PATH ONLY")
        print(f"     normalized diagonal dominance: min {OVC['dom_min']:+.3f}  median "
              f"{OVC['dom_median']:+.3f}  max {OVC['dom_max']:+.3f}")
        print(f"     diag_wins (of 4): {OVC['diag_wins_hist']}   -> POSITIVE CONTROL PASSES, "
              f"{OVC['n_perfect']} heads map all 4 rooms to themselves")
        k = OVC['L22H7']
        print(f"     L22H7 -- the named copy head -- diag_wins {k['diag_wins']}/4 (CHANCE), "
              f"dominance {k['dom_norm']:+.4f}, RANK {k['rank']} of {OVC['n_heads']}, "
              f"{k['percentile']:.1f}th percentile")
        print("     P6: a HIGH score is evidence of direct copying; a LOW score is NOT evidence of")
        print("     no copying, because a head can copy through composition. UNVERIFIED, not")
        print("     OVERTURNED -- but the label has never been supported by the weights.")
        print(f"     top-6: " + "  ".join(f"{r['head']} {r['dom_norm']:+.2f}" for r in OVC['top6']))
        h0 = OVC['L17H0']
        print(f"     THREE INSTRUMENTS CONVERGE ON A DIFFERENT HEAD: L17H0 is in the published eight")
        print(f"     (attention), 4th of 168 under I_all ablation (R18), and {h0['rank']}rd here "
              f"({h0['dom_norm']:+.4f}, {h0['diag_wins']}/4). POST HOC -- R19 registers it\n")

        if OVC.get('three_sets'):
            T = OVC['three_sets']
            print(f"     RUN ON THREE TOKEN SETS -- scores are NOT comparable across sets (different")
            print(f"     embedding norms), so every head is ranked WITHIN its own set:")
            print(f"       {'set':<9}{'n':>3}{'perfect-wins heads':>21}{'max dominance':>16}")
            for nm, n in T['sets'].items():
                print(f"       {nm:<9}{n:>3}{T['perfect'][nm]:>21}{T['max_dom'][nm]:>16.3f}")
            print(f"       -> positive control passes on ALL THREE; the instrument is blind on none")
            print(f"       {'head':<8}" + "".join(f"{nm+' dom':>13}{'rank':>6}" for nm in T['sets']))
            for k, v in T['heads'].items():
                print(f"       {k:<8}" + "".join(f"{v[nm]['dom']:>13.3f}{v[nm]['rank']:>6}"
                                                 for nm in T['sets']))
            print(f"       L22H7 is bottom-quartile on ALL THREE -- not a mislabelled copier, its")
            print(f"       direct OV path copies nothing in this task's vocabulary.")
            print(f"       L17H0 is high on ALL THREE -- a GENERIC direct copier, NOT room-specific,")
            print(f"       which withdraws the mechanistic reading its rank invited one step ago.")
            print(f"       L16H3, the LOUDEST head under ablation, is among the WORST copiers.")
            print(f"       THREE INSTRUMENTS, THREE DIFFERENT ANSWERS -- and still no arbiter\n")

    if RSL:
        print("RES  CAN THE MANDATED METHOD ANSWER THIS REPO'S OWN SURVIVING QUESTION? at this n, NO")
        print(f"       minimum attainable p, empirical null over {RSL['n']} values   "
              f"1/{RSL['n']+1} = {RSL['min_attainable_p']:.4f}")
        print(f"       Bonferroni at alpha 0.05 needs                     "
              f"{RSL['bonferroni_needs']:.5f}   "
              f"{'reachable' if RSL['bonferroni_reachable'] else 'UNREACHABLE by construction'}")
        print(f"       BH-FDR at alpha 0.05                               "
              f"{RSL['bh_discoveries']} discoveries   (first threshold "
              f"{RSL['bh_first_threshold']:.6f})")
        print(f"       uncorrected empirical p <= 0.05                    "
              f"{RSL['uncorrected_at_05']} of {RSL['n']}")
        print(f"       the published 2*sd count                           "
              f"{RSL['two_sd_count']} of {RSL['n']}   excess kurtosis "
              f"{RSL['excess_kurtosis']:.2f}")
        print(f"       smallest p: " + "  ".join(f"{r['head']} {r['p']:.4f}"
                                                 for r in RSL['smallest_ps'][:4]))
        print("     THE P-VALUES ARE 1/167, 2/167, 3/167 ... an empirical null built from the")
        print("     population being tested turns every p into a RANK OVER n. No resolution beyond")
        print("     ordering, so ZERO DISCOVERIES IS A RESOLUTION LIMIT, NOT AN ABSENCE.")
        print("     The SET-level test has resolution because its null is GENERATED by 50,000")
        print("     resamples rather than BEING the population -- and a count at a fixed threshold,")
        print("     which is what the transport result compares, is untouched by any of this\n")

    if WOC:
        print("W_O  an outside critique of R6, MEASURED from the weights rather than accepted")
        print(f"     r_out/r is bounded in [1/cond, cond] over the {WOC['n_heads']} band heads, each "
              f"block {WOC['block_shape'][0]}x{WOC['block_shape'][1]}")
        print(f"       condition number  min {WOC['cond_min']:.2f}  p25 {WOC['cond_p25']:.2f}  "
              f"MEDIAN {WOC['cond_median']:.2f}  p75 {WOC['cond_p75']:.2f}  max "
              f"{WOC['cond_max']:.2f} ({WOC['worst_head']})")
        print(f"       stable rank       MEDIAN {WOC['srank_median']:.1f} of "
              f"{WOC['srank_of_dims']} dimensions")
        print("     NULLSPACE HALF REFUTED -- at stable rank 117 of 128 there is essentially no")
        print("     nullspace to land in. HIGH-GAIN HALF BOUNDED at ~6x median, not unbounded.")
        print("     The bound is a WORST CASE over arbitrary directions and is therefore loose;")
        print("     tightening needs the activations, which were never stored\n")

    if FTR:
        print("FLR  DOES A SCALAR FLOOR TRANSPORT? -- the one result here that is about the METHOD")
        print(f"     transport A's WHOLE rule  |x - mu_A| > floor_A  (mu {FTR['reference_mu']:+.4f}, "
              f"floor {FTR['reference_floor']:.4f}) into three configurations")
        print(f"     each differing from A in EXACTLY ONE factor:")
        print(f"     {'configuration':<26}{'own floor':>10}{'own':>8}{'A-rule':>9}{'ratio':>7}"
              f"   differs by")
        for r in FTR['rows']:
            print(f"     {r['config']:<26}{r['own_floor']:>10.4f}"
                  f"{r['own_n']:>5}/{r['n']:<3}{r['transported_n']:>6}/{r['n']:<3}"
                  f"{r['ratio']:>7.2f}   {r['differs_by']}")
        print(f"     ROW D IS THE POSITIVE CONTROL AND THE DISCRIMINATOR: a completely fresh item")
        print(f"     draw transports at ratio 1.00, so a failure elsewhere is not sampling noise.")
        print(f"     THE TWO FAILURES POINT OPPOSITE WAYS -- intervention inflates the rate "
              f"{FTR['rows'][2]['ratio']:.2f}x,")
        print(f"     task deflates it to {FTR['rows'][3]['ratio']:.2f}x. A scalar floor is not merely "
              f"imprecise: its BIAS")
        print(f"     DEPENDS ON WHICH WAY THE CONFIGURATION MOVED, so no safety factor fixes it.")
        print(f"     WHICH KNOB FAILS -- the centre or the scale? Transporting both at once cannot")
        print(f"     say, and the remedies differ: a local re-centring is cheap, a local SCALE means")
        print(f"     the floor is not a number you can carry.")
        print(f"     {'configuration':<26}{'own':>6}{'both':>7}{'scale only':>12}{'centre only':>13}"
              f"{'mu x':>7}{'floor x':>9}")
        for r in FTR['rows']:
            print(f"     {r['config']:<26}{r['own_n']:>6}{r['transported_n']:>7}"
                  f"{r['scale_only_n']:>12}{r['centre_only_n']:>13}"
                  f"{r['mu_ratio']:>7.2f}{r['floor_ratio']:>9.2f}")
        LX = FTR['layer_axis']
        print(f"     FOURTH AXIS -- LAYER BAND, the largest variation here and it was not in the")
        print(f"     table. It is also the ONLY axis where the REVERSE direction is testable,")
        print(f"     because both regions come from the same result file:")
        print(f"       sham L0-7 judged by the BAND's rule : {LX['sham_by_band_rule']:>3} against "
              f"its own {LX['sham_own']:>3}   ratio {LX['ratio_down']:.2f}  -- you see NOTHING")
        print(f"       band L14-27 judged by the SHAM rule : {LX['band_by_sham_rule']:>3} against "
              f"its own {LX['band_own']:>3}   ratio {LX['ratio_up']:.2f}  -- 46% of the band")
        print(f"       floor ratio {LX['floor_ratio_band_over_sham']:.2f}x   "
              f"mu ratio {LX['mu_ratio']:.2f}x")
        print(f"     AND IT CORRECTS THE PREVIOUS STEP. `the centre is ~10% of the half-width so it")
        print(f"     does not matter` was measured ON THE BAND. Here centre-only gives "
              f"{LX['sham_centre_only']} against own {LX['sham_own']},")
        print(f"     because the centre SHIFT is {100 * LX['shift_over_sham_scale']:.0f}% of the "
              f"destination's scale rather than a few percent.")
        print(f"     THE UNIFYING QUANTITY IS |mu_dest - mu_src| / floor_dest:")
        for r in FTR['rows'][1:]:
            print(f"       {r['config']:<26}{100 * r['shift_over_dest_scale']:>6.1f}%   "
                  f"centre-only ratio {r['centre_only_ratio']:.2f}")
        print(f"       {'sham L0-7 (layer axis)':<26}"
              f"{100 * LX['shift_over_sham_scale']:>6.1f}%   centre-only ratio "
              f"{LX['sham_centre_only'] / max(LX['sham_own'], 1e-9):.2f}")
        print(f"     -> the CENTRE matters exactly when its SHIFT is large relative to the")
        print(f"     DESTINATION's scale. `the scale is the estimand` is itself SCOPED.")
        print(f"     -> RE-CENTRING FIXES NOTHING and the local SCALE fixes almost everything. The")
        print(f"     centre moves by about the SAME factor as the scale and it does not matter,")
        print(f"     because the centre is ~10% of the half-width: shifting it barely moves a")
        print(f"     threshold sitting at +-floor. THE SCALE IS THE ESTIMAND.")
        print(f"     NOT a calibration against a nominal alpha -- the `own` column is the same 2*sd")
        print(f"     rule on a heavy-tailed distribution, so this compares two APPLICATIONS of one")
        print(f"     rule. That is the transportability question, which is the one being asked\n")

    if SO:
        print("SEL  THE EIGHT WERE SELECTED, EVALUATED AND AUDITED ON THE SAME ITEMS -- from source")
        print(f"       e132_read_head.py:29         SEEDS = range(3000, 3300)   head SELECTION")
        print(f"       e132b_read_head_causal.py:27 SEEDS = range(3000, 3300)   causal EVALUATION")
        print(f"       R10_exhaustive/run.py:72     SEEDS = range(3000, 3400)   THIS AUDIT")
        print(f"       R11 set B                          range(3400, 3800)     the ONLY "
              f"independent items in the project")
        print(f"     Winner's curse is MAXIMAL, and nothing here had said so. It cuts both ways:")
        print(f"     the `not enriched` null is STRENGTHENED (they fail on their own home data), and")
        print(f"     every head number here except set B is computed on the data they were CHOSEN on")
        print(f"     shrinkage on the only independent items:")
        print(f"       {'aggregation':<18}{'the eight':>11}{'null median':>13}{'p':>10}")
        for nm, d_ in SO['aggregations'].items():
            print(f"       {nm:<18}{d_['observed']:>11.4f}{d_['null_median']:>13.4f}{d_['p']:>10.4f}")
        print(f"     TWO OF THREE FIRE, THE MEDIAN DOES NOT -- reported, not chosen. L16H3 and L22H7")
        print(f"     carry {100 * SO['top2_share_of_sum']:.0f}% of sum|c_A|, so the sum-ratio is a "
              f"two-head statistic. The set-level")
        print(f"     winner's curse IS NOT A SET PROPERTY. It is one head.")
        print(f"     L22H7 alone retains {SO['L22H7_retention']:.4f} -- the LOWEST of all 168 band "
              f"heads, {SO['L22H7_percentile']:.1f}th percentile,")
        print(f"     exact one-head p = {SO['L22H7_one_head_p']:.4f}; band median retention "
              f"{SO['band_median_retention']:.2f}; its own layer-mates {SO['L22_layermates']}")
        print(f"     THAT IS WHAT THE RANK MOVE 41 -> 160 WAS, and it now has a name.")
        print(f"     RTM control: the eight are BELOW the null median on set A, so regression to the")
        print(f"     mean predicts they shrink LESS than random -- the observed direction runs")
        print(f"     AGAINST that prediction rather than being explained by it\n")

    if SE:
        print("SET  ARE THE EIGHT ENRICHED AGAINST MATCHED-LAYER RANDOM SETS?  -- the test this")
        print("     project should have run first, instead of eight uncorrected comparisons")
        print("     against a scalar floor whose reference class does not hold LAYER fixed.")
        print(f"     {'arm':<10}{'T_pub':>9}{'null median':>13}{'p':>9}{'excess kurt':>13}")
        for tag in ('I_final', 'I_all'):
            a = SE['arms'][tag]
            print(f"     {tag:<10}{a['T_pub']:>9.4f}{a['null_median']:>13.4f}{a['p']:>9.4f}"
                  f"{a['excess_kurtosis']:>13.2f}")
        print(f"     {'arm':<10}{'SIGNED T_pub':>14}{'null med':>10}{'p HURT':>9}{'p HELP':>9}")
        for tag in ('I_final', 'I_all'):
            a = SE['arms'][tag]
            print(f"     {tag:<10}{a['T_pub_signed']:>+14.4f}{a['null_median_signed']:>+10.4f}"
                  f"{a['p_hurt']:>9.4f}{a['p_help']:>9.4f}")
        print(f"     SIGNED TOO, because |.| discards the sign and the eight carry a DIRECTIONAL")
        print(f"     claim -- read heads plus a copy head should HURT when ablated. Neither fires.")
        print(f"     signed positive control: top-8 by SIGNED drop is reached by "
              f"{SE['positive_control_signed_hits']} of {SE['n_replicates']} matched sets")
        print(f"     the nearest thing to a signal in the whole set is I_final HELP at "
              f"p = {SE['arms']['I_final']['p_help']:.4f} -- WRONG DIRECTION for the claimed role,")
        print(f"     and not significant. RAW vs CENTRED sign counts differ and the repo quotes the")
        print(f"     raw one: {SE['arms']['I_final']['n_raw_pos']} positive / "
              f"{SE['arms']['I_final']['n_raw_neg']} negative RAW, but "
              f"{SE['arms']['I_final']['n_above_mu']} above / "
              f"{SE['arms']['I_final']['n_below_mu']} below the mean "
              f"{SE['arms']['I_final']['mu']:+.4f}, which is the statistic every verdict uses")
        print(f"     the null draws WITH REPLACEMENT and the observed set cannot -- layer multiset "
              f"{SE['arms']['I_final']['layer_multiset']},")
        print(f"     so L17 can be drawn twice. That makes the null WIDER and the test CONSERVATIVE. "
              f"Distinct-per-layer:")
        print(f"       I_final p {SE['arms']['I_final']['p_distinct_per_layer']:.4f} "
              f"(against {SE['arms']['I_final']['p']:.4f})   "
              f"I_all p {SE['arms']['I_all']['p_distinct_per_layer']:.4f} "
              f"(against {SE['arms']['I_all']['p']:.4f}) -- both move AWAY from significance")
        print(f"     NOT ENRICHED under either -- and T_pub is BELOW the null median in both. The")
        print(f"     eight are on average LESS extreme than random heads from the SAME LAYERS.")
        print(f"     instrument checked before the null was believed: positive control (the actual")
        print(f"     top-8) -- only {SE['positive_control_hits']} of {SE['n_replicates']} matched "
              f"sets reached it; null calibration "
              f"{SE['null_calibration_rate']:.3f} of 200 random matched sets fall under 0.05")
        print(f"     AND THIS RETIRES THIS FILE'S OWN HEADLINE FROM ONE STEP EARLIER: L17H0 at rank")
        print(f"     4 of 168 under I_all has one-head p = {SE['L17H0_one_head_p']:.4f}, which is "
              f"{SE['L17H0_bonferroni_8']:.4f} after")
        print(f"     Bonferroni over the eight tested. A POST-SELECTION DESCRIPTIVE TAIL, not a "
              f"finding -- 168 heads were scanned to surface it\n")

    if R18:
        print("R18 is `final`-only a proxy for a head?  NO -- H-support fails 4 of 4")
        print(f"      CORRECTED positive control (the original was withdrawn as D88): at the LAST")
        print(f"      layer the two interventions differ only where nothing downstream reads, so")
        print(f"      eta must be ~0.  max|eta| at the last layer = "
              f"{R18['pc_last_layer_max_abs_eta']:.5f}  vs between-head sd "
              f"{R18['pc_between_head_sd']:.5f} -> {'PASS' if R18['pc_passes'] else 'FAIL'}")
        print(f"      saturation {100 * R18['flip_rate']:.2f}% sign flips (refusal was >50%)")
        print(f"      {'component':<34}{'observed':>10}{'required':>12}")
        print(f"      {'Spearman(tau_final, tau_all)':<34}{R18['spearman']:>+10.4f}{'>= 0.9':>12}")
        print(f"      {'published-head verdicts agree':<34}{R18['published_agree']:>8}/8{'8/8':>12}")
        print(f"      {'layer-centroid shift':<34}{R18['centroid_shift_norm']:>10.4f}{'<= 0.03':>12}")
        print(f"      {'top-10 overlap':<34}{R18['top10_overlap']:>8}/10{'>= 8/10':>12}")
        print(f"      -> {R18['h_support_components_failed']} of 4 FAIL. `final`-only is NOT a "
              f"proxy; every head number here is about I_final(L,h)")
        print(f"      R18's OWN looser rule (>=0.7 / <=0.3) puts {R18['spearman']:+.4f} IN BETWEEN "
              f"-> claim neither, kill does not fire. Both reported.")
        print(f"      {'head':<9}{'final |c|':>10}{'xfloor':>8}{'rank':>6}   {'ALL |c|':>9}"
              f"{'xfloor':>8}{'rank':>6}")
        for e in R18['eight']:
            print(f"      {e['head']:<9}{e['final']:>10.4f}{e['final_xfloor']:>8.2f}"
                  f"{e['final_rank']:>6}   {e['all']:>9.4f}{e['all_xfloor']:>8.2f}"
                  f"{e['all_rank']:>6}")
        print(f"      L17H0 is the result: 0.18x the floor at rank 77 under the intervention this")
        print(f"      repo has used throughout, and the 4TH LARGEST OF 168 under the total knockout")
        print(f"      floor {R18['floor_final']:.4f} -> {R18['floor_all']:.4f} "
              f"({R18['floor_ratio']:.2f}x), so `x floor` is NOT comparable across arms -- read ranks")
        print(f"      centroid {R18['centroid_final']:.3f} ({R18['depth_frac_final']:.4f} "
              f"of depth) -> {R18['centroid_all']:.3f} ({R18['depth_frac_all']:.4f}) "
              f"({R18['centroid_shift_layers']:+.3f} layers). NOT a verdict on R12: that needs the")
        print(f"      same shift on qwen2.5-3b to separate a fraction-shift from a layer-shift")
        print(f"      and the |eta| profile is NOT monotone in depth, which confirms D88's")
        print(f"      retraction empirically: "
              f"{' '.join(f'{R18['eta_by_layer'][x]:.3f}' for x in (0, 6, 18, 27))} at L0/L6/L18/L27\n")

    if R17:
        print("R17 is the headline an ARTIFACT of measuring where the FLOOR IS LARGEST?")
        print(f"      the eight were measured at margin 4.477, the highest configuration available,")
        print(f"      and the floor is the DENOMINATOR of `x floor`. Shuffled floor is "
              f"{R17['floor_ratio']:.3f}x of it.")
        print(f"      {'head':<9}{'UNSH |c|':>10}{'xfloor':>8}{'rank':>6}   {'SHUF |c|':>10}"
              f"{'xfloor':>8}{'rank':>6}{'num ratio':>11}")
        for r in R17['rows']:
            print(f"      {r['head']:<9}{r['cu']:>10.4f}{r['xf_u']:>8.2f}{r['ru']:>6}   "
                  f"{r['cs']:>10.4f}{r['xf_s']:>8.2f}{r['rs']:>6}{r['num_ratio']:>11.2f}")
        print(f"      CLEARING THE FLOOR: {R17['n_clear_unshuffled']} of 8 unshuffled -> "
              f"{R17['n_clear_shuffled']} OF 8 shuffled. The lower floor rescued NOTHING.")
        print("      -> WORLD 'artifact of the highest-floor configuration' is KILLED\n")
        print("      two narrative-friendly patterns in that table, both controlled in the same run:")
        print(f"      (1) seven of eight RISE in rank, mean {R17['mean_rank_unshuffled']:.1f} -> "
              f"{R17['mean_rank_shuffled']:.1f}. But ranks regress toward the middle "
              f"({R17['mid_rank']:.1f}) for EVERY")
        print(f"          head: global slope {R17['regression_slope']:.4f} predicts "
              f"{R17['predicted_mean_rank']:.1f}, residual {R17['residual']:+.2f}, null sd "
              f"{R17['null_sd']:.2f}")
        print(f"          over {R17['n_null']} random 8-head sets, one-sided p = "
              f"{R17['p_one_sided']:.4f} -> INSIDE THE NULL, no finding")
        print(f"      (2) L22H7's raw effect more than halves ({R17['L22H7_num_ratio']:.3f}x) and it")
        print(f"          is the only one of the eight to FALL in rank. But the median band head "
              f"fell to {R17['median_num_ratio']:.3f}x")
        print(f"          with IQR {R17['iqr_lo']:.3f}-{R17['iqr_hi']:.3f}, so "
              f"{R17['L22H7_num_ratio']:.3f} is the {R17['L22H7_percentile']:.1f}th percentile:")
        print("          inside the IQR, low-normal NOT anomalous -> no finding")
        print("      THE FIRST ROUND THAT ATTACKED A HEADLINE CLAIM AND DID NOT MOVE IT. No ledger")
        print("      row: nothing in the artifact was wrong, and a pattern caught before it was")
        print("      written down is not a defect in the artifact\n")

    if R15:
        print("R15 the SHUFFLED exhaustive scan -- the pre-registered kill on head-ranking transfer")
        v = 'TRANSFERS' if R15['spearman_abs'] >= .7 else (
            'DOES NOT TRANSFER' if R15['spearman_abs'] <= .3 else 'IN BETWEEN -- claim neither')
        print("      Spearman over 168 band heads, shuffled vs unshuffled:")
        print(f"        on |centred drop|  {R15['spearman_abs']:+.4f}   <- the statistic this repo "
              f"RANKS BY   -> {v}")
        print(f"        on signed drop     {R15['spearman_signed']:+.4f}")
        print(f"      thresholds committed BEFORE the run: >={R15['threshold_transfers']} transfers,"
              f" <={R15['threshold_does_not']} does not. Two statistics straddle it and picking the")
        print("      one that clears is a narrative, so both are reported and NEITHER is claimed.")
        print(f"      population confound CHECKED: same draw_seed {R15['same_draw_seed']}, same n "
              f"{R15['same_n_items']}; R14's A_orig=1.000 makes the dropped filter a measured no-op")
        print(f"      floor {R15['floor_shuffled']:.4f} shuffled vs {R15['floor_unshuffled']:.4f} "
              f"unshuffled = {R15['floor_ratio']:.3f}x, while base margin fell "
              f"{R15['margin_unshuffled']:.3f} -> {R15['margin_shuffled']:.3f} "
              f"({R15['margin_ratio']:.2f}x)")
        print(f"      clearing the floor: {R15['n_clear_shuffled']} shuffled, "
              f"{R15['n_clear_unshuffled']} unshuffled")
        print("      THE FINDING IS THE THIRD READING -- the floor is POSITION-DEPENDENT:")
        print(f"      {'line':>5}{'n':>5}{'margin':>9}{'acc':>7}{'floor':>9}{'floor/margin':>14}")
        for r in R15['per_line']:
            print(f"      {r['line']:>5}{r['n']:>5}{r['margin']:>9.3f}{r['acc']:>7.3f}"
                  f"{r['floor']:>9.4f}{r['floor_over_margin']:>14.3f}")
        print(f"      floor spans {R15['line_floor_spread']:.2f}x while margin spans "
              f"{R15['line_margin_spread']:.2f}x; Spearman(margin, floor) = "
              f"{R15['spearman_margin_vs_floor']:+.4f}")
        print(f"      so the ABSOLUTE floor is robust, but floor/margin spreads "
              f"{R15['ratio_spread']:.2f}x -- `x floor`, the unit this repo ranks published heads")
        print("      in, IS NOT PORTABLE ACROSS TASK CONFIGURATIONS\n")

    if DS:
        print("R12C the instrument's sensitivity is MONOTONE IN DEPTH, and R12's verdict is a depth")
        print("      claim. Ablation zeroes the final position only, so a head's writes at earlier")
        print("      positions survive; the layers that can READ them number (NL-1-L) -- NL-1 at")
        print("      layer 0, ZERO at the last layer, where the measurement is COMPLETE.")
        print("      (NL-1-L)/NL is a FRACTION OF DEPTH, which is the exact shape of R12's winner:")
        print("      the confound MANUFACTURES `RELATIVE` OUT OF `ABSOLUTE`.")
        print(f"      magnitude trend, qwen2.5-1.5b:  all 28 layers "
              f"{DS['spearman_layer_vs_magnitude_all']:+.4f}   band 14-27 "
              f"{DS['spearman_layer_vs_magnitude_band']:+.4f}")
        print(f"        mean |centred| L0-6 {DS['early_L0_6']:.4f}  L21-27 "
              f"{DS['late_L21_27']:.4f}   ratio {DS['late_over_early']:.2f}x")
        print("      POSITIVE CONTROL -- a bias-only profile MUST peak at the LAST layer:")
        print(f"      {'model':<14}{'NL':>4}{'centroid':>10}{'peak L':>8}{'rate':>7}"
              f"{'LAST L rate':>13}{'layers above it':>17}")
        for m in ('qwen2.5-1.5b', 'qwen2.5-3b'):
            d = DS[m]
            print(f"      {m:<14}{d['NL']:>4}{d['centroid']:>10.3f}{d['peak_layer']:>8}"
                  f"{d['peak_rate']:>7.3f}{d['last_layer_rate']:>13.3f}"
                  f"{d['n_layers_above_last']:>17}")
        print("      BOTH near MINIMAL at the last layer -- the bias does not run the SHAPE. It")
        print("      still moves the CENTROID, which is a first moment. R12: UNVERIFIED, which is")
        print("      NOT an acquittal\n")

    if SV:
        print("R16 the audited heads were SELECTED by attention and MEASURED by ablation -- agree?")
        print(f"      over {SV['n_band']} band heads, same model, same items, same vocabulary:")
        print(f"        Spearman(|centred ablation|, room attention) = {SV['spearman_room']:+.4f}")
        print(f"        Spearman(|centred ablation|, name attention) = {SV['spearman_name']:+.4f}")
        print(f"      BOTH NEGATIVE -- the instruments mildly ANTI-correlate")
        print(f"      SIGNED, so the negative number is not misread: room "
              f"{SV['spearman_room_signed']:+.4f}  name {SV['spearman_name_signed']:+.4f} -- about "
              f"THREE TIMES weaker, so this is a MAGNITUDE effect, not a direction one.")
        print(f"        attention picks heads that do LESS, not heads that help. But the top "
              f"name-attention quartile does skew to hurting:")
        for q in SV['name_quartiles']:
            print(f"          name-att Q{q['q']}  n={q['n']:>3}  mean signed "
                  f"{q['mean_signed']:+.4f}   pos/neg {q['n_pos']}/{q['n_neg']}")
        print(f"      {'head':<9}{'ablation':>10}{'room rank':>11}{'name rank':>11}")
        for r in SV['top_ablation']:
            print(f"      {r['head']:<9}{r['abl']:>10.4f}{r['room_rank']:>11}{r['name_rank']:>11}")
        print(f"      reverse: top-5 by room-att -> ablation ranks "
              f"{SV['top5_room_ablation_ranks']}")
        print(f"               top-5 by name-att -> ablation ranks "
              f"{SV['top5_name_ablation_ranks']}")
        print(f"      NOT A DISCOVERY: attention as an unreliable proxy for causal importance is "
              f"established background (arXiv 2504.13752 states it in its abstract). What is new "
              f"here is that THIS audit's eight heads were picked by exactly that proxy\n")

    if TA2:
        print("R2T what does R2's task require? -- R13's audit, transferred at last")
        print(f"      sequences are `core + core` with len(core) = T = {TA2['T']}, CONSTANT on all "
              f"{TA2['n_seq']} sequences; ids uniform in [{TA2['vocab_lo']}, {TA2['vocab_hi']})")
        print(f"      at position T+i the answer sits at i+1, so it is ALWAYS EXACTLY "
              f"{TA2['offset_to_answer']} POSITIONS BACK")
        print(f"      -> a head attending at a CONSTANT DISTANCE solves it with no content matching,"
              f" and the task cannot tell that from prefix-matching")
        print(f"      and the SELECTION criterion is the same quantity: attention from i to i-T+1, "
              f"a fixed offset ({TA2['selection_uses_fixed_offset']}), whose own docstring calls it "
              f"a 'prefix-matching score' ({TA2['selection_called_prefix_matching']})")
        print(f"      the NAME asserts content matching; the COMPUTATION measures distance\n")

    if TC:
        print("R2* the centring correction applied to R2, which had never been audited like R1")
        print(f"      {'model':<16}{'d_top':>10}{'null mean':>11}{'mu/sd':>8}{'x uncent':>10}{'x centred':>11}")
        for r in TC['rows']:
            print(f"      {r['model']:<16}{r['d_top']:>+10.4f}{r['null_mean']:>+11.4f}"
                  f"{r['mean_over_sd']:>8.2f}{r['x_uncentred']:>10.2f}{r['x_centred']:>11.2f}")
        print(f"      every null is NEGATIVE ({TC['mean_over_sd_max']:.2f} to "
              f"{TC['mean_over_sd_min']:.2f} sd) -- ablating random heads HURTS induction, the "
              f"opposite of the room task where it HELPED")
        print(f"      d_top is negative too, so centring makes clearing HARDER -- and the count "
              f"survives anyway: {TC['n_clear_uncentred']} -> {TC['n_clear_centred']} of {TC['n']}")
        print(f"      WHY R1 AND R2 DISAGREED, stated on one scale at last:")
        print(f"        R1's eight  " + " ".join(f"{v:.2f}" for v in TC['r1_x_centred']))
        print(f"        R2's valid  " + " ".join(f"{r['x_centred']:.2f}" for r in TC['rows']
                                                 if r['x_centred'] > 1))
        print(f"        R1 max {TC['r1_max']:.2f}   R2 min {TC['r2_min_clearing']:.2f} -- the two "
              f"distributions barely touch. Not a methods disagreement, an EFFECT SIZE one\n")

    if TP:
        print("TAX does the pre-registered taxonomy VERDICT carry information, or only the count?")
        print(f"      observed {TP['verdict']} at n={TP['n']}; expected {TP['expected_per_bin']:.1f} "
              f"per bin over {TP['n_bins']} bins")
        print(f"      PERMUTATION, labels assigned uniformly at random, {TP['n_draws']} draws:")
        print(f"        it fires {TP['verdict_fires_under_random_labels_pct']:.2f}% of the time")
        print("        by n: " + "  ".join(f"n={k} {v:.1f}%" for k, v in TP['fires_by_n'].items()))
        print(f"      -> THE VERDICT IS DEAD AS EVIDENCE. It was informative at n=22 and stopped "
              f"discriminating around n=45")
        print(f"      what replaces it: chi-square {TP['chi_square']:.2f}, permutation p "
              f"{TP['chi_square_p']:.5f} -- the DISTRIBUTION is uneven, and the two SMALL bins "
              f"carry it")
        print("        " + ", ".join(f"{k} {v}" for k, v in TP['smallest_bins']) +
              f" against an expected {TP['expected_per_bin']:.1f}")
        print(f"      the right question was never 'does a bin dominate' but 'is the partition "
              f"uneven', and the answer sits at the opposite end from the threshold")
        print(f"      AND THE VERDICT SPACE HAS COLLAPSED. It discriminated five ways in the first "
              f"26 rows and has been frozen since:")
        print("        " + "  ".join(f"n={h['n']}:{h['verdict'].split('-')[0]}"
                                     for h in TP['verdict_history']))
        print(f"        UNCLASSIFIED never decreases and is {TP['unclassified_now']}; "
              f"TAXONOMY-EXISTS needs <=2, so it is PERMANENTLY UNREACHABLE from "
              f"n={TP['taxonomy_exists_unreachable_from_n']}")
        print(f"        reachable verdicts now: {TP['reachable_verdicts']} -- a test with one "
              f"reachable outcome is not a test\n")

    if FD:
        print("R15 a design defect in a run that has NOT happened, from an earlier run's records")
        print(f"      the exhaustive runner keeps only items answered CORRECTLY. Under shuffling "
              f"that is {FD['n_kept']} of {FD['n_offered']}, and WHICH ones is position-dependent:")
        print(f"      ends L0,1,6,7  offered {FD['ends_offered_pct']:.1f}%  ->  kept "
              f"{FD['ends_kept_pct']:.1f}%   ({FD['skew_points']:+.1f} points toward the easy half)")
        print(f"      the floor it produced would be the EASY HALF's floor, with nothing in the "
              f"output saying so")
        print(f"      FIX, free: drop the filter. A drop is a change in MARGIN, defined whether or "
              f"not the argmax is correct -- and on the original task accuracy is "
              f"{FD['accuracy_original']:.3f}, so the filter has never rejected a single item there")
        print(f"      first time in this project a design was attacked BEFORE the compute\n")

    if TW:
        print("R12 is the hump at a fixed LAYER or a fixed DEPTH FRACTION? -- pre-registered")
        print(f"      {TW['model']}, {TW['n_layers']} layers vs 28: at 28 the two coincide, at "
              f"{TW['n_layers']} they are five layers apart")
        print(f"      centroid {TW['centroid']:.3f}   bootstrap 95% CI "
              f"[{TW['centroid_ci95_lo']:.2f}, {TW['centroid_ci95_hi']:.2f}]")
        print(f"        CI half-width {TW['centroid_ci95_halfwidth']:.4f} layers -- R18's 1.0-layer"
              f" deadband is justified against THIS, not against the rounded endpoints")
        print(f"        ABSOLUTE predicted {TW['absolute_prediction']:.2f}  -> "
              f"{'INSIDE' if TW['absolute_inside_ci'] else 'OUTSIDE'} the interval")
        print(f"        RELATIVE predicted {TW['relative_prediction']:.2f}  -> "
              f"{'INSIDE' if TW['relative_inside_ci'] else 'OUTSIDE'} the interval")
        print(f"      -> {TW['verdict']}   depth fraction {TW['depth_fraction']:.4f} "
              f"(qwen2.5-1.5b: 0.6383)")
        print(f"      KILL (no interior peak): peak L{TW['peak_layers'][0]} of {TW['n_layers']}, "
              f"max/min-nonzero {TW['max_over_min_nonzero']:.2f} -> "
              f"{'FIRED' if TW['kill_fired'] else 'did not fire'}")
        print(f"      BUT THE SHAPE DOES NOT TRANSFER. {TW['n_heads_per_layer']} heads per layer "
              f"=> a rate carries about +-{100*1.96*TW['rate_se_at_half']:.0f} points:")
        print("        " + "   ".join(f"L{r['layer']} {100*r['rate']:.0f}%+-{100*r['ci95']:.0f}"
                                      for r in TW['top4']))
        print(f"        the four highest layers are statistically indistinguishable -- the PEAK "
              f"LOCATION is not resolved, and the verdict rests on the CENTROID\n")

    if FT:
        print("R14 does the model BIND the name, or COPY line 0? -- pre-registered before the probe")
        print(f"      accuracy ORIGINAL (answer always at line 0): {FT['accuracy_original']:.3f}")
        print(f"      accuracy SHUFFLED (answer at a random line): {FT['accuracy_shuffled']:.3f}"
              f"   chance {FT['chance']:.2f}")
        print(f"      -> {FT['verdict']}   (BINDING needed >= "
              f"{FT['binding_ratio_threshold'] * FT['accuracy_original']:.3f}, POSITION needed <= "
              f"{FT['position_ceiling']:.3f})")
        print("      accuracy by the answer's line -- the control returned a THIRD shape:")
        print("        line  " + "  ".join(f"{k:>4}" for k in FT['by_line']))
        print("              " + "  ".join(f"{v:>4.2f}" for v in FT['by_line'].values()))
        print(f"        ends L0,1,6,7 {FT['ends']['acc']:.3f} +-{FT['ends']['ci95']:.3f}   "
              f"middle L2-5 {FT['middle']['acc']:.3f} +-{FT['middle']['ci95']:.3f}   "
              f"diff {FT['ends_minus_middle']:+.3f}  z {FT['ends_minus_middle_z']:+.2f}")
        print(f"        a U, not a step and not a decay: primacy AND recency")
        print(f"      every line above chance ({FT['all_lines_above_chance']}); worst is line "
              f"{FT['worst_line']} at {FT['worst_acc']:.2f} = {FT['worst_over_chance']:.1f}x chance")
        print(f"      -> THE MODEL IS NOT COPYING POSITION 0. R13's finding about the TASK stands; "
              f"the insinuation about the MODEL was mine and is refuted\n")

    if TA:
        print("TSK what does the TASK require? -- twelve rounds audited the measurement, not this")
        print(f"      the query is the first single-token person, and all {TA['n_persons']} are "
              f"single-token, so it is always '{TA['query_person']}'")
        print(f"      fact lines follow PERSONS order, so the answer's fact is always LINE "
              f"{TA['query_line_index']}")
        print(f"      -> THE CORRECT ANSWER IS ALWAYS THE ROOM IN THE FIRST SENTENCE")
        print(f"      the ANSWER varies -- over 400 seeds the four rooms take "
              f"{TA['answer_min_share_pct']:.1f}%-{TA['answer_max_share_pct']:.1f}% -- "
              f"but the POSITION does not")
        print(f"      'copy the room from line 0' scores "
              f"{TA['trivial_strategy_accuracy_pct']:.0f}% without matching a single name")
        print(f"      a FIXED-POSITION RETRIEVAL task, and it cannot distinguish position-copying "
              f"from name-binding: they agree on every item it contains")
        cm = TA.get('cross_model')
        if cm:
            print(f"      UNIFORM ACROSS MODELS? probed with the runners' own convention over "
                  f"{cm['n_cells']} model x vocabulary cells:")
            print(f"        single-token persons vary -- " +
                  '  '.join(f"{k} {v}/8" for k, v in cm['n_single_by_model'].items()))
            print(f"        distinct query LINE indices: {cm['distinct_query_lines']} -- "
                  f"{'UNIFORM' if cm['uniform_across_models'] else 'NOT UNIFORM'}, so the "
                  f"cross-model comparisons stay commensurable")
        print()

    if IR:
        print("REP do the eight numbers this project is ABOUT reproduce under a different runner?")
        print(f"      margins: E132b {IR['margin_e132b']:.10f}  R10 {IR['margin_r10']:.10f}  "
              f"diff {IR['margin_abs_diff']:.2e}")
        print(f"      max |E132b drop - R10 drop| over the {IR['n']}: "
              f"{IR['max_abs_diff']:.2e}  -- float32 nondeterminism")
        print(f"      -> two separately written runners agree; the compared quantities are "
              f"commensurable. Closure, never previously done, and it could have failed")
        print(f"      AND THE METHOD POINT: E132b asked about {IR['n_heads_hypothesis_driven']} "
              f"heads, R10 about {IR['n_heads_exhaustive']} -- same code path, same items, "
              f"{IR['exhaustive_over_hypothesis']:.0f}x the questions")
        print(f"      asking about all of them is what produced every finding of the last four "
              f"steps, for one 16-minute job on a consumer GPU\n")

    if RV:
        print("RNK of ALL 168 band heads, which clear -- and where do the published ones rank?")
        print(f"      exhaustive floor {RV['floor_2sd']:.4f};  {RV['n_clear']} of "
              f"{RV['n_band_heads']} heads clear it ({RV['pct_clear']:.1f}%)")
        for c in RV['clearing_heads']:
            print(f"        {c['head']:<8}{c['drop']:>+9.4f}{c['x_floor']:>7.2f}x   {c['direction']}")
        print(f"      {RV['n_clear_positive']} of {RV['n_clear']} clear in the HELPING direction -- "
              f"clearing the floor is not evidence of a role")
        print(f"      AND THE COUNT ITSELF IS NOT INFORMATIVE: a normal would give "
              f"{RV['expected_beyond_2sd_normal']:.1f} beyond 2sd, a Laplace "
              f"{RV['expected_beyond_2sd_laplace']:.1f}; observed {RV['n_clear']}. Excess kurtosis "
              f"{RV['excess_kurtosis']:+.2f} -- 2*sd is a normal-theory cut on a heavy tail")
        print(f"      leave-one-out (each head judged by a null excluding it): "
              f"{RV['n_clear_leave_one_out']} -- the circularity check ran and came back clean")
        print(f"      WHAT SURVIVES IS THE RANKING, which needs no threshold:")
        print(f"      published heads among the clearing set: "
              f"{RV['n_published_among_clearing']} of {RV['n_clear']}")
        for r in RV['published_ranks']:
            print(f"        rank {r['rank']:>3}/{RV['n_band_heads']}   {r['head']:<8}"
                  f"{r['drop']:>+9.4f}{'   <- the proven copy head' if r['head']=='L22H7' else ''}")
        print(f"      DEPTH CONTROL -- the floor grows with depth, so raw |drop| favours deep heads")
        print(f"        mean layer: published {RV['mean_layer_published']:.1f}  "
              f"top-9 raw {RV['mean_layer_top9_raw']:.1f}  "
              f"top-9 normalised by layer sd {RV['mean_layer_top9_norm']:.1f}")
        print(f"        published among the normalised top nine: "
              f"{RV['published_in_top9_by_layer_sd']}")
        print(f"        the two top-nines share {RV['top9_overlap_between_normalisations']} of 9 "
              f"members -- WHICH heads are top is normalisation-dependent;")
        print(f"        that the published ones are in NEITHER is not. The invariance is the result.")
        for r in RV['ranks_by_layer_sd']:
            print(f"        rank {r['rank']:>3}/{RV['n_band_heads']} by layer-sd   {r['head']:<8}"
                  f"{r['layer_sd_units']:>6.2f} layer-sd")
        print()

    if SL:
        print("SET the circuit result on the SAME statistic as the head result")
        print(f"      k=5 null over {SL['n_draws']} draws: mean {SL['null_mean']:+.4f}  "
              f"sd {SL['null_sd']:.4f}  min {SL['null_min']:+.4f}  max {SL['null_max']:+.4f}")
        print(f"      a percentile from {SL['n_draws']} draws resolves to "
              f"{SL['percentile_resolution_pct']:.1f}% -- '0.0th' means 'below all of them', no finer")
        print(f"      {'set':<28}{'drop':>9}{'x floor':>9}{'z vs null mean':>16}{'sd past min':>13}")
        for k, v in sorted(SL['sets'].items(), key=lambda kv: kv[1]['drop']):
            print(f"      {k:<28}{v['drop']:>+9.4f}{v['x_floor_2sd']:>9.2f}"
                  f"{v['z_from_null_mean']:>+16.2f}{v['sd_beyond_null_min']:>13.2f}"
                  f"   (uncentred {v['x_floor_2sd_UNCENTRED']:.2f})")
        print(f"      k=5 null sd is {SL['k5_over_k1_sd']:.2f}x the k=1 exhaustive sd -- five heads "
              f"roughly DOUBLES the floor, and the circuit clears the larger one anyway\n")

    if IN:
        print("ITM is the floor HEAD CHOICE, or the finite item sample? -- and what that separates")
        print(f"      band floor (normalised)          {IN['band_floor_normalised']:.5f}")
        print(f"      quietest layer L{IN['quietest_layer']:<3}                {IN['quietest_bound']:.5f}"
              f"   strict min of {IN['n_layers']}")
        print(f"      p10 layer     L{IN['p10_layer']:<3}                {IN['p10_bound']:.5f}"
              f"   selection-robust, and the operative bound")
        print(f"      *** RETRACTED: Spearman(layer effect scale, layer spread) = "
              f"{IN['spearman_scale_vs_spread']:+.3f} over {IN['n_layers']} layers -- a quiet layer "
              f"is quiet in BOTH terms, so it bounds only the item noise of equally quiet heads")
        print(f"      -> the withdrawn reading was: at most {IN['bound_pct_of_floor_variance']:.2f}% of the floor's VARIANCE "
              f"can be item sampling ({IN['strict_pct_of_floor_variance']:.2f}% on the strict min)")
        print(f"      the floor is component choice. Which makes the next line the real result:")
        print(f"      {'head':<9}{'drop':>9}{'x item-noise':>14}{'x floor':>9}   measurable / distinctive")
        for e in IN['effects']:
            print(f"      {e['head']:<9}{e['drop']:>+9.4f}{e['x_item_noise']:>14.1f}"
                  f"{e['x_floor']:>9.2f}   {'YES' if e['measurable'] else 'no ':<4}/ "
                  f"{'YES' if e['distinctive'] else 'no'}")
        print(f"      {IN['n_measurable_UNVERIFIED']} of {IN['n_total']} would be 'measurable' "
              f"-- UNVERIFIED, the threshold is a quiet-layer bound applied to live heads; "
              f"{IN['n_distinctive']} of {IN['n_total']} are DISTINCTIVE")
        print(f"      -> 'inside the noise floor' was conflating two different failures\n")

    if FA:
        print("R1* AUDIT OF THE FLOOR ITSELF -- the reference class had never been checked")
        print(f"      30-draw floor replayed from seed {FA['draw_seed']}: {FA['sampled_floor']:.10f}")
        print(f"      the value R1 recorded            : {FA['recorded_floor']:.10f}"
              f"   (reconstruction error {FA['reconstruction_error']:.2e})")
        print(f"      EXHAUSTIVE over all {FA['n_band_heads']} band heads : "
              f"{FA['exhaustive_floor']:.4f}   -- {FA['divergence_pct']:.1f}% above the sampled one")
        print(f"      what a {FA['n_draws']}-draw floor from this population looks like: "
              f"p05 {FA['boot_p05']:.4f}  median {FA['boot_median']:.4f}  p95 {FA['boot_p95']:.4f}"
              f"  = {FA['boot_spread_x']:.1f}x")
        print(f"      -> the headline floor sits at the {FA['sampled_floor_percentile']:.1f}th "
              f"percentile of ITS OWN sampling distribution: typical, and unresolved")
        print(f"      circularity: {', '.join(FA['contaminating_heads'])} are IN the null that "
              f"judges them; leave-them-out floor {FA['leave_out_floor']:.4f}")
        print(f"      {'head':<9}{'drop':>9}{'x samp':>9}{'x l-o-o':>9}{'x exhaust':>11}")
        for e in FA['per_effect']:
            print(f"      {e['head']:<9}{e['drop']:>+9.4f}{e['x_sampled']:>9.2f}"
                  f"{e['x_leave_out']:>9.2f}{e['x_exhaustive']:>11.2f}"
                  f"{'   <- in the null' if e['in_the_null'] else ''}")
        print(f"      inside: sampled {FA['n_inside_sampled']}/{FA['n_total']}  "
              f"leave-out {FA['n_inside_leave_out']}/{FA['n_total']}  "
              f"EXHAUSTIVE {FA['n_inside_exhaustive']}/{FA['n_total']}\n")

    if NINE:
        print("R9  the floor at every layer -- is R1's band-vs-sham ratio a DEPTH artifact?")
        print(f"      {'model':<17}{'quietest':>16}{'noisiest':>16}{'stack':>8}"
              f"{'max adj':>12}{'band/sham':>11}{'rho':>7}")
        for nm, r in NINE['models'].items():
            print(f"      {nm:<17}L{r['quietest_layer']:<3}{r['quietest_floor']:>11.4f}"
                  f"  L{r['noisiest_layer']:<3}{r['noisiest_floor']:>11.4f}"
                  f"{r['stack_spread']:>7.1f}x"
                  f"  L{r['largest_adjacent_at_layer']}->{r['largest_adjacent_at_layer']+1}"
                  f"{r['largest_adjacent_ratio']:>5.1f}x{r['band_over_sham']:>10.2f}x"
                  f"{r['spearman_rho_layer_sd']:>7.3f}")
        print(f"      stack spread {NINE['stack_spread_min']:.1f}x-{NINE['stack_spread_max']:.1f}x"
              f"  |  largest ADJACENT jump {NINE['adjacent_ratio_min']:.1f}x-"
              f"{NINE['adjacent_ratio_max']:.1f}x -- NOT the same number, and the pages said it was")
        print(f"      rho > 0 on {NINE['n_rho_positive']} of {NINE['n_models']}: the floor grows "
              f"with depth, so R1's two arms differ in WHERE they sit as well as in what they are")
        print(f"      gate REFUSED: predicted band sd is NEGATIVE on "
              f"{NINE['n_negative_predicted_sd']} of {NINE['n_models']} "
              f"-- the estimator extrapolates to a depth only the band occupies\n")

    if TEN:
        for nm, r in TEN.items():
            print(f"R10 {nm}: every head once, {r['sampling']}, {r['rooms']}")
            if r['per_head_L22']:
                ph = sorted(r['per_head_L22'].items(), key=lambda kv: -abs(kv[1]))
                print("      L22 all heads: " +
                      '  '.join(f"h{h}{v:+.4f}" for h, v in ph[:6]))
                print("                     " +
                      '  '.join(f"h{h}{v:+.4f}" for h, v in ph[6:]))
            print(f"      {'head':<9}{'drop':>9}{'own 2sd':>10}{'x own':>7}{'x pooled':>10}")
            for e in r['effects_vs_own_layer']:
                print(f"      {e['head']:<9}{e['drop']:>+9.4f}{e['own_floor_2sd']:>10.4f}"
                      f"{e['x_own']:>7.2f}{e['x_pooled']:>10.2f}")
            print(f"      inside their OWN layer's floor {r['n_inside_own']} of "
                  f"{len(r['effects_vs_own_layer'])}; inside the band-pooled floor "
                  f"{r['n_inside_pooled']} of {len(r['effects_vs_own_layer'])}   "
                  f"rho {r['spearman_rho_layer_sd']:+.3f}\n")

    if SN:
        n = SN['null']
        print(f"R1'' the k=5 SET-level null -- which splits \"inside the floor\" into two causes")
        print(f"      null over {SN['n_draws']} random 5-head draws: mean {n['mean']:+.4f} "
              f"sd {n['sd']:.4f}  p95 {n['p95']:+.4f}")
        for k, v in SN['sets'].items():
            print(f"      {k:<26}{v['drop']:>+10.4f}   {v['pct_in_null']:>5.1f}th percentile")
        print(f"      -> the COPY circuit is a genuine resolution limit; the READ candidates are "
              f"not\n")

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
                  f"randdir {R['median_rr_randdir']:.2f}x  -> {R['gate']}"
                  f"  ({R['gate_reason']})")
        if R.get('sign_inverted_arms'):
            print(f"      *** POSITIVE CONTROL SIGN INVERTED vs the zero arm on: "
                  f"{', '.join(R['sign_inverted_arms'])} -- |PC| > sd passes these")
            print(f"      readability order low->high: "
                  f"{' < '.join(R['readability_order_low_to_high'])}"
                  f"  -- same order in {R['n_cells_matching_order']} of "
                  f"{R['n_cells_total']} cells (within-cell, no ratio, no inclusion rule)")

    if E8:
        print("\nR8  which COMPONENT of a head's output does the intervention destroy?")
        print(f"      {'model':<16}{'mean':>8}{'const_only':>12}{'shrink':>9}{'randdir':>9}"
              f"   overshoot  order-eligible")
        for r in E8['rows']:
            f = lambda k: (f"{r[f'read_{k}']:.2f}" + ('' if r[f'ok_{k}'] else '!'))
            print(f"      {r['model']:<16}{f('mean'):>8}{f('constant_only'):>12}"
                  f"{f('shrink'):>9}{f('randdir'):>9}{r['overshoot']:>11}"
                  f"   {r['order_eligible']} {','.join(r['why_ineligible'])}")
        print(f"      ! = positive control sign-inverted vs the zero arm; that arm is inadmissible")
        print(f"      constant_only ~ shrink: {E8['n_const_approx_shrink']} of {E8['n_cs']}  |  "
              f"mean is lowest: {E8['n_mean_lowest']} of {E8['n_cm']}  |  "
              f"order-eligible {E8['n_order_eligible']} of {len(E8['rows'])} -> gate NOT MET")

    if args.check:
        claims = [
            ('R1 ratio min', A['ratio_min'], 2.74, 0.01),
            ('R1 ratio max', A['ratio_max'], 12.27, 0.01),
            ('R1 informative models', A['n_informative'], 4, 0),
            ('R1 prior effects inside the floor', PE['n_inside'] if PE else -1, 7, 0),
            ('R1 prior effects total', PE['n_total'] if PE else -1, 8, 0),
            ('R1 COPY set percentile', SN['sets']['COPY']['pct_in_null'] if SN else -1, 0.0, 0.05),
            ('R1 READ set percentile', SN['sets']['READ']['pct_in_null'] if SN else -1, 46.667, 0.01),
            ('R10 inside own-layer floor',
             list(TEN.values())[0]['n_inside_own'] if TEN else -1, 8, 0),
            ('R10 inside pooled floor',
             list(TEN.values())[0]['n_inside_pooled'] if TEN else -1, 7, 0),
            # THE FLOOR'S OWN AUDIT. The reconstruction error is asserted at ZERO because it is a
            # replay of a deterministic draw against an exhaustive table, not an estimate: any
            # non-zero value means the seed, the pools, the call order or the exhaustive run have
            # diverged, and the headline floor would no longer be the number R1 measured.
            ('R1* floor reconstruction error', FA['reconstruction_error'] if FA else -1, 0.0, 0.0),
            ('R1* exhaustive floor', FA['exhaustive_floor'] if FA else -1, 0.4870, 0.0001),
            ('R1* divergence pct', FA['divergence_pct'] if FA else -1, 10.246, 0.001),
            ('R1* sampling spread x', FA['boot_spread_x'] if FA else -1, 2.685, 0.001),
            ('R1* inside sampled', FA['n_inside_sampled'] if FA else -1, 7, 0),
            ('R1* inside exhaustive', FA['n_inside_exhaustive'] if FA else -1, 8, 0),
            ('R1* contaminating heads', len(FA['contaminating_heads']) if FA else -1, 2, 0),
            # THE SCOPE ERROR ASSERTED AS TWO SEPARATE NUMBERS. Both pages read the whole-stack
            # spread and wrote "neighbouring layers"; asserting only one of them would let the
            # confusion come back as soon as either page is edited.
            ('R9 stack spread min', NINE['stack_spread_min'] if NINE else -1, 8.062, 0.001),
            ('R9 stack spread max', NINE['stack_spread_max'] if NINE else -1, 96.151, 0.001),
            ('R9 largest adjacent jump min', NINE['adjacent_ratio_min'] if NINE else -1, 4.847, 0.001),
            ('R9 largest adjacent jump max', NINE['adjacent_ratio_max'] if NINE else -1, 15.217, 0.001),
            ('R9 models with negative predicted sd',
             NINE['n_negative_predicted_sd'] if NINE else -1, 2, 0),
            ('R9 models with rho > 0', NINE['n_rho_positive'] if NINE else -1, 4, 0),
            # THE SHARPEST RESULT IN THE REPOSITORY, asserted so it cannot silently drift:
            # three of the eight effects are many times the instrument's own noise, and NONE of
            # the eight is distinguishable from a random head. If either count moves, the front
            # page's central paragraph is wrong and the build must say so.
            ('ITM measurable (UNVERIFIED, asserted only so the retraction is checkable)',
             IN['n_measurable_UNVERIFIED'] if IN else -1, 3, 0),
            ('ITM distinctive', IN['n_distinctive'] if IN else -1, 0, 0),
            ('ITM item-noise share of floor variance',
             IN['bound_pct_of_floor_variance'] if IN else -1, 0.659, 0.001),
            ('ITM copy head vs item noise',
             next((e['x_item_noise'] for e in IN['effects'] if e['head'] == 'L22H7'), -1)
             if IN else -1, 3.33, 0.01),
            ('SET copy circuit x floor',
             SL['sets']['COPY']['x_floor_2sd'] if SL else -1, 1.6453, 0.0001),
            ('SET copy circuit z vs null mean',
             SL['sets']['COPY']['z_from_null_mean'] if SL else -1, -3.291, 0.001),
            ('SET k5 over k1 sd', SL['k5_over_k1_sd'] if SL else -1, 2.017, 0.001),
            # R12'S PREDICTIONS, ASSERTED BEFORE ITS RUN LANDS. If either moves, the
            # pre-registration has been edited after the fact and the build says so.
            ('R15 spearman abs', R15['spearman_abs'] if R15 else -1, 0.6092, 0.0005),
            ('R15 spearman signed', R15['spearman_signed'] if R15 else -1, 0.7175, 0.0005),
            ('R15 floor shuffled', R15['floor_shuffled'] if R15 else -1, 0.4023, 0.0005),
            ('R15 margin vs floor', R15['spearman_margin_vs_floor'] if R15 else -1, 0.8810, 0.0005),
            ('R12C 3b last-layer rate',
             DS['qwen2.5-3b']['last_layer_rate'] if DS else -1, 0.0, 0.0001),
            ('R12C 1.5b last-layer rate',
             DS['qwen2.5-1.5b']['last_layer_rate'] if DS else -1, 0.166667, 0.0001),
            ('R12C 1.5b peak rate',
             DS['qwen2.5-1.5b']['peak_rate'] if DS else -1, 0.833333, 0.0001),
            ('R12C depth trend all-28',
             DS['spearman_layer_vs_magnitude_all'] if DS else -1, 0.7947, 0.0005),
            ('R16 spearman name signed',
             SV['spearman_name_signed'] if SV else -1, -0.1142, 0.0001),
            ('R16 spearman room', SV['spearman_room'] if SV else -1, -0.1885, 0.0001),
            ('R16 spearman name', SV['spearman_name'] if SV else -1, -0.3952, 0.0001),
            ('R2T fixed offset', TA2['offset_to_answer'] if TA2 else -1, 64, 0),
            ('R2* clears centred', TC['n_clear_centred'] if TC else -1, 4, 0),
            ('R2* clears uncentred', TC['n_clear_uncentred'] if TC else -1, 4, 0),
            ('R2* min clearing', TC['r2_min_clearing'] if TC else -1, 1.19996, 0.00001),
            ('TAX taxonomy-exists unreachable from',
             TP['taxonomy_exists_unreachable_from_n'] if TP else -1, 22, 0),
            ('TAX reachable verdicts', len(TP['reachable_verdicts']) if TP else -1, 1, 0),
            ('TAX verdict fires under random labels',
             TP['verdict_fires_under_random_labels_pct'] if TP else -1, 100.0, 0.01),
            ('TAX chi-square', TP['chi_square'] if TP else -1, 34.676, 0.001),
            ('R15 selection skew points', FD['skew_points'] if FD else -1, 10.2, 0.05),
            ('R15 kept under shuffling', FD['n_kept'] if FD else -1, 96, 0),
            ('R12 centroid', TW['centroid'] if TW else -1, 22.833, 0.001),
            ('R12 CI half-width',
             TW['centroid_ci95_halfwidth'] if TW else -1, 1.2439, 0.0001),
            ('R12 CI lower', TW['centroid_ci95_lo'] if TW else -1, 21.52, 0.01),
            ('R12 depth fraction', TW['depth_fraction'] if TW else -1, 0.6524, 0.0001),
            ('R14 shuffled accuracy', FT['accuracy_shuffled'] if FT else -1, 0.8, 0.001),
            ('R14 ends minus middle z', FT['ends_minus_middle_z'] if FT else -1, 4.96, 0.01),
            ('R14 worst line over chance', FT['worst_over_chance'] if FT else -1, 2.286, 0.001),
            ('TSK cross-model cells probed',
             TA['cross_model']['n_cells'] if (TA and TA.get('cross_model')) else -1, 8, 0),
            ('TSK cross-model query line',
             TA['cross_model']['the_line'] if (TA and TA.get('cross_model')) else -1, 0, 0),
            ('TSK query line index', TA['query_line_index'] if TA else -1, 0, 0),
            ('TSK answer share min pct', TA['answer_min_share_pct'] if TA else -1, 23.5, 0.05),
            ('TSK answer share max pct', TA['answer_max_share_pct'] if TA else -1, 26.25, 0.05),
            ('CTR clears centred', CN['n_clear_centred'] if CN else -1, 1, 0),
            ('CTR clears uncentred', CN['n_clear_uncentred'] if CN else -1, 0, 0),
            ('CTR studied-band null mean', CN['null_mean'] if CN else -1, 0.0479, 0.0001),
            ('CTR sham-band mean over sd',
             CN['bands']['sham_L0_7']['mean_over_sd'] if CN else -1, 0.1005, 0.0001),
            # BOTH FORMS ASSERTED. The uncentred pair is what R12's thresholds were committed
            # from; the centred pair is what the corrected statistic gives. Asserting only the
            # current one would let the addendum drift from the history it describes.
            ('R12 absolute prediction, centred',
             RC['predicted_centroid_absolute_36L'] if RC else -1, 17.2347, 0.0001),
            ('R12 relative prediction, centred',
             RC['predicted_centroid_relative_36L'] if RC else -1, 22.3413, 0.0001),
            ('R12 centroid, uncentred as committed',
             RC['clearing_centroid_layer_UNCENTRED'] if RC else -1, 17.3878, 0.0001),
            ('R12 ambiguous window lower edge',
             RC['r12_window_absolute_max'] if RC else -1, 19.5, 0.0),
            ('R12 ambiguous window upper edge',
             RC['r12_window_relative_min'] if RC else -1, 20.5, 0.0),
            ('REF depth vs clearing rate',
             RC['spearman_layer_vs_clearing_rate'] if RC else -1, 0.645, 0.001),
            ('REF copy head rank in its layer clearing set',
             RC['copy_head_rank_in_its_layer_clearing_set'] if RC else -1, 5, 0),
            ('REF published heads in the peak layers',
             RC['n_published_in_peak_layers'] if RC else -1, 4, 0),
            ('REF sham floor', RC['sham_floor'] if RC else -1, 0.0792, 0.0001),
            ('REF band over sham ratio', RC['ratio'] if RC else -1, 6.1508, 0.0001),
            ('REF eight clearing sham', RC['n_clear_sham'] if RC else -1, 3, 0),
            ('REF band heads clearing sham',
             RC['band_heads_clearing_sham'] if RC else -1, 78, 0),
            ('PWR positive-control heads', PW['n_positive_control'] if PW else -1, 9, 0),
            ('PWR heads with dynamic range', PW['n_with_room'] if PW else -1, 167, 0),
            ('PWR undecidable heads', len(PW['undecidable']) if PW else -1, 1, 0),
            ('R11 resolvable on the disjoint set', EL['n_resolvable_B'] if EL else -1, 7, 0),
            ('R11 band verdicts agreeing', EL['band_verdicts_agree'] if EL else -1, 157, 0),
            ('R11 band ratio Spearman', EL['band_ratio_spearman'] if EL else -1, 0.9825, 0.0001),
            ('R11 resolvable at 2 sigma', EL['n_resolvable'] if EL else -1, 8, 0),
            ('R11 agreement inside the SEM band', EL['agree_within_sem'] if EL else -1, 164, 0),
            ('R11 floor divergence across item sets',
             EL['floor_divergence_pct'] if EL else -1, 0.4327, 0.0001),
            # CENTRED now (D87). The uncentred +0.9778 is kept as its own row so the correction is
            # checkable, not merely asserted.
            ('R11 rank Spearman A vs B', EL['rank_spearman_A_vs_B'] if EL else -1, 0.9570, 0.0001),
            ('R11 rank Spearman uncentred',
             EL['rank_spearman_uncentred'] if EL else -1, 0.9778, 0.0001),
            ('R11 top-9 overlap across item sets',
             EL['top9_overlap_across_item_sets'] if EL else -1, 7, 0),
            ('REP max input replication difference',
             IR['max_abs_diff'] if IR else -1, 3.608e-06, 1e-8),
            ('RNK published in normalised top nine',
             RV['published_in_top9_by_layer_sd'] if RV else -1, 0, 0),
            ('RNK top-nine overlap between normalisations',
             RV['top9_overlap_between_normalisations'] if RV else -1, 6, 0),
            ('RNK excess kurtosis of the band', RV['excess_kurtosis'] if RV else -1, 7.43, 0.01),
            ('RNK normal-predicted tail count',
             RV['expected_beyond_2sd_normal'] if RV else -1, 7.64, 0.01),
            ('RNK leave-one-out clearing count',
             RV['n_clear_leave_one_out'] if RV else -1, 9, 0),
            ('RNK heads clearing the exhaustive floor', RV['n_clear'] if RV else -1, 10, 0),
            ('RNK published heads among them',
             RV['n_published_among_clearing'] if RV else -1, 1, 0),
            ('RNK proven copy head rank', RV['copy_head_rank'] if RV else -1, 41, 0),
            ('RNK clearing heads where ablation HELPS',
             RV['n_clear_positive'] if RV else -1, 7, 0),
            ('LDG defect rows', DL['n'] if DL else -1, 111, 0),
            ('LDG largest bin', DL['largest_bin'] if DL else -1, 27, 0),
            ('LDG outside reader pct', DL['outside_reader_pct'] if DL else -1, 8.108, 0.001),
            # THE ASSERTION FIRED, AND IT WAS RIGHT. It was written at n=37 to fail the build
            # the day an instrument finally caught a CONTROL defect. At n=49 the provenance
            # validator fired on its own during a routine gate run, and what it revealed was a
            # false-conviction rule inside itself -- the first CONTROL defect any instrument here
            # has found. The claim the detector suite was built from is now FALSE, and the check
            # written to notice that is what noticed. Expected count updated, not the check.
            ('LDG instrument-found CONTROL defects',
             DL['cross_tab']['CONTROL']['instrument'] if DL else -1, 2, 0),
            # -> 3 with D84: R15's own pre-registered third reading found that the floor is a
            # function of the task's headroom. The instrument found the scope of its own number.
            ('LDG instrument-found SCOPE defects',
             DL['cross_tab']['SCOPE']['instrument'] if DL else -1, 3, 0),
            ('VAR in-sample floor share', VD['in_sample']['floor_share_pct'] if VD else -1,
             72.05, 0.01),
            ('VAR held-out pairings near 52',
             VD['held_out_sweep']['n_within_3pp_of_52'] if VD else -1, 0, 0),
            ('R2 valid cells', B['n_valid'], 4, 0),
            ('R2 inverted', B['n_inverted'], 0, 0),
            ('R5 cells', E['n_cells'], 6, 0),
            ('R5 worse on 2sd', E['n_worse_2sd'], 6, 0),
            ('R5 worse on p10-p90', E['n_worse_w'], 6, 0),
        ]
        if R and R.get('gate'):
            # A VERDICT IS A CLAIM AND WAS NEVER CHECKED. --check asserted numbers and
            # prose_numbers.py asserts decimals; a wrong verdict string passed both for as long
            # as it existed. Asserted here as a string comparison against the shipped README.
            shipped = (HERE / 'R7_norm_matched' / 'README.md').read_text()
            want_not_met = '`NOT MET` on the gate' in shipped
            if want_not_met and R['gate'] != 'NOT MET':
                print(f"  STALE: R7 README says NOT MET, headline computes {R['gate']}")
                return 1
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
