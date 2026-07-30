#!/usr/bin/env python3
"""R35's pooled verdict averaged a passing and a failing regime. This is the per-layer version.

Three debts, all owed from R35, none of them depending on any pending ruling:

  1. THE POOLED VERDICT IS UNVERIFIED AS WRITTEN. R35 registered "X < 0.30 in either model -> the
     shape is not a head property", got +0.4524 / +0.4292, and read a pass. But X by depth third is
     +0.2795 / +0.1444 early and +0.7946 / +0.7806 late -- the early third is BELOW the kill line
     the pooled number cleared. A pooled X is a weighted average of two regimes straddling the
     threshold, and its bootstrap CI is a CI on the mixture weight, not on any estimand.

  2. X MUST BE DIVIDED BY ITS OWN CEILING, PER LAYER. `sd_items` carries a head-intrinsic component
     that a total item swap cannot touch, so the instrument's own ceiling is not 1.0. The
     attenuation-corrected quantity is X / X_ctrl at the SAME layer, where X_ctrl is measured on two
     DISJOINT item sets at the SAME support. I quoted a navigator's per-layer X_ctrl without ever
     measuring it; this file measures it.

  3. THE SKIPPED-PAIR COUNT WAS NEVER EMITTED. concordance_by_layer drops any pair whose difference
     is exactly 0 on either side. That is a silent cap on float scalars parsed from JSON, and a cap
     that can only fail silently must be counted out loud.

═══ SCOPE, AND IT IS A HARD LIMIT ON HALF THIS FILE ═══
X_ctrl needs a SECOND ITEM SET at the same support. Only 1.5b has one (off400). There is no 3b
off400 on disk at the time of writing -- a GPU scan for it is queued -- so 3b HAS NO INSTRUMENT
CERTIFICATE, and its X by depth is reported as UNVERIFIED rather than as a second confirmation.
Under the standing standard a single-model certificate is not a certificate.

No thresholds are registered here: R35's registered rule already fired and is not being re-read.
This file emits the scoped quantities that rule should have been read against, and the pooled
verdict is marked UNVERIFIED in the output rather than replaced by a new one.
"""
import itertools
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
SCAN = HERE.parent / 'R29_cancellation' / 'results'
SEED = 20260730
N_BOOT = 2000


def load(model, support, off='off0'):
    f = SCAN / f'r29_scan_qwen2.5-{model}_I_{support}_{off}.json'
    if not f.exists():
        return None
    cp = json.load(open(f))['control_per_cell']
    ks = sorted(cp)
    return {'keys': ks, 'layer': np.array([int(k[1:3]) for k in ks]),
            'head': np.array([int(k[4:6]) for k in ks]),
            'sd': np.array([cp[k]['sd_items'] for k in ks])}


def concordance(v1, v2, lay):
    """Per-layer (concordant - discordant)/n_pairs, plus the SKIPPED count, emitted not hidden."""
    per, cnt, skipped = {}, {}, 0
    for L in np.unique(lay):
        i = np.where(lay == L)[0]
        c = d = 0
        for a, b in itertools.combinations(i, 2):
            s1, s2 = v1[a] - v1[b], v2[a] - v2[b]
            if s1 == 0 or s2 == 0:
                skipped += 1
                continue
            if (s1 > 0) == (s2 > 0):
                c += 1
            else:
                d += 1
        if c + d:
            per[int(L)] = (c - d) / (c + d)
            cnt[int(L)] = c + d
    return per, cnt, skipped


