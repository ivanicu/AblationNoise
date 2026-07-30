#!/usr/bin/env python3
"""Is the ablation-effect distribution's shape a property of the HEAD, or of (HEAD x SUPPORT)?

The navigator ruled that R34's rho(layer, median||E_h||) = +0.7321 / +0.7264 is MEASUREMENT and not
model, because the gradient REVERSES SIGN when the ablation support changes, and no property of a
head can do that. It also killed my own replacement story. Both claims are REPRODUCED here rather
than quoted -- a navigator's judgement binds, its facts do not.

  I_final   the head is zeroed at the FINAL QUERY POSITION only
  I_all     the head is zeroed at ALL 121 POSITIONS
They are bit-identical at the last layer (max|delta| = 0.000e+00, both models) and diverge
monotonically with depth. Same heads, same items, same model: only the SUPPORT of the intervention
differs.

MY OWN HYPOTHESIS, WHICH THIS FILE ALSO TESTS AND WHICH THE NAVIGATOR SAYS DIES: "a late head's
perturbation has fewer remaining layers in which to be absorbed, so it reaches the logits larger."
That predicts I_all shows the SAME-SIGNED, LARGER depth gradient -- more layers, more absorption of
early heads. If I_all's gradient is NEGATIVE, absorption is dead and what remains is that an early
head does its work at NON-FINAL positions: zeroing it at the final query token removes almost none
of that work, while a late head at the final token IS its work.

═══ THE STATISTIC ═══
  X   within-layer rank concordance of a cell's I_final rank against its I_all rank, pooled over
      all WITHIN-LAYER head pairs -- 1.5b 28 x C(12,2) = 1848 pairs, 3b 36 x C(16,2) = 4320.
      Depth is held FIXED inside every pair, so the confound the ruling just exposed cannot enter,
      and each stratum has n = 12 or 16 rather than R34's n = 2.
      X is Kendall-style: (concordant - discordant) / n_pairs, so 0 = no ordering shared, 1 = the
      within-layer ordering is identical under both supports.
  Error bars by LAYER-LEVEL bootstrap, because pairs inside a layer are dependent.

═══ REGISTERED BEFORE THE RUN ═══
  T   X < 0.30 in EITHER model
      ->  "the ablation-effect distribution has a shape that is a property of the head" is DEAD.
          The shape belongs to (head x support); every per-head magnitude claim in R23-R34 is
          re-scoped to I_final; and the shape question is re-asked with SUPPORT as a first-class
          axis in margin-nats.
      X >= 0.30 in BOTH  ->  the within-layer ordering is support-stable and only the DEPTH AXIS is
          the artifact; the shape survives as a head property.

  POSITIVE CONTROL, MANDATORY, ADMISSIBILITY GATE (P5*): the same X on I_final off0 versus I_final
  off400 in 1.5b -- two ITEM SETS at the SAME support -- must return X >= 0.30. If a change of item
  set alone already destroys the within-layer ordering, then a low X against support says nothing
  and the whole comparison is UNVERIFIED.

Zero forward passes. Everything comes from R29's scan JSONs, whose control_per_cell carries `mean`
and `sd_items` per cell for both supports and both models over identical cell sets.
"""
import itertools
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
N_BOOT = 2000
RULE = {'T_min_X': 0.30, 'control_min_X': 0.30, 'n_boot': N_BOOT}
SCAN = REPO / 'R29_cancellation' / 'results'


def load(model, support, off='off0'):
    f = SCAN / f'r29_scan_qwen2.5-{model}_I_{support}_{off}.json'
    if not f.exists():
        return None
    cp = json.load(open(f))['control_per_cell']
    ks = sorted(cp)
    lay = np.array([int(k[1:3]) for k in ks])
    hd = np.array([int(k[4:6]) for k in ks])
    return {'keys': ks, 'layer': lay, 'head': hd,
            'mean': np.array([cp[k]['mean'] for k in ks]),
            'sd': np.array([cp[k]['sd_items'] for k in ks])}


def spearman(a, b):
    def rk(v):
        o = np.argsort(v, kind='mergesort')
        r = np.empty(len(v), float)
        r[o] = np.arange(len(v), dtype=float)
        return r
    x, y = rk(a) - rk(a).mean(), rk(b) - rk(b).mean()
    d = math.sqrt((x ** 2).sum() * (y ** 2).sum())
    return float((x * y).sum() / d) if d > 0 else float('nan')


def concordance_by_layer(v1, v2, lay):
    """(concordant - discordant)/n_pairs, per layer. Returns per-layer values and pair counts."""
    per, cnt = {}, {}
    for L in np.unique(lay):
        i = np.where(lay == L)[0]
        c = d = 0
        for a, b in itertools.combinations(i, 2):
            s1, s2 = v1[a] - v1[b], v2[a] - v2[b]
            if s1 == 0 or s2 == 0:
                continue
            if (s1 > 0) == (s2 > 0):
                c += 1
            else:
                d += 1
        n = c + d
        if n:
            per[int(L)] = (c - d) / n
            cnt[int(L)] = n
    return per, cnt


def pooled_X(per, cnt):
    tot = sum(cnt.values())
    return sum(per[L] * cnt[L] for L in per) / tot, tot


