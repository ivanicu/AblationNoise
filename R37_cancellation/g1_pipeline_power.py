#!/usr/bin/env python3
"""INSTRUMENT CHARACTERISATION, not a hypothesis test. Zero forwards, no verdict is read.

The admissibility number that stopped the last run -- power 0.767 at T = 0.208, rho = 0.30 -- rests
on two things that turned out to be unmeasured or wrong:

  1. MY POSITIVE CONTROL NEVER TOUCHED THE DATA. amended_cancellation.py's G1 synthesised
     y = rho*z + sqrt(1-rho^2)*eps and correlated it with -c_h directly. It never called
     crossfit_X, never touched bf/ba, never resampled a base instance. So it measured the power of
     a NOISELESS rho and is structurally incapable of detecting the attenuation the whole
     admissibility exercise is about. It would have reported ~1.00 recovery and stamped the
     instrument ADMISSIBLE while the real estimator sits near 0.76. A CHECK THAT CANNOT FAIL --
     the second one in this file family, and this time inside the fix for the first.

  2. THE ATTENUATION MODEL WAS WRONG TWICE, IN OPPOSITE DIRECTIONS, AND SURVIVED BY ACCIDENT.
     X = rho(signed Delta r, -c_h) has BOTH arguments measured, so classical attenuation is
     sqrt(r_xx * r_yy), not sqrt(r_xx) -- and c_h's own reliability was never measured. Separately,
     r_ss = 0.8719 is a SPLIT-HALF reliability while the estimator uses all 64 instances, so the
     Spearman-Brown value 0.9316 is the right one. sqrt(0.8719) = 0.9338 against r_full = 0.9316:
     two errors of ~3.5% cancelling. The number was right for the wrong reason.

  3. AND THE INJECTION TARGET WAS ON THE WRONG SCALE. For bivariate normal,
     rho_S = (6/pi)*asin(rho_P/2), so injecting rho_P = 0.30 delivers rho_S = 0.2876 -- 4.1% less
     than registered, on a cell whose margin was 0.033.

So this file measures the instrument instead of modelling it.

═══ WHAT IT DOES ═══
  A  CALIBRATE THE INJECTION NOISELESSLY. Perturb each head's .all magnitude multiplicatively by
     exp(lam * z_c), z_c = the within-layer standardised c_h. Binary-search lam so that on the
     FULL-64, noise-free arrays the resulting rho(Delta r, -c_h) equals the target on the SPEARMAN
     scale. The coupling is therefore defined by what it does, not by a Gaussian parameter.
  B  MEASURE IT THROUGH THE WHOLE PIPELINE. Apply the SAME multiplicative perturbation to the
     per-instance tensor -- so every bit of measurement noise is preserved -- then resample the 64
     base instances and run the real crossfit_X. The gap between A and B IS the attenuation, and it
     is measured rather than assumed.
  C  SHAM ARM at lam = 0 through the identical pipeline. A recovery rate without its false-positive
     twin is not a power measurement.
  D  MEASURE rho_bar_z, the mean off-diagonal correlation of the 10 per-layer Fisher-z values over
     bootstrap replicates, and emit L_eff = L / (1 + (L-1)*rho_bar_z). The layers are NOT
     independent strata -- they share the same 64 base instances -- so every pooled SE in this
     project has been assuming something known to be false. This number retires that.

═══ REGISTERED BEFORE THE RUN ═══
  ADMISSIBLE on 1.5b alone IFF the LOWER Wilson 95% bound of pipeline-routed recovery at
  rho_S = 0.30, T = 0.208, is >= 0.80 AND the sham arm's false-positive rate is <= 0.05.
    lower bound >= 0.80 -> the parametric "underpowered" verdict is OVERTURNED; the cancellation
                           test may run on 1.5b as registered, and job 495 becomes confirmation
                           rather than a precondition.
    lower bound <  0.80 -> 1.5b-only is INADMISSIBLE, confirmed empirically rather than modelled;
                           the test waits for 495 and is re-registered on the pooled geometry WITH
                           A POOLED NULL RECALIBRATING T (0.208 was calibrated 1.5b-only).
    sham > 0.05         -> UNVERIFIED_INSTRUMENT, and neither branch may be read.
  N >= 2000 draws: at recovery ~0.78 the binomial SE at n=200 is 0.029, which cannot resolve 0.767
  from 0.80 -- the previous control's sample size could not have answered its own question.
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
LMAX, N_POWER, N_SPLIT, N_RHOZ = 10, 2000, 4, 400
T_REG = 0.208
RHO_S_TARGET = 0.30
RULE = {'T': T_REG, 'rho_S_target': RHO_S_TARGET, 'n_power': N_POWER,
        'admissible_iff': 'wilson_lo >= 0.80 AND sham <= 0.05',
        'rho_P_equivalent': 2 * math.sin(math.pi * RHO_S_TARGET / 6)}
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


def zpool(rs):
    z = [math.atanh(r) for r in rs if r == r and abs(r) < 0.999999]
    return float(math.tanh(sum(z) / len(z))) if z else float('nan')


def resid(y, x):
    x = x - x.mean()
    v = (x * x).sum()
    return y - y.mean() - x * ((x * (y - y.mean())).sum() / v if v > 0 else 0.0)


def zc_within(ch, lay):
    z = np.zeros(len(ch))
    for L in range(LMAX):
        i = np.where(lay == L)[0]
        s = ch[i].std(ddof=1)
        z[i] = (ch[i] - ch[i].mean()) / (s if s > 0 else 1.0)
    return z


def X_from(fA, fB, aA, aB, ch, lay, per_layer=False):
    mf = (np.sign(fA) * fB).sum(1)
    ma = (np.sign(aA) * aB).sum(1)
    rs = []
    for L in range(LMAX):
        i = np.where(lay == L)[0]
        dr = (rk(mf[i]) - rk(ma[i])) / (len(i) - 1)
        g = rk(ma[i])
        rs.append(sp(resid(dr, g), resid(-ch[i], g)))
    return rs if per_layer else zpool(rs)


def pipeline_X(bf, ba, lay, gain, rng, n_split=N_SPLIT, resample=True):
    """The REAL estimator, on data doctored by exp(gain) per head. Noise fully preserved."""
    nb = bf.shape[1]
    g = gain[:, None, None]
    bfd, bad = bf, ba * np.exp(g)
    xs = []
    for _ in range(n_split):
        idx = rng.integers(0, nb, nb) if resample else np.arange(nb)
        p = rng.permutation(nb)
        A, B = idx[p[:nb // 2]], idx[p[nb // 2:]]
        aA = bad[:, A].mean(1)
        ch = np.abs(aA.sum(1)) / np.maximum(np.abs(aA).sum(1), 1e-300)
        xs.append(X_from(bfd[:, A].mean(1), bfd[:, B].mean(1), aA, bad[:, B].mean(1), ch, lay))
    return float(np.nanmean(xs))


def noiseless_X(bf, ba, lay, lam, zc):
    """Full-64, no resampling, no split: the coupling the injection DEFINES."""
    bad = ba * np.exp(lam * zc)[:, None, None]
    aA = bad.mean(1)
    ch = np.abs(aA.sum(1)) / np.maximum(np.abs(aA).sum(1), 1e-300)
    return X_from(bf.mean(1), bf.mean(1), aA, aA, ch, lay)


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
    nb = bf.shape[1]
    ch0 = np.abs(ba.mean(1).sum(1)) / np.maximum(np.abs(ba.mean(1)).sum(1), 1e-300)
    zc = zc_within(ch0, lay)
    print(f'  layers 0-{LMAX-1}, H = {len(lay)}, base instances n = {nb}')
    print(f"  scale note: rho_S {RHO_S_TARGET} corresponds to rho_P "
          f"{RULE['rho_P_equivalent']:.4f} for bivariate normal — the previous control injected "
          f"rho_P and read rho_S, delivering {6/math.pi*math.asin(0.30/2):.4f}")

    # ── A: calibrate lam so the NOISELESS coupling equals the target ──
    lo, hi = 0.0, 4.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if noiseless_X(bf, ba, lay, mid, zc) < RHO_S_TARGET:
            lo = mid
        else:
            hi = mid
    lam = (lo + hi) / 2
    nl = noiseless_X(bf, ba, lay, lam, zc)
    print(f'  A CALIBRATION: lam {lam:.5f} gives a NOISELESS coupling of {nl:+.4f} '
          f'(target {RHO_S_TARGET})')
    out['calibration'] = {'lam': lam, 'noiseless_X': nl, 'target': RHO_S_TARGET}

    # ── B/C: recovery and sham, both THROUGH the real pipeline ──
    res = {}
    for name, g in (('recovery', lam * zc), ('sham', np.zeros(len(zc)))):
        xs = np.array([pipeline_X(bf, ba, lay, g, rng) for _ in range(N_POWER)])
        k = int((np.abs(xs) >= T_REG).sum())
        loW, hiW = wilson(k, N_POWER)
        res[name] = {'rate': k / N_POWER, 'wilson95': [loW, hiW], 'n': N_POWER,
                     'mean_X': float(np.nanmean(xs)), 'sd_X': float(np.nanstd(xs, ddof=1))}
        print(f"  {name.upper():<9} through the FULL pipeline: mean X {res[name]['mean_X']:+.4f} "
              f"sd {res[name]['sd_X']:.4f}   P(|X| >= {T_REG}) = {k/N_POWER:.4f}  "
              f"Wilson95 [{loW:.4f}, {hiW:.4f}]")
    out['arms'] = res
    att = res['recovery']['mean_X'] / nl if nl != 0 else float('nan')
    print(f'  MEASURED ATTENUATION through the pipeline: {att:.4f} '
          f'(noiseless {nl:+.4f} -> routed {res["recovery"]["mean_X"]:+.4f})')
    out['measured_attenuation'] = att

    # ── D: the layer dependence every pooled SE in this project has assumed away ──
    Z = []
    for _ in range(N_RHOZ):
        idx = rng.integers(0, nb, nb)
        p = rng.permutation(nb)
        A, B = idx[p[:nb // 2]], idx[p[nb // 2:]]
        aA = ba[:, A].mean(1)
        chb = np.abs(aA.sum(1)) / np.maximum(np.abs(aA).sum(1), 1e-300)
        rs = X_from(bf[:, A].mean(1), bf[:, B].mean(1), aA, ba[:, B].mean(1), chb, lay,
                    per_layer=True)
        Z.append([math.atanh(r) if r == r and abs(r) < 0.999999 else 0.0 for r in rs])
    Z = np.array(Z)
    C = np.corrcoef(Z.T)
    off = C[~np.eye(LMAX, dtype=bool)]
    rz = float(np.nanmean(off))
    leff = LMAX / (1 + (LMAX - 1) * rz)
    se_naive = 1 / math.sqrt(12 - 3) / math.sqrt(LMAX)
    se_corr = math.sqrt(1.06 / (12 - 3)) / math.sqrt(leff)
    print(f'  D LAYER DEPENDENCE: mean off-diagonal corr of per-layer Fisher-z = {rz:+.4f}  '
          f'-> L_eff {leff:.2f} of {LMAX}')
    print(f'    SE naive 1/sqrt(n-3)/sqrt(L) {se_naive:.4f}  ->  corrected '
          f'sqrt(1.06/(n-3))/sqrt(L_eff) {se_corr:.4f}   ({se_corr/se_naive:.2f}x)')
    out['layer_dependence'] = {'rho_bar_z': rz, 'L_eff': leff, 'se_naive': se_naive,
                               'se_corrected': se_corr, 'ratio': se_corr / se_naive}

    adm = bool(res['recovery']['wilson95'][0] >= 0.80 and res['sham']['rate'] <= 0.05)
    verdict = ('UNVERIFIED_INSTRUMENT' if res['sham']['rate'] > 0.05
               else 'ADMISSIBLE_ON_1P5B_ALONE' if adm else 'INADMISSIBLE_ON_ONE_MODEL_MEASURED')
    out['verdict'] = verdict
    print(f'\n  VERDICT  {verdict}')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r37_g1_pipeline_power.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
