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


def _spearman(a, b):
    rk = lambda v: [sorted(v).index(x) for x in v]  # noqa: E731
    x, y = rk(a), rk(b)
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    num = sum((i - mx) * (j - my) for i, j in zip(x, y))
    den = math.sqrt(sum((i - mx) ** 2 for i in x) * sum((j - my) ** 2 for j in y))
    return num / den if den else float('nan')


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

    floor = 2 * sd([v for _, _, v in band])
    order = sorted(band, key=lambda x: -abs(x[2]))
    clear = [x for x in order if abs(x[2]) > floor]
    eight = {(int(m.group(1)), int(m.group(2))): h
             for h in pe['effects'] if (m := _re.match(r'L(\d+)H(\d+)', h))}
    ranks = [{'head': eight[(x, h)], 'rank': i, 'drop': v, 'x_floor': abs(v) / floor}
             for i, (x, h, v) in enumerate(order, 1) if (x, h) in eight]
    return {
        'n_band_heads': len(band), 'floor_2sd': floor,
        'n_clear': len(clear), 'pct_clear': 100 * len(clear) / len(band),
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
        'clearing_heads': [{'head': f'L{x}H{h}', 'drop': v, 'x_floor': abs(v) / floor,
                            'direction': 'ablation HELPS' if v > 0 else 'ablation hurts'}
                           for x, h, v in clear],
        'n_clear_positive': sum(v > 0 for _, _, v in clear),
        'n_published_among_clearing': sum((x, h) in eight for x, h, _ in clear),
        'published_ranks': sorted(ranks, key=lambda r: r['rank']),
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
                     'x_floor_2sd': abs(v['drop']) / (2 * sd),
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
    SR, TEN, NINE = r1_set_null_range(), r10(), r9()
    FA, VD, DL = r1_floor_audit(), variance_decomposition(), defect_ledger()
    IN = item_noise_bound()
    SL = set_level_scale()
    RV = rank_vs_role()

    if args.json:
        print(json.dumps({'r1': A, 'r1_vocabulary': V, 'r2': B, 'r4': D, 'r5': E, 'r6': S, 'r6_diag': G, 'r7': R, 'r8': E8,
                          'r1_prior_effects': PE, 'r1_set_null': SN, 'r1_set_null_range': SR,
                          'r9': NINE, 'r10': TEN, 'r1_floor_audit': FA, 'variance_decomposition': VD, 'defect_ledger': DL, 'item_noise_bound': IN, 'set_level_scale': SL, 'rank_vs_role': RV,
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
                  f"{v['z_from_null_mean']:>+16.2f}{v['sd_beyond_null_min']:>13.2f}")
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
             SL['sets']['COPY']['x_floor_2sd'] if SL else -1, 1.454, 0.001),
            ('SET copy circuit z vs null mean',
             SL['sets']['COPY']['z_from_null_mean'] if SL else -1, -3.291, 0.001),
            ('SET k5 over k1 sd', SL['k5_over_k1_sd'] if SL else -1, 2.017, 0.001),
            ('RNK excess kurtosis of the band', RV['excess_kurtosis'] if RV else -1, 7.43, 0.01),
            ('RNK normal-predicted tail count',
             RV['expected_beyond_2sd_normal'] if RV else -1, 7.64, 0.01),
            ('RNK leave-one-out clearing count',
             RV['n_clear_leave_one_out'] if RV else -1, 9, 0),
            ('RNK heads clearing the exhaustive floor', RV['n_clear'] if RV else -1, 9, 0),
            ('RNK published heads among them',
             RV['n_published_among_clearing'] if RV else -1, 0, 0),
            ('RNK proven copy head rank', RV['copy_head_rank'] if RV else -1, 56, 0),
            ('RNK clearing heads where ablation HELPS',
             RV['n_clear_positive'] if RV else -1, 7, 0),
            ('LDG defect rows', DL['n'] if DL else -1, 50, 0),
            ('LDG largest bin', DL['largest_bin'] if DL else -1, 15, 0),
            ('LDG outside reader pct', DL['outside_reader_pct'] if DL else -1, 14.0, 0.001),
            # THE ASSERTION FIRED, AND IT WAS RIGHT. It was written at n=37 to fail the build
            # the day an instrument finally caught a CONTROL defect. At n=49 the provenance
            # validator fired on its own during a routine gate run, and what it revealed was a
            # false-conviction rule inside itself -- the first CONTROL defect any instrument here
            # has found. The claim the detector suite was built from is now FALSE, and the check
            # written to notice that is what noticed. Expected count updated, not the check.
            ('LDG instrument-found CONTROL defects',
             DL['cross_tab']['CONTROL']['instrument'] if DL else -1, 1, 0),
            ('LDG instrument-found SCOPE defects',
             DL['cross_tab']['SCOPE']['instrument'] if DL else -1, 0, 0),
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
