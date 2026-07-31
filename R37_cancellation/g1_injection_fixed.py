#!/usr/bin/env python3
"""The positive control, with the injection ROUTED SOMEWHERE THE STATISTIC CAN SEE IT. Zero forwards.

g1_pipeline_power.py fixed one defect and introduced two. Both are recorded there; both are fixed
here, and the fix follows from stating the statistic's own algebra before touching any data.

    X = rho( resid(Delta r | rank m_all) , resid(-c_h | rank m_all) )
    Delta r = rank_L(m_final) - rank_L(m_all)
    c_h     = |sum_t e_t| / sum_t |e_t|   computed from the .all tensor

DEFECT 1, FIXED: I INJECTED THROUGH m_all, WHICH THE STATISTIC PARTIALS OUT BY CONSTRUCTION.
Perturbing the .all tensor moves rank(m_all) -- and rank(m_all) is exactly the covariate being
residualised away. It also moves c_h, because c_h is recomputed from the same perturbed tensor, so
the perturbation partly cancelled its own effect. The binary search saturated at lam = 4.0 for a
noiseless coupling of only +0.1159 against a target of 0.30, which is what a blind route looks like.
    NOW: the injection enters through the .final tensor, multiplicatively, as exp(-lam * z_c).
    It moves rank(m_final) -> Delta r, which the partialling does NOT remove, and it leaves the
    .all tensor untouched so c_h and the covariate are both exactly as measured.
    Sign: high-c_h heads get SMALLER m_final, so Delta r falls with c_h, so rho(Delta r, -c_h) > 0
    -- the registered direction.

DEFECT 2, FIXED: A ZERO-GAIN ARM IS THE OBSERVED, NOT A SHAM. lam = 0 leaves the data untouched, so
that arm measured the real data (mean X +0.1600, which is R37 v2's +0.1672) and called it a
false-positive rate.
    NOW: the sham PERMUTES c_h WITHIN LAYER. Both marginals survive exactly -- the same 12 c_h
    values and the same 12 Delta r values in each layer -- and only the pairing is destroyed, which
    is the thing under test.

═══ REGISTERED BEFORE THE RUN ═══
  target      rho_S = 0.30 on the SPEARMAN scale, calibrated noiselessly by binary search on lam
  recovery    P(|X| >= T) over N draws, each resampling the 64 base instances and running the FULL
              estimator: split-half sign, cross-fit magnitude, ranking, partialling, Fisher-z
  sham        the same pipeline with c_h permuted within layer; this is the false-positive rate
  T           0.208, carried over unchanged
  N           2000 -- at a recovery near 0.78 the binomial SE at n = 200 is 0.029, which cannot
              resolve 0.767 from 0.80, so the previous control could not have answered its own
              question even had it been routed correctly
  ADMISSIBLE on 1.5b alone IFF the LOWER Wilson 95% bound of recovery >= 0.80 AND sham <= 0.05.
  This file reads NO hypothesis. It characterises the instrument only.
"""
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
LMAX, N_POWER, N_SPLIT = 10, 2000, 4
T_REG, RHO_S_TARGET = 0.208, 0.30
RULE = {'T': T_REG, 'rho_S_target': RHO_S_TARGET, 'n_power': N_POWER,
        'injection_route': '.final tensor, exp(-lam*z_c) — NOT partialled out',
        'sham': 'permute c_h WITHIN layer — both marginals preserved, only the pairing destroyed',
        'admissible_iff': 'wilson_lo >= 0.80 AND sham <= 0.05'}


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
    return float(math.tanh(sum(z) / len(z))) if z else float('nan')


def resid(y, x):
    x = x - x.mean()
    v = (x * x).sum()
    return y - y.mean() - x * ((x * (y - y.mean())).sum() / v if v > 0 else 0.0)


def X_of(mf, ma, ch, lay, permute_c=None):
    rs = []
    for L in range(LMAX):
        i = np.where(lay == L)[0]
        dr = (rk(mf[i]) - rk(ma[i])) / (len(i) - 1)
        cc = ch[i][permute_c[L]] if permute_c is not None else ch[i]
        g = rk(ma[i])
        rs.append(sp(resid(dr, g), resid(-cc, g)))
    return zpool(rs)


