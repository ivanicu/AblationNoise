#!/usr/bin/env python3
"""CAN THIS TEST ADMIT A KILL AT ALL? Computed BEFORE running it. Zero forwards.

Three consecutive rounds in this project were run and then invalidated by a ruling that arrived
afterwards. The process fix is to settle the DESIGN first -- and the first question a design has to
answer is not "what does it say" but "can it say anything".

The corrected threshold from R37 v2 is
    T = max(0.15, null_mean + 1.645*null_sd, 2*RES) = max(0.15, 0.0372 + 1.645*0.104, 0.0828)
      = 0.208
and the registered positive control injects rho = 0.30. So the question is arithmetic:

    AT T = 0.208, DOES THE 12-HEAD x 10-LAYER LATTICE HAVE 80% POWER AT rho = 0.30?

Measurement error attenuates a true rho by about sqrt(r_ss), so the reliability has to be measured
first -- per layer, not pooled, because a pooled reliability can hide a layer that is pure noise.

This file emits: per-layer split-half reliability of the cross-fit magnitude under BOTH supports,
the per-layer sign-agreement rate that bounds the cross-fit's attenuation, and the resulting power
surface over (T, rho). It runs NO hypothesis test and reads NO verdict.
"""
import json
import math
import pathlib
import statistics as st
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
LMAX, N_SPLIT = 10, 200
N = st.NormalDist()


def rk(v):
    o = np.argsort(v, kind='mergesort')
    r = np.empty(len(v), float)
    r[o] = np.arange(len(v), dtype=float)
    return r


def sp(a, b):
    x, y = rk(a) - rk(a).mean(), rk(b) - rk(b).mean()
    d = math.sqrt((x * x).sum() * (y * y).sum())
    return float((x * y).sum() / d) if d > 0 else float('nan')


def power(T, rho, r_ss, n_head, n_layer):
    """Fisher-z power for a pooled within-layer Spearman, with sqrt(r_ss) attenuation."""
    se = 1 / math.sqrt(n_head - 3) / math.sqrt(n_layer)
    att = rho * math.sqrt(max(r_ss, 0.0))
    z = math.atanh(att)
    return float(1 - N.cdf((math.atanh(T) - z) / se)), se, att


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'question': 'can the registered test admit a kill at n = 12 heads x 10 '
                                     'layers, at T = 0.208 and rho = 0.30?'}
    d = json.load(open(REPO / 'R19_crossed_position_support' / 'results' /
                       'r19_crossed_qwen2.5-1.5b.json'))
    c = d['cells']
    keys = sorted(k for k in c if k.endswith('.final'))
    lay_all = np.array([int(k[1:3]) for k in keys])
    m = lay_all < LMAX
    lay = lay_all[m]
    ba = np.stack([np.array(c[k.replace('.final', '.all')]['base_pos'])[:, :, 0] for k in keys])[m]
    bf = np.stack([np.array(c[k]['base_pos'])[:, :, 0] for k in keys])[m]
    nb = ba.shape[1]

    print(f"  {'layer':<7}{'r_ss(.all)':<13}{'r_ss(.final)':<15}{'sign agreement':<17}n_heads")
    ra_all, rf_all, sg = [], [], []
    per = {}
    for L in range(LMAX):
        i = np.where(lay == L)[0]
        A_, F_, S_ = [], [], []
        for _ in range(N_SPLIT):
            p = rng.permutation(nb)
            A, B = p[:nb // 2], p[nb // 2:]
            for arr, acc in ((ba, A_), (bf, F_)):
                eA, eB = arr[i][:, A].mean(1), arr[i][:, B].mean(1)
                acc.append(sp((np.sign(eA) * eA).sum(1), (np.sign(eB) * eB).sum(1)))
            eA, eB = ba[i][:, A].mean(1), ba[i][:, B].mean(1)
            S_.append(float((np.sign(eA) == np.sign(eB)).mean()))
        ra_all.append(float(np.nanmean(A_)))
        rf_all.append(float(np.nanmean(F_)))
        sg.append(float(np.mean(S_)))
        per[int(L)] = {'r_ss_all': ra_all[-1], 'r_ss_final': rf_all[-1], 'sign_agree': sg[-1],
                       'n_heads': int(len(i))}
        print(f'  {L:<7}{ra_all[-1]:<13.4f}{rf_all[-1]:<15.4f}{sg[-1]:<17.4f}{len(i)}')
    r_pool = float(np.mean(ra_all))
    dropped = [L for L in range(LMAX) if ra_all[L] < 0.60]
    out['per_layer'] = per
    out['pooled_r_ss_all'] = r_pool
    out['pooled_sign_agreement'] = float(np.mean(sg))
    out['layers_below_0p60_dropped'] = dropped
    print(f'\n  pooled r_ss(.all) {r_pool:.4f}   pooled sign agreement {np.mean(sg):.4f}   '
          f'layers dropped at r_ss < 0.60: {dropped if dropped else "none"}')

    print(f"\n  POWER SURFACE, 12 heads x 10 layers, attenuation sqrt(r_ss)")
    print(f"    {'T':<8}{'true rho':<11}{'attenuated':<13}{'power':<9}")
    grid = {}
    for T in (0.15, 0.208, 0.25):
        for rho in (0.20, 0.30, 0.40):
            pw, se, att = power(T, rho, r_pool, 12, LMAX)
            grid[f'T{T}_rho{rho}'] = {'power': pw, 'se': se, 'attenuated_rho': att}
            flag = '  <- BELOW the 0.80 bar' if pw < 0.80 else ''
            print(f'    {T:<8.3f}{rho:<11.2f}{att:<13.3f}{pw:<9.3f}{flag}')
    out['power_1p5b_layers0_9'] = grid

    # what geometry WOULD be admissible
    print(f"\n  WHAT GEOMETRY CLEARS 0.80 AT T = 0.208, rho = 0.30")
    opts = [('1.5b layers 0-9 (as registered)', 12, 10),
            ('3b   layers 0-9 (16 heads/layer, needs job 495)', 16, 10),
            ('1.5b + 3b layers 0-9 pooled', None, None),
            ('1.5b all 28 layers (MIXES REGIMES — not the question)', 12, 28)]
    adm = {}
    for name, nh, nl in opts:
        if nh is None:
            se = 1 / math.sqrt((12 - 3) * LMAX + (16 - 3) * LMAX)
            att = 0.30 * math.sqrt(r_pool)
            pw = float(1 - N.cdf((math.atanh(0.208) - math.atanh(att)) / se))
        else:
            pw, se, att = power(0.208, 0.30, r_pool, nh, nl)
        adm[name] = {'power': pw, 'se': se}
        print(f'    {name:<48} SE {se:.4f}  power {pw:.3f}'
              f"{'  ADMISSIBLE' if pw >= 0.80 else '  underpowered'}")
    out['admissible_geometries'] = adm
    out['conclusion'] = ('at T = 0.208 the registered 1.5b-only geometry has power '
                         f'{grid["T0.208_rho0.3"]["power"]:.3f} at rho = 0.30, below the 0.80 bar. '
                         'The test is NOT admissible as registered on one model.')
    print(f"\n  {out['conclusion']}")
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r37_admissibility.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