def boot(per, cnt, rng, n=N_BOOT):
    Ls = list(per)
    v = []
    for _ in range(n):
        s = rng.choice(len(Ls), len(Ls), replace=True)
        w = sum(cnt[Ls[i]] for i in s)
        v.append(sum(per[Ls[i]] * cnt[Ls[i]] for i in s) / w)
    return float(np.mean(v)), float(np.std(v, ddof=1)), \
        [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def thirds(per):
    Ls = sorted(per)
    k = len(Ls) // 3
    return (float(np.mean([per[L] for L in Ls[:k]])),
            float(np.mean([per[L] for L in Ls[k:2 * k]])),
            float(np.mean([per[L] for L in Ls[-k:]])))


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED,
           'debt': 'pooled X averages two regimes straddling the registered threshold; X must be '
                   'divided by its own per-layer ceiling; the skipped-pair count was never emitted',
           'pooled_verdict_status': 'UNVERIFIED — it averages a passing and a failing regime'}

    # ── the ceiling, measured, not quoted ──
    print('  X_ctrl — two DISJOINT item sets at the SAME support (the instrument\'s own ceiling)')
    c0, c4 = load('1.5b', 'final', 'off0'), load('1.5b', 'final', 'off400')
    ctrl_per = None
    if c0 and c4 and c0['keys'] == c4['keys']:
        ctrl_per, ctrl_cnt, sk_c = concordance(c0['sd'], c4['sd'], c0['layer'])
        t = thirds(ctrl_per)
        mb, sb, ci = boot(ctrl_per, ctrl_cnt, rng)
        vals = np.array([ctrl_per[L] for L in sorted(ctrl_per)])
        out['X_ctrl_1.5b'] = {'thirds': list(t), 'pooled_boot_mean': mb, 'boot_sd': sb,
                              'boot_ci95': ci, 'min': float(vals.min()), 'max': float(vals.max()),
                              'skipped_pairs': sk_c, 'n_layers': len(ctrl_per),
                              'per_layer': {str(k): v for k, v in ctrl_per.items()}}
        print(f"    1.5b thirds {t[0]:+.4f} / {t[1]:+.4f} / {t[2]:+.4f}   range "
              f"[{vals.min():+.4f}, {vals.max():+.4f}]   pooled {mb:+.4f}+-{sb:.4f}   "
              f"skipped {sk_c}")
        print(f"    -> the ceiling is {'FLAT with depth' if max(t) - min(t) < 0.15 else 'NOT flat'}"
              f" (spread {max(t) - min(t):.4f}), so a depth gradient in X is NOT the instrument")
    print('    3b: no off400 on disk -> NO CEILING, NO CERTIFICATE')

    # ── X per layer, and X / X_ctrl where a ceiling exists ──
    print('\n  X — within-layer concordance of I_final against I_all, per depth third')
    res = {}
    for model in ('1.5b', '3b'):
        a, b = load(model, 'final'), load(model, 'all')
        if a is None or b is None:
            continue
        per, cnt, sk = concordance(a['sd'], b['sd'], a['layer'])
        t = thirds(per)
        mb, sb, ci = boot(per, cnt, rng)
        row = {'thirds': list(t), 'pooled_boot_mean': mb, 'boot_sd': sb, 'boot_ci95': ci,
               'skipped_pairs': sk, 'n_layers': len(per),
               'per_layer': {str(k): v for k, v in per.items()}}
        # per-third bootstrap, which R35 never did for the thirds it quoted
        Ls = sorted(per)
        k3 = len(Ls) // 3
        for name, sub in (('first', Ls[:k3]), ('last', Ls[-k3:])):
            p2 = {L: per[L] for L in sub}
            c2 = {L: cnt[L] for L in sub}
            m2, s2, ci2 = boot(p2, c2, rng)
            row[f'{name}_third_boot'] = {'mean': m2, 'sd': s2, 'ci95': ci2}
        if ctrl_per is not None and model == '1.5b':
            rat = {L: per[L] / ctrl_per[L] for L in per if L in ctrl_per and ctrl_per[L] != 0}
            row['X_over_Xctrl_thirds'] = list(thirds(rat))
            row['certificate'] = 'attenuation-corrected against a measured per-layer ceiling'
        else:
            row['certificate'] = 'NONE — no second item set for this model; UNVERIFIED'
        res[model] = row
        print(f"    {model:<5} thirds {t[0]:+.4f} / {t[1]:+.4f} / {t[2]:+.4f}   "
              f"first-third CI [{row['first_third_boot']['ci95'][0]:+.4f}, "
              f"{row['first_third_boot']['ci95'][1]:+.4f}]   "
              f"last-third CI [{row['last_third_boot']['ci95'][0]:+.4f}, "
              f"{row['last_third_boot']['ci95'][1]:+.4f}]   skipped {sk}")
        if 'X_over_Xctrl_thirds' in row:
            r = row['X_over_Xctrl_thirds']
            print(f"          X / X_ctrl by third: {r[0]:+.4f} / {r[1]:+.4f} / {r[2]:+.4f}   "
                  f"<- attenuation-corrected")
        else:
            print(f"          {row['certificate']}")
    out['X'] = res

    # what the registered rule WOULD have said, read per regime instead of pooled
    print('\n  THE REGISTERED RULE (X < 0.30 -> not a head property), READ PER REGIME:')
    for m, r in res.items():
        f_, _, l_ = r['thirds']
        cert = 'certified' if 'X_over_Xctrl_thirds' in r else 'UNVERIFIED (no ceiling)'
        print(f"    {m:<5} early third {f_:+.4f} -> "
              f"{'FAILS the 0.30 line' if f_ < 0.30 else 'clears it'}   "
              f"late third {l_:+.4f} -> {'FAILS' if l_ < 0.30 else 'clears it'}   [{cert}]")
    out['read_per_regime'] = {m: {'early': r['thirds'][0], 'late': r['thirds'][2],
                                  'early_fails_0p30': bool(r['thirds'][0] < 0.30),
                                  'late_fails_0p30': bool(r['thirds'][2] < 0.30),
                                  'certificate': r['certificate']} for m, r in res.items()}

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r35_per_layer_attenuation.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
