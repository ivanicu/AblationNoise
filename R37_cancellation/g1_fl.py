#!/usr/bin/env python3
"""The instrument, third rebuild: resample OUTSIDE the split loop, and a Freedman-Lane sham.

Three defects fixed, each of which was found by asking what the previous version could not do.

1. THE BOOTSTRAP RESAMPLE WAS DRAWN INSIDE THE SPLIT LOOP, so averaging splits averaged over
   resamples too and drove the reported sd toward zero without limit. The diagnosis was the
   perfection of the scaling: sd fell as 1/sqrt(n_split) to three decimals at n = 1, 2, 4, 8, 16.
   A genuine base-instance variance falls to a FLOOR, it does not vanish. With the resample moved
   OUTSIDE, the floor appears: sd 0.0412 at n_split 4, 0.0360 at 8, 0.0312 at 50.
   Fixed here: ONE resample per draw, splits inside it.

2. n_split MUST MATCH THE REPORTED ESTIMATOR. amended_cancellation.py reports crossfit_X at
   n_split = 50; the control measured at 4. Two different estimators, and the agreement between
   my 0.0311 and the correct 0.0312 was a data-dependent coincidence that will not survive 3b.

3. THE SHAM WAS BUILT ON A DIFFERENT COVARIATE GEOMETRY THAN THE ALTERNATIVE. It permuted c_h
   while leaving g = rank(m_all) in place -- and real c_h is computed from the same .all tensor as
   m_all, so permuting c_h destroyed the c_h-to-m_all relation as well, giving resid(-c_h|g) a
   different leverage in the null than in the observed arm.
   THE EVIDENCE WAS ALREADY VISIBLE: sham sd 0.0155 against recovery sd 0.0312 at n_split = 50.
   A NULL TIGHTER THAN THE ALTERNATIVE IS THE SIGNATURE OF A NULL BUILT ON DIFFERENT GEOMETRY.
   Fixed here with FREEDMAN-LANE: permute, within layer, the RESIDUALS of -c_h on rank(m_all),
   never c_h itself. The covariate relation is preserved by construction and only the residual
   pairing -- the thing under test -- is destroyed.

═══ REGISTERED BEFORE THE RUN ═══
  T = max(0.15, 2*RES), RES measured at n_split = 50 IN THIS RUN.
      0.15 is a RESTORATION: amended_cancellation.py registered T_floor = 0.15 and that
      registration predates every g1 file. 0.208 was an intruder imported from the naive
      statistic's permutation null and never had a registration row. A SHAM-DERIVED T IS NOT A
      CONSTANT OF THE STATISTIC -- the 4-split sham quantile 0.0879 becomes ~0.024 at 50 splits --
      so no threshold in this file is taken from a sham.
  INSTRUMENT_SENSITIVE_1P5B iff ALL THREE:
      Wilson-95 lower bound of P(|X| >= T) >= 0.80
      Freedman-Lane sham false-positive rate <= 0.05
      |Freedman-Lane sham mean| <= 0.02
  STOPPING CONDITION ON THE SHAM ITSELF:
      FL sham sd within +-25% of the recovery sd -> defect 3 was the whole story, and the
          within-layer c_h-permutation sham is RETRACTED REPO-WIDE.
      FL sham sd still below 0.023 -> the null remains unmatched and the cancellation test STAYS
          UNREAD regardless of anything else here.

═══ WHAT THIS FILE IS AND IS NOT ═══
It is an INSTRUMENT-SENSITIVITY measurement: does this pipeline recover a planted rho_S = 0.30 in
this model? It is NOT a claim about heads. The 12 heads per layer are the POPULATION inside a
model, not a sample from one, so resampling them would price generalisation to heads that do not
exist. Under the standing standard the SAMPLING UNIT IS THE MODEL and n = 1; generality is bought
from 495/496/497, never from a head-level SE. NO HYPOTHESIS IS READ HERE.
"""
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
LMAX, N_DRAW, N_SPLIT = 10, 2000, 50
RHO_S_TARGET = 0.30
RULE = {'T_form': 'max(0.15, 2*RES) with RES at n_split=50 in this run', 'T_floor': 0.15,
        'rho_S_target': RHO_S_TARGET, 'n_draw': N_DRAW, 'n_split': N_SPLIT,
        'sham': 'Freedman-Lane: permute resid(-c_h | rank m_all) within layer',
        'admissible_iff': 'wilson_lo >= 0.80 AND FL_fp <= 0.05 AND |FL_mean| <= 0.02',
        'sham_stopping': 'FL sd within +-25% of recovery sd -> retract the c_h-permutation sham '
                         'repo-wide; FL sd < 0.023 -> null unmatched, test stays unread'}


