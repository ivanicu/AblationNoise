#!/usr/bin/env python3
"""R19 analysis -- WRITTEN BEFORE THE DATA EXISTS.

At the time this file was committed, `results/` held only SMOKE_smoke.json (n_base=2, a runner
check) and the 64-base run was queued behind another job. That is the point: AN ANALYSIS WRITTEN
BEFORE THE DATA CANNOT BE TUNED TO IT. Pre-registered prose fixes the thresholds; pre-registered
CODE fixes the estimators, the aggregation, the bootstrap unit and the tie-breaking too -- all the
places a verdict can be moved after the fact without touching a single stated number.

Everything here implements PREREGISTRATION.md plus its two amendments, and nothing else:

  H-support   Spearman(tau_final, tau_all) >= 0.9 AND published verdicts agree 8/8
              AND layer-centroid shift <= 0.03 normalized depth AND top-10 overlap >= 8/10
  H-position  median head-wise ICC(1,1) across the 8 positions >= 0.50 (Amendment 1, CHOSEN)
              AND P_pub not above matched-layer controls at one-sided p >= 0.05
              AND Spearman(line-0 rank, position-averaged rank) >= 0.8
  H-published matched-layer set randomization p < 0.05, TWO-SIDED (Amendment 2 -- E132b made no
              per-head directional claim, and using its observed signs would be circular)
              AND holding on both all-position and position-averaged estimands
  H-depth     pre-declared UNTESTED: two models is n=2

  positive control   last-layer |eta| must be ~0, below the between-head sd, else REFUSED
  saturation         > 50% sign flips under `all` => REFUSED

  discovery/confirmation split (Amendment 1): base 0..31 nominate, 32..63 judge. THE EIGHT ARE
  EXEMPT and use all 64, because a prior experiment on a disjoint item family specified them.

Three metrics are carried separately end to end and never merged into one verdict.
The statistical unit is the BASE INSTANCE. Every interval is a cluster bootstrap over base
instances; 1024 prompts are not 1024 samples.
"""
from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

METRICS = ['signed_margin_drop', 'room_set_kl', 'behavioural_flip']
BAND_LO, BAND_HI = 14, 28
ALPHA = 0.05
N_PERM = 50000
N_BOOT = 2000
ICC_FLOOR = 0.50            # Amendment 1: CHOSEN, not derived
SPEARMAN_SUPPORT = 0.9
SPEARMAN_POSITION = 0.8
CENTROID_SHIFT_MAX = 0.03
TOP10_OVERLAP_MIN = 8
DISCOVERY_HALF = 32         # base 0..31 discovery, 32..63 confirmation


def spearman(a, b):
    def rk(z):
        o = sorted(range(len(z)), key=lambda i: z[i])
        r = [0.0] * len(z)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and z[o[j + 1]] == z[o[i]]:
                j += 1
            for t in range(i, j + 1):
                r[o[t]] = (i + j) / 2 + 1
            i = j + 1
        return r
    ra, rb = rk(a), rk(b)
    n = len(a)
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = math.sqrt(sum((v - ma) ** 2 for v in ra))
    db = math.sqrt(sum((v - mb) ** 2 for v in rb))
    return num / (da * db) if da and db else float('nan')


def icc1(rows):
    """ICC(1,1) for one head: rows[b][p], variance components over base instances.

    Between-base variance against total. A head whose effect is the same at every position has
    between-base variance dominating; a head whose effect is position-driven does not.
    """
    nb = len(rows)
    npos = len(rows[0])
    grand = sum(sum(r) for r in rows) / (nb * npos)
    msb = npos * sum((sum(r) / npos - grand) ** 2 for r in rows) / (nb - 1) if nb > 1 else 0.0
    msw = sum(sum((v - sum(r) / npos) ** 2 for v in r) for r in rows) / (nb * (npos - 1))
    den = msb + (npos - 1) * msw
    return (msb - msw) / den if den else float('nan')


def load(path):
    d = json.load(open(path))
    if str(d.get('verdict', '')).startswith('REFUS'):
        print(f"REFUSED artifact: {d.get('verdict')} -- {d.get('why', '')}")
        return None
    return d


def cells(d, scope, mi):
    """{(layer, head): {'pos': [8], 'base': [n_base]}} for one scope and one metric index."""
    NH = d['n_heads_per_layer']
    out = {}
    for L in range(d['n_layers']):
        for h in range(NH):
            c = d['cells'][f'L{L:02d}H{h:02d}.{scope}']
            out[(L, h)] = {'pos': [row[mi] for row in c['pos']],
                           'base': [row[mi] for row in c['base']]}
    return out