def boot_X(per, cnt, rng, n=N_BOOT):
    Ls = list(per)
    vals = []
    for _ in range(n):
        s = rng.choice(len(Ls), len(Ls), replace=True)
        w = sum(cnt[Ls[i]] for i in s)
        vals.append(sum(per[Ls[i]] * cnt[Ls[i]] for i in s) / w)
    return float(np.mean(vals)), float(np.std(vals, ddof=1)), \
        [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'question': 'is the shape a property of the HEAD or of the (head x support) pair?'}

    # ── 1. reproduce the sign reversal rather than quote it ──
    print('  REPRODUCING THE SIGN REVERSAL  (navigator facts do not bind; its judgement does)')
    print(f"    {'model':<7}{'quantity':<12}{'rho(layer, .) I_final':<24}I_all")
    rev = {}
    for model in ('1.5b', '3b'):
        a, b = load(model, 'final'), load(model, 'all')
        if a is None or b is None:
            continue
        assert a['keys'] == b['keys'], 'cell sets differ between supports'
        row = {}
        for q in ('sd', 'mean'):
            va = a[q] if q == 'sd' else np.abs(a['mean'])
            vb = b[q] if q == 'sd' else np.abs(b['mean'])
            row[q] = {'I_final': spearman(a['layer'].astype(float), va),
                      'I_all': spearman(b['layer'].astype(float), vb)}
            lbl = 'sd_items' if q == 'sd' else '|mean|'
            print(f"    {model:<7}{lbl:<12}{row[q]['I_final']:<+24.4f}{row[q]['I_all']:+.4f}")
        # depth-tercile medians and the I_all/I_final ratio, in margin-nats
        t = np.array_split(np.argsort(a['layer'], kind='mergesort'), 3)
        row['tercile_median_sd_I_final'] = [float(np.median(a['sd'][i])) for i in t]
        row['tercile_median_sd_I_all'] = [float(np.median(b['sd'][i])) for i in t]
        row['tercile_ratio_all_over_final'] = [
            float(np.median(b['sd'][i]) / np.median(a['sd'][i])) for i in t]
        row['rho_layer_log_ratio'] = spearman(a['layer'].astype(float),
                                              np.log(b['sd'] / np.maximum(a['sd'], 1e-300)))
        rev[model] = row
        print(f"      tercile median sd_items, margin-nats:  I_final "
              + ' / '.join(f'{x:.4f}' for x in row['tercile_median_sd_I_final'])
              + '   I_all ' + ' / '.join(f'{x:.4f}' for x in row['tercile_median_sd_I_all']))
        print(f"      I_all / I_final by tercile: "
              + ' / '.join(f'{x:.2f}x' for x in row['tercile_ratio_all_over_final'])
              + f"   rho(layer, log ratio) {row['rho_layer_log_ratio']:+.4f}")
    out['sign_reversal'] = rev
    out['absorption_hypothesis_dead'] = bool(
        all(rev[m]['sd']['I_all'] < 0 < rev[m]['sd']['I_final'] for m in rev))
    print(f"    absorption hypothesis (I_all same sign, larger) -> "
          f"{'DEAD, I_all reverses' if out['absorption_hypothesis_dead'] else 'not excluded'}")

    # ── 2. positive control FIRST: two item sets, same support ──
    print('\n  POSITIVE CONTROL — I_final off0 vs I_final off400, 1.5b (same support, 2 item sets)')
    c0, c4 = load('1.5b', 'final', 'off0'), load('1.5b', 'final', 'off400')
    ctrl = None
    if c0 and c4 and c0['keys'] == c4['keys']:
        per, cnt = concordance_by_layer(c0['sd'], c4['sd'], c0['layer'])
        Xc, nc = pooled_X(per, cnt)
        mb, sb, ci = boot_X(per, cnt, rng)
        ctrl = {'X': Xc, 'n_pairs': nc, 'boot_mean': mb, 'boot_sd': sb, 'boot_ci95': ci,
                'passes': bool(Xc >= RULE['control_min_X'])}
        print(f"    X {Xc:+.4f}  over {nc} within-layer pairs   bootstrap sd {sb:.4f}  "
              f"95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]   >= {RULE['control_min_X']} -> {ctrl['passes']}")
    out['positive_control'] = ctrl

    # ── 3. the statistic ──
    print('\n  X — within-layer rank concordance of I_final against I_all')
    res = {}
    for model in ('1.5b', '3b'):
        a, b = load(model, 'final'), load(model, 'all')
        if a is None or b is None:
            continue
        per, cnt = concordance_by_layer(a['sd'], b['sd'], a['layer'])
        X, n = pooled_X(per, cnt)
        mb, sb, ci = boot_X(per, cnt, rng)
        res[model] = {'X': X, 'n_pairs': n, 'boot_mean': mb, 'boot_sd': sb, 'boot_ci95': ci,
                      'per_layer_X': per,
                      'first_third_X': float(np.mean([per[L] for L in sorted(per)[:len(per) // 3]])),
                      'last_third_X': float(np.mean([per[L] for L in sorted(per)[-(len(per) // 3):]])),
                      'passes': bool(X >= RULE['T_min_X'])}
        r = res[model]
        print(f"    {model:<6} X {X:+.4f}  over {n} within-layer pairs   bootstrap sd {sb:.4f}  "
              f"95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]")
        print(f"           first third of layers {r['first_third_X']:+.4f}   "
              f"last third {r['last_third_X']:+.4f}")
    out['X'] = res

    if ctrl is None or not ctrl['passes']:
        verdict = 'UNVERIFIED_CONTROL_FAILED'
    elif all(v['passes'] for v in res.values()):
        verdict = 'SHAPE_IS_A_HEAD_PROPERTY_DEPTH_AXIS_IS_THE_ARTIFACT'
    else:
        verdict = 'SHAPE_BELONGS_TO_HEAD_TIMES_SUPPORT'
    out['verdict'] = verdict
    print(f'\n  VERDICT  {verdict}')

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r35_head_or_support.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