def rk(v):
    o = np.argsort(v, kind='mergesort')
    r = np.empty(len(v), float)
    r[o] = np.arange(len(v), dtype=float)
    return r


def sp(a, b):
    x, y = rk(a) - rk(a).mean(), rk(b) - rk(b).mean()
    d = math.sqrt((x * x).sum() * (y * y).sum())
    return float((x * y).sum() / d) if d > 0 else float('nan')


def zpool(rs):
    z = [math.atanh(r) for r in rs if r == r and abs(r) < 0.999999]
    return (float(math.tanh(sum(z) / len(z))) if z else float('nan')), len(z)


def resid(y, x):
    x = x - x.mean()
    v = (x * x).sum()
    return y - y.mean() - x * ((x * (y - y.mean())).sum() / v if v > 0 else 0.0)


def one_draw(bf, ba, lay, lam, zc, rng, fl=False, resample=True, n_split=N_SPLIT):
    """ONE bootstrap resample per draw; splits vary inside it. Injection enters .final only."""
    nb = bf.shape[1]
    bfd = bf * np.exp(-lam * zc)[:, None, None]
    idx = rng.integers(0, nb, nb) if resample else np.arange(nb)
    xs, kept = [], []
    for _ in range(n_split):
        p = rng.permutation(nb)
        A, B = idx[p[:nb // 2]], idx[p[nb // 2:]]
        fA, fB = bfd[:, A].mean(1), bfd[:, B].mean(1)
        aA, aB = ba[:, A].mean(1), ba[:, B].mean(1)
        mf = (np.sign(fA) * fB).sum(1)
        ma = (np.sign(aA) * aB).sum(1)
        ch = np.abs(aA.sum(1)) / np.maximum(np.abs(aA).sum(1), 1e-300)
        rs = []
        for L in range(LMAX):
            i = np.where(lay == L)[0]
            g = rk(ma[i])
            dr = resid((rk(mf[i]) - rk(ma[i])) / (len(i) - 1), g)
            pr = resid(-ch[i], g)
            if fl:                       # Freedman-Lane: permute the RESIDUAL, not the variable
                pr = pr[rng.permutation(len(i))]
            rs.append(sp(dr, pr))
        v, k = zpool(rs)
        xs.append(v)
        kept.append(k)
    return float(np.nanmean(xs)), float(np.mean(kept))


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - s) / d, (c + s) / d


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE}
    d = json.load(open(REPO / 'R19_crossed_position_support' / 'results' /
                       'r19_crossed_qwen2.5-1.5b.json'))
    c = d['cells']
    keys = sorted(k for k in c if k.endswith('.final'))
    lay_all = np.array([int(k[1:3]) for k in keys])
    m = lay_all < LMAX
    lay = lay_all[m]
    bf = np.stack([np.array(c[k]['base_pos'])[:, :, 0] for k in keys])[m]
    ba = np.stack([np.array(c[k.replace('.final', '.all')]['base_pos'])[:, :, 0] for k in keys])[m]
    aA0 = ba.mean(1)
    ch0 = np.abs(aA0.sum(1)) / np.maximum(np.abs(aA0).sum(1), 1e-300)
    zc = np.zeros(len(ch0))
    for L in range(LMAX):
        i = np.where(lay == L)[0]
        s = ch0[i].std(ddof=1)
        zc[i] = (ch0[i] - ch0[i].mean()) / (s if s > 0 else 1.0)
    neg = {int(L): float(((np.sign(bf.mean(1)) * bf.mean(1)).sum(1)[lay == L] < 0).mean())
           for L in range(LMAX)}
    print(f'  layers 0-{LMAX-1}, H = {len(lay)}, n_base = {bf.shape[1]}, n_split = {N_SPLIT}, '
          f'ONE resample per draw')
    print(f"  sign mix, frac(m_final < 0) per layer: "
          f"{' '.join(f'{neg[L]:.2f}' for L in range(LMAX))}   <- the plant's direction is "
          f"conditional on this")
    out['sign_mix_frac_mfinal_negative'] = neg

    lo, hi = 0.0, 6.0
    for _ in range(40):
        mid = (lo + hi) / 2
        v, _ = one_draw(bf, ba, lay, mid, zc, np.random.default_rng(SEED), resample=False,
                        n_split=N_SPLIT)
        if v < RHO_S_TARGET:
            lo = mid
        else:
            hi = mid
    lam = (lo + hi) / 2
    nl, _ = one_draw(bf, ba, lay, lam, zc, np.random.default_rng(SEED), resample=False)
    print(f'  CALIBRATION on {N_SPLIT} splits: lam {lam:.5f} -> noiseless {nl:+.4f} '
          f'(target {RHO_S_TARGET})')
    out['calibration'] = {'lam': lam, 'noiseless_X': nl}

    res = {}
    for name, lm, fl in (('recovery', lam, False), ('sham_freedman_lane', lam, True)):
        vals, kk = [], []
        for _ in range(N_DRAW):
            v, k = one_draw(bf, ba, lay, lm, zc, rng, fl=fl)
            vals.append(v)
            kk.append(k)
        vals = np.array(vals)
        res[name] = {'mean_X': float(np.nanmean(vals)), 'sd_X': float(np.nanstd(vals, ddof=1)),
                     'mean_layers_kept': float(np.mean(kk))}
        print(f"  {name:<20} mean X {res[name]['mean_X']:+.4f}  sd {res[name]['sd_X']:.4f}  "
              f"layers kept {res[name]['mean_layers_kept']:.2f}/{LMAX}")
        res[name]['_vals'] = vals
    RES = res['recovery']['sd_X']
    T = max(RULE['T_floor'], 2 * RES)
    print(f'  RES (n_split={N_SPLIT}, resample outside) {RES:.4f}  ->  T = max(0.15, 2*RES) = '
          f'{T:.4f}   (0.208 was an intruder and is not used)')
    out['RES'], out['T'] = RES, T

    for name in res:
        v = res[name].pop('_vals')
        k = int((np.abs(v) >= T).sum())
        loW, hiW = wilson(k, N_DRAW)
        res[name].update({'rate_at_T': k / N_DRAW, 'wilson95': [loW, hiW]})
        print(f"  {name:<20} P(|X| >= {T:.4f}) = {k/N_DRAW:.4f}  Wilson95 [{loW:.4f}, {hiW:.4f}]")
    out['arms'] = res

    fl_sd, rec_sd = res['sham_freedman_lane']['sd_X'], RES
    ratio = fl_sd / rec_sd
    matched = bool(0.75 <= ratio <= 1.25)
    still_tight = bool(fl_sd < 0.023)
    print(f'  SHAM GEOMETRY: FL sd {fl_sd:.4f} vs recovery sd {rec_sd:.4f}  ratio {ratio:.3f}  '
          f'-> matched(+-25%) {matched}   still-tight(<0.023) {still_tight}')
    out['sham_geometry'] = {'fl_sd': fl_sd, 'recovery_sd': rec_sd, 'ratio': ratio,
                            'matched_within_25pct': matched, 'still_tight': still_tight}

    ok = (res['recovery']['wilson95'][0] >= 0.80
          and res['sham_freedman_lane']['rate_at_T'] <= 0.05
          and abs(res['sham_freedman_lane']['mean_X']) <= 0.02)
    verdict = ('UNVERIFIED_NULL_STILL_UNMATCHED' if still_tight
               else 'INSTRUMENT_SENSITIVE_1P5B' if ok
               else 'INSTRUMENT_NOT_SENSITIVE_1P5B')
    out['verdict'] = verdict
    print(f'\n  VERDICT  {verdict}   (instrument sensitivity only — NO hypothesis is read)')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r37_g1_fl.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