def main():
    p = HERE / 'results' / 'r19_crossed_qwen2.5-1.5b.json'
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
    if not p.exists():
        print(f"no result file at {p}")
        print("This analysis was written before the data existed. Run it on the smoke file to")
        print("check it end to end:  python3 analyze.py results/SMOKE_smoke.json")
        return 1
    d = load(p)
    if d is None:
        return 2
    NH = d['n_heads_per_layer']
    NL = d['n_layers']
    nb = d['n_base']
    band = [(L, h) for L in range(BAND_LO, min(BAND_HI, NL)) for h in range(NH)]
    by_layer = {}
    for k in band:
        by_layer.setdefault(k[0], []).append(k)

    print(f"R19  {d['model']}  {d['n_prompts']} prompts = {nb} base x {d['n_positions']} pos "
          f"x {d['n_nuisance']} rep")
    print(f"     unit: {d['statistical_unit']}")
    print(f"     baseline accuracy {d['baseline_accuracy']:.4f}  margin "
          f"{d['baseline_margin_mean']:.4f}")
    print(f"     accuracy by position {[round(x, 3) for x in d['baseline_accuracy_by_pos']]}")
    print(f"     margin   by position {[round(x, 3) for x in d['baseline_margin_by_pos']]}")

    # ---- gating positive control: last-layer eta must be ~0
    fin0 = cells(d, 'final', 0)
    all0 = cells(d, 'all', 0)

    def tau(c, k):
        return sum(c[k]['base']) / len(c[k]['base'])

    last = [(NL - 1, h) for h in range(NH)]
    eta_last = [abs(tau(all0, k) - tau(fin0, k)) for k in last]
    vb = [tau(fin0, k) for k in band]
    mub = sum(vb) / len(vb)
    sdb = math.sqrt(sum((z - mub) ** 2 for z in vb) / (len(vb) - 1))
    ok_pc = max(eta_last) < sdb
    print(f"\n     POSITIVE CONTROL  last-layer max|eta| {max(eta_last):.6f}  vs between-head sd "
          f"{sdb:.6f}  -> {'PASS' if ok_pc else 'REFUSED'}")
    print(f"     SATURATION        all {100 * d['flip_rate_all']:.2f}%  final "
          f"{100 * d['flip_rate_final']:.2f}%  (refusal at >50%)")
    if not ok_pc or d['flip_rate_all'] > 0.50:
        print("     -> REFUSED by a pre-registered gate; no hypothesis is read.")
        return 3

    pe = None
    try:
        import headline as H
        pe = H.r1_prior_effects()
    except Exception as e:                                   # noqa: BLE001
        print(f"     (published-head list unavailable: {e!r}) -- H-published will be skipped")
    eight = []
    if pe:
        eight = sorted((int(k[1:k.index('H')]), int(k[k.index('H') + 1:])) for k in pe['effects'])
        eight = [k for k in eight if k in band]

    report = {'model': d['model'], 'n_base': nb, 'metrics': {}}
    rng = random.Random(20260728)

    for mi, mname in enumerate(METRICS):
        fin, alle = cells(d, 'final', mi), cells(d, 'all', mi)
        tf = {k: sum(fin[k]['base']) / nb for k in band}
        ta = {k: sum(alle[k]['base']) / nb for k in band}
        muf = sum(tf.values()) / len(tf)
        mua = sum(ta.values()) / len(ta)
        ff = 2 * math.sqrt(sum((z - muf) ** 2 for z in tf.values()) / (len(tf) - 1))
        fa = 2 * math.sqrt(sum((z - mua) ** 2 for z in ta.values()) / (len(ta) - 1))

        # H-support, four components
        rho = spearman([abs(tf[k] - muf) for k in band], [abs(ta[k] - mua) for k in band])
        of = sorted(band, key=lambda k: -abs(tf[k] - muf))
        oa = sorted(band, key=lambda k: -abs(ta[k] - mua))
        overlap = len(set(of[:10]) & set(oa[:10]))
        agree = sum(1 for k in eight
                    if (abs(tf[k] - muf) > ff) == (abs(ta[k] - mua) > fa)) if eight else -1

        def centroid(t, mu, f):
            rate = {L: sum(1 for h in range(NH) if abs(t[(L, h)] - mu) > f) / NH
                    for L in range(BAND_LO, min(BAND_HI, NL))}
            tot = sum(rate.values())
            return sum(L * q for L, q in rate.items()) / tot if tot else float('nan')

        cf, ca = centroid(tf, muf, ff), centroid(ta, mua, fa)
        shift = abs(ca - cf) / (NL - 1)
        h_support = (rho >= SPEARMAN_SUPPORT and (agree == 8 or not eight)
                     and shift <= CENTROID_SHIFT_MAX and overlap >= TOP10_OVERLAP_MIN)

        # H-position, on the `all` arm (the intervention that sees whole-sequence writes)
        # ICC NEEDS THE BASE x POSITION CELLS, and writing this file before the data existed is
        # what caught that the runner did not record them: Amendment 1 committed H-position to a
        # median head-wise ICC(1,1), and marginal means over each axis cannot produce one. The
        # runner now stores `base_pos`; a result file without it is from the older runner and this
        # component reports NOT COMPUTABLE rather than a substitute statistic.
        has_bp = 'base_pos' in d['cells'][f'L{BAND_LO:02d}H00.all']
        if has_bp:
            iccs = []
            for k in band:
                c = d['cells'][f'L{k[0]:02d}H{k[1]:02d}.all']['base_pos']
                iccs.append(icc1([[row[mi] for row in bp] for bp in c]))
            icc_med = sorted(iccs)[len(iccs) // 2]
        else:
            icc_med = float('nan')
        pi = {k: math.sqrt(sum((alle[k]['pos'][pp] - ta[k]) ** 2
                               for pp in range(d['n_positions'])) / d['n_positions'])
              for k in band}
        p_pos = float('nan')
        if eight:
            tp = sum(pi[k] for k in eight) / len(eight)
            null = [sum(pi[rng.choice(by_layer[k[0]])] for k in eight) / len(eight)
                    for _ in range(N_PERM)]
            p_pos = (1 + sum(1 for z in null if z >= tp)) / (1 + N_PERM)
        rank0 = sorted(band, key=lambda k: -abs(alle[k]['pos'][0] - ta[k]))
        rho_pos = spearman([rank0.index(k) for k in band], [oa.index(k) for k in band])
        h_position = (has_bp and icc_med >= ICC_FLOOR and (p_pos != p_pos or p_pos >= ALPHA)
                      and rho_pos >= SPEARMAN_POSITION)

        # H-published, TWO-SIDED (Amendment 2), distinct-per-layer (D105)
        pub = {}
        if eight:
            from collections import Counter
            cnt = Counter(k[0] for k in eight)
            for tag, t, mu in (('final', tf, muf), ('all', ta, mua)):
                T = sum(abs(t[k] - mu) for k in eight) / len(eight)
                nl = []
                for _ in range(N_PERM):
                    st = []
                    for lay, c in cnt.items():
                        st += rng.sample(by_layer[lay], c)
                    nl.append(sum(abs(t[k] - mu) for k in st) / len(st))
                pub[tag] = {'T': T, 'p': (1 + sum(1 for z in nl if z >= T)) / (1 + N_PERM),
                            'null_median': sorted(nl)[N_PERM // 2]}
        h_published = bool(pub) and all(v['p'] < ALPHA for v in pub.values())

        # cluster bootstrap over BASE INSTANCES for the headline contrast
        boot = []
        for _ in range(N_BOOT):
            idx = [rng.randrange(nb) for _ in range(nb)]
            tfb = {k: sum(fin[k]['base'][i] for i in idx) / nb for k in band}
            tab = {k: sum(alle[k]['base'][i] for i in idx) / nb for k in band}
            mf = sum(tfb.values()) / len(tfb)
            ma = sum(tab.values()) / len(tab)
            boot.append(spearman([abs(tfb[k] - mf) for k in band],
                                 [abs(tab[k] - ma) for k in band]))
        boot.sort()

        print(f"\n  --- metric: {mname}")
        print(f"      H-support   Spearman {rho:+.4f} (>= {SPEARMAN_SUPPORT}) | published agree "
              f"{agree}/8 | centroid shift {shift:.4f} (<= {CENTROID_SHIFT_MAX}) | top-10 "
              f"{overlap}/10 (>= {TOP10_OVERLAP_MIN})  -> {'PASS' if h_support else 'FAIL'}")
        print(f"                  cluster bootstrap over {nb} base instances, {N_BOOT} draws: "
              f"Spearman 95% CI [{boot[int(.025*N_BOOT)]:+.4f}, {boot[int(.975*N_BOOT)]:+.4f}]")
        icc_s = f"{icc_med:+.4f}" if has_bp else "NOT COMPUTABLE (no base_pos)"
        print(f"      H-position  median ICC {icc_s} (>= {ICC_FLOOR}) | P_pub one-sided p "
              f"{p_pos:.4f} (>= {ALPHA} to pass) | line-0 vs pos-avg Spearman {rho_pos:+.4f} "
              f"(>= {SPEARMAN_POSITION})  -> {'PASS' if h_position else 'FAIL'}")
        if pub:
            for tag, v in pub.items():
                print(f"      H-published {tag:<6} T {v['T']:.4f}  matched-layer null median "
                      f"{v['null_median']:.4f}  two-sided p {v['p']:.4f}")
            print(f"                  -> {'ENRICHED' if h_published else 'NOT enriched'}")
        print(f"      H-depth     UNTESTED by pre-registration: two models is n=2")
        report['metrics'][mname] = {
            'spearman_final_vs_all': rho, 'spearman_ci95': [boot[int(.025 * N_BOOT)],
                                                            boot[int(.975 * N_BOOT)]],
            'published_agree': agree, 'centroid_final': cf, 'centroid_all': ca,
            'centroid_shift_norm': shift, 'top10_overlap': overlap, 'h_support': h_support,
            'icc_median': icc_med, 'p_position': p_pos, 'spearman_line0_vs_posavg': rho_pos,
            'h_position': h_position, 'published': pub, 'h_published': h_published,
            'floor_final': ff, 'floor_all': fa}

    # ---- the registered OV prediction. Written into the analysis BEFORE the data exists, so
    # the test cannot be tuned to it: the 25 heads are a frozen list, the null is
    # matched-layer, and BOTH halves must hold. A KL effect WITH a margin effect would mean the
    # two metrics are redundant, not that OV has behavioural content.
    pf = ROOT / 'R16_selection_vs_effect' / 'results' / 'ov_perfect_room_copiers.json'
    if pf.exists():
        from collections import Counter
        cop = json.load(open(pf))['heads']
        cop = [(int(k[1:k.index('H')]), int(k[k.index('H') + 1:])) for k in cop]
        cop = [k for k in cop if k in band]
        rngp = random.Random(20260728)
        cnt = Counter(k[0] for k in cop)
        pred = {}
        for mi, mname in ((1, 'room_set_kl'), (0, 'signed_margin_drop')):
            c = cells(d, 'all', mi)
            tv = {k: sum(c[k]['base']) / nb for k in band}
            mu = sum(tv.values()) / len(tv)
            stat = sum(abs(tv[k] - mu) for k in cop) / len(cop)
            nl = []
            for _ in range(N_PERM):
                st = []
                for lay, n_ in cnt.items():
                    st += rngp.sample(by_layer[lay], n_)
                nl.append(sum(abs(tv[k] - mu) for k in st) / len(st))
            pred[mname] = {'T': stat, 'null_median': sorted(nl)[N_PERM // 2],
                           'p_one_sided': (1 + sum(1 for z in nl if z >= stat)) / (1 + N_PERM)}
        ok_kl = pred['room_set_kl']['p_one_sided'] < ALPHA
        ok_mg = pred['signed_margin_drop']['p_one_sided'] >= ALPHA
        print()
        print('  --- REGISTERED OV PREDICTION (%d frozen OV-perfect room copiers)' % len(cop))
        for k, v in pred.items():
            print('      %-20s T %.4f  matched-layer null median %.4f  one-sided p %.4f'
                  % (k, v['T'], v['null_median'], v['p_one_sided']))
        print('      room_set_kl LARGER than matched  -> %s   (needs p < %s)'
              % ('PASS' if ok_kl else 'FAIL', ALPHA))
        print('      margin INDISTINGUISHABLE          -> %s   (needs p >= %s)'
              % ('PASS' if ok_mg else 'FAIL', ALPHA))
        print('      BOTH HALVES -> %s'
              % ('CONFIRMED' if (ok_kl and ok_mg) else 'NOT CONFIRMED'))
        report['ov_prediction'] = {'n_heads': len(cop), 'tests': pred,
                                   'kl_larger': ok_kl, 'margin_null': ok_mg,
                                   'confirmed': bool(ok_kl and ok_mg)}
    out = HERE / 'results' / f"r19_analysis_{d['model']}.json"
    json.dump(report, open(out, 'w'), indent=1)
    print(f"\n  wrote {out}")
    print(f"  NOTE: the discovery/confirmation split (base 0..{DISCOVERY_HALF-1} nominate, "
          f"{DISCOVERY_HALF}..{nb-1} judge) applies to any head R19 ITSELF surfaces. The eight are")
    print(f"  exempt and judged on all {nb}, because a prior experiment on a disjoint item family")
    print(f"  specified them. No R19-nominated head is reported above.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