def run_pipeline(bf, ba, lay, lam, zc, rng, resample=True, sham=False, n_split=N_SPLIT):
    """The REAL estimator. Injection enters .final only; .all is untouched."""
    nb = bf.shape[1]
    bfd = bf * np.exp(-lam * zc)[:, None, None]
    xs = []
    for _ in range(n_split):
        idx = rng.integers(0, nb, nb) if resample else np.arange(nb)
        p = rng.permutation(nb)
        A, B = idx[p[:nb // 2]], idx[p[nb // 2:]]
        fA, fB = bfd[:, A].mean(1), bfd[:, B].mean(1)
        aA, aB = ba[:, A].mean(1), ba[:, B].mean(1)
        mf = (np.sign(fA) * fB).sum(1)
        ma = (np.sign(aA) * aB).sum(1)
        ch = np.abs(aA.sum(1)) / np.maximum(np.abs(aA).sum(1), 1e-300)
        pc = None
        if sham:
            pc = {L: rng.permutation(int((lay == L).sum())) for L in range(LMAX)}
        xs.append(X_of(mf, ma, ch, lay, pc))
    return float(np.nanmean(xs))


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
    print(f'  layers 0-{LMAX-1}, H = {len(lay)}, base instances n = {bf.shape[1]}')
    print('  injection route: .final tensor only — the partialling is on rank(m_all), which the '
          'injection now does NOT touch')

    lo, hi = 0.0, 6.0
    for _ in range(44):
        mid = (lo + hi) / 2
        v = run_pipeline(bf, ba, lay, mid, zc, np.random.default_rng(SEED),
                         resample=False, n_split=1)
        if v < RHO_S_TARGET:
            lo = mid
        else:
            hi = mid
    lam = (lo + hi) / 2
    nl = run_pipeline(bf, ba, lay, lam, zc, np.random.default_rng(SEED), resample=False, n_split=1)
    reached = abs(nl - RHO_S_TARGET) < 0.02
    print(f'  CALIBRATION: lam {lam:.5f} -> noiseless coupling {nl:+.4f} (target {RHO_S_TARGET})   '
          f"reached: {reached}{'' if reached else '  <- STILL SATURATING, route still blind'}")
    out['calibration'] = {'lam': lam, 'noiseless_X': nl, 'target': RHO_S_TARGET,
                          'target_reached': bool(reached)}

    res = {}
    for name, lm, sh in (('recovery', lam, False), ('sham', lam, True)):
        xs = np.array([run_pipeline(bf, ba, lay, lm, zc, rng, sham=sh) for _ in range(N_POWER)])
        k = int((np.abs(xs) >= T_REG).sum())
        loW, hiW = wilson(k, N_POWER)
        res[name] = {'rate': k / N_POWER, 'wilson95': [loW, hiW],
                     'mean_X': float(np.nanmean(xs)), 'sd_X': float(np.nanstd(xs, ddof=1))}
        print(f"  {name.upper():<9} mean X {res[name]['mean_X']:+.4f} sd {res[name]['sd_X']:.4f}   "
              f"P(|X| >= {T_REG}) = {k/N_POWER:.4f}   Wilson95 [{loW:.4f}, {hiW:.4f}]")
    out['arms'] = res
    att = res['recovery']['mean_X'] / nl if nl else float('nan')
    print(f"  ATTENUATION through the full pipeline: {att:.4f}  "
          f"(noiseless {nl:+.4f} -> routed {res['recovery']['mean_X']:+.4f})")
    out['measured_attenuation'] = att

    ok_sham = res['sham']['rate'] <= 0.05
    ok_rec = res['recovery']['wilson95'][0] >= 0.80
    verdict = ('UNVERIFIED_INJECTION_STILL_BLIND' if not reached
               else 'UNVERIFIED_SHAM_TOO_HOT' if not ok_sham
               else 'ADMISSIBLE_ON_1P5B_ALONE' if ok_rec
               else 'INADMISSIBLE_ON_ONE_MODEL_MEASURED')
    out['verdict'] = verdict
    print(f'\n  VERDICT  {verdict}')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r37_g1_injection_fixed.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
