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
    SR, TEN = r1_set_null_range(), r10()

    if args.json:
        print(json.dumps({'r1': A, 'r1_vocabulary': V, 'r2': B, 'r4': D, 'r5': E, 'r6': S, 'r6_diag': G, 'r7': R, 'r8': E8,
                          'r1_prior_effects': PE, 'r1_set_null': SN, 'r1_set_null_range': SR, 'r10': TEN,
                          'r1_behavioural_scale': BS, 'cross_round_scale': CR},
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
