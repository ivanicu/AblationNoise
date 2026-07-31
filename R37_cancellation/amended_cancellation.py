#!/usr/bin/env python3
"""Cancellation as the generator of R35's support-dependent reordering. AMENDED. Zero forwards.

The first attempt (support_reordering.py) returned a kill on both legs and I did not read it,
because it had NO POSITIVE CONTROL -- and the registered asymmetry makes a NEGATIVE the cheap
outcome, which is exactly the condition under which an underpowered instrument fabricates one.
Its verdict is annotated UNVERIFIED_NO_POSITIVE_CONTROL. This file is the amended registration.

═══ WHAT CHANGED, AND WHY EACH ONE MATTERS ═══

1. THE OUTCOME IS NOW SIGNED. Under the no-mechanism null E[|Delta r|] > 0, and its value is set by
   the NOISE MAGNITUDE -- which itself covaries with c_h. So |Delta r| has a null centre that MOVES
   WITH THE PREDICTOR and can be nonzero with zero mechanism. Signed Delta r has null mean exactly 0
   under exchangeability. Direction registered a priori: cancellation means restricting the support
   REMOVES the cancellation, so high-cancellation (low c_h) heads should RISE under .final, i.e.
   rho(Delta r_h, -c_h) > 0.

2. THE MAGNITUDE IS CROSS-FIT, TO KILL RECTIFICATION BIAS. sum_t|e_hat_t| is a POSITIVELY BIASED
   estimator of sum_t|e_t|, and the bias is maximal exactly where |e_t|/sigma -> 0 -- which is the
   definition of a high-cancellation head. Since .final effects are 2-10x smaller than .all, the two
   conditions carry DIFFERENT rectification bias whose difference is monotone in c_h. That produces
   a nonzero X from noise alone, IN THE REGISTERED DIRECTION. The fix takes the SIGN from one half
   of the base instances and the VALUE from the other:
       m_h = sum_t sign(e_hat_t^A) * e_hat_t^B
   Under a fixed true sign pattern this is unbiased, because the sign carries no magnitude.
   The naive sum_t|e_hat_t| is retained as a labelled SECONDARY.

3. c_h COMES FROM HALF A, THE RANKS FROM HALF B, so predictor and outcome do not share estimation
   noise. >= 50 random 32/32 splits, averaged.

4. T = max(0.15, 2*RES), and RES is the BASE-INSTANCE BOOTSTRAP SD -- never a propagated sem.
   Spearman's z-variance is 1.06/(n-3) not 1/(n-3), and the 10 layers are NOT independent strata
   (they share the same 64 base instances), so any parametric pooled SE is wrong in an unknown
   direction. Fisher-z is used ONLY as the pooling transform, never as a variance model.

═══ FOUR GATES, ALL REGISTERED BEFORE THE RUN, IN THIS ORDER ═══
  G0  RELIABILITY, PRINTED FIRST. Within-layer split-half reliability of m_h, Spearman-Brown
      corrected. If r_yy is far below 0.7 then Delta r is mostly noise, X is attenuated toward 0,
      and any negative is MANUFACTURED rather than measured.
  G1  POSITIVE CONTROL, MANDATORY BEFORE ANY KILL. Inject a known coupling of rho = 0.30 between
      -c_h and a synthetic Delta r on the SAME 12 x 10 lattice and the REAL c_h vector, 200 draws.
      Recovery = fraction with |X| >= T. Must reach >= 0.80.
      FAIL -> UNVERIFIED_INSTRUMENT_UNDERPOWERED. No work is removed. This is R36's failure mode,
      and I have now hit it twice, so it gates everything below.
  G2  SHAM. Permute the position index INDEPENDENTLY WITHIN EACH BASE INSTANCE, then recompute the
      whole pipeline. This preserves every per-instance magnitude and all noise, and flattens the
      instance-mean profile -- so true position structure is gone while rectification is intact.
      (Unlike the position-LABEL permutation of R36, which was exactly invariant for every
      dispersion statistic, this one DOES move the instance-mean pos vector.)
      |X_sham| >= 0.05 -> UNVERIFIED_RECTIFICATION_CONFOUND, whatever X is.
  G3  THE TEST. |X| < T or the 95% BCa CI covers 0 -> CANCELLATION DEAD.

═══ REGISTERED ASYMMETRY, unchanged and stated before the run ═══
A NEGATIVE is a legitimate ONE-MODEL result because it REMOVES work and cannot be inflated into a
claim. A POSITIVE is NOT a result; it earns exactly one thing, the 3b crossed scan.
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
LMAX, N_SPLIT, N_BOOT, N_POWER = 10, 50, 1000, 200
RULE = {'T_floor': 0.15, 'T_form': 'max(0.15, 2*RES)', 'n_splits': N_SPLIT, 'n_boot': N_BOOT,
        'G1_target_rho': 0.30, 'G1_min_recovery': 0.80, 'G2_max_sham': 0.05,
        'G0_reliability_warn_below': 0.70,
        'direction': 'rho(signed Delta r, -c_h) > 0',
        'asymmetry': 'NEGATIVE is a legitimate one-model result; POSITIVE is not a result'}
N = st.NormalDist()


def rk(v):
    o = np.argsort(v, kind='mergesort')
    r = np.empty(len(v), float)
    r[o] = np.arange(len(v), dtype=float)
    return r


def spear(a, b):
    x, y = rk(a) - rk(a).mean(), rk(b) - rk(b).mean()
    d = math.sqrt((x * x).sum() * (y * y).sum())
    return float((x * y).sum() / d) if d > 0 else float('nan')


def zpool(rs):
    z = [0.5 * math.log((1 + r) / (1 - r)) for r in rs if r == r and abs(r) < 0.999999]
    if not z:
        return float('nan')
    zb = sum(z) / len(z)
    return float(math.tanh(zb))


def resid(y, x):
    x = x - x.mean()
    v = (x * x).sum()
    return y - y.mean() - x * ((x * (y - y.mean())).sum() / v if v > 0 else 0.0)


def crossfit_X(bf, ba, lay, rng, partial, n_split=N_SPLIT, sham=False):
    """Sign from half A, value from half B, c_h from half A. Averaged over n_split draws."""
    nb = bf.shape[1]
    xs = []
    for _ in range(n_split):
        p = rng.permutation(nb)
        A, B = p[:nb // 2], p[nb // 2:]
        f, a = bf, ba
        if sham:                       # permute position index INDEPENDENTLY per base instance
            f = np.stack([np.stack([r[rng.permutation(r.shape[-1])] for r in h]) for h in bf])
            a = np.stack([np.stack([r[rng.permutation(r.shape[-1])] for r in h]) for h in ba])
        fA, fB = f[:, A].mean(1), f[:, B].mean(1)
        aA, aB = a[:, A].mean(1), a[:, B].mean(1)
        mf = (np.sign(fA) * fB).sum(1)          # cross-fit: unbiased under a fixed sign pattern
        ma = (np.sign(aA) * aB).sum(1)
        ch = np.abs(aA.sum(1)) / np.maximum(np.abs(aA).sum(1), 1e-300)
        rs = []
        for L in range(LMAX):
            i = np.where(lay == L)[0]
            if len(i) < 4:
                continue
            dr = (rk(mf[i]) - rk(ma[i])) / (len(i) - 1)      # SIGNED
            y, pr = dr, -ch[i]
            if partial:
                g = rk(ma[i])
                y, pr = resid(y, g), resid(pr, g)
            rs.append(spear(y, pr))
        xs.append(zpool(rs))
    return float(np.nanmean(xs))


def bca(boot, hat, jack):
    b = np.asarray([x for x in boot if x == x])
    pr = min(max(float((b < hat).mean()), 1 / (2 * len(b))), 1 - 1 / (2 * len(b)))
    z0 = N.inv_cdf(pr)
    jm = np.mean(jack)
    den = 6.0 * ((((jm - jack) ** 2).sum()) ** 1.5)
    a = ((jm - jack) ** 3).sum() / den if den > 0 else 0.0
    out = []
    for q in (0.025, 0.975):
        z = N.inv_cdf(q)
        adj = z0 + (z0 + z) / max(1 - a * (z0 + z), 1e-12)
        out.append(float(np.percentile(b, 100 * N.cdf(adj))))
    return out


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
    H, nb = len(lay), bf.shape[1]
    print(f'  layers 0-{LMAX-1}, H = {H} heads, base instances n = {nb}')

    # ── G0 RELIABILITY, FIRST ──
    rr = []
    for _ in range(N_SPLIT):
        p = rng.permutation(nb)
        A, B = p[:nb // 2], p[nb // 2:]
        mA = (np.sign(ba[:, A].mean(1)) * ba[:, A].mean(1)).sum(1)
        mB = (np.sign(ba[:, B].mean(1)) * ba[:, B].mean(1)).sum(1)
        rr.append(zpool([spear(mA[lay == L], mB[lay == L]) for L in range(LMAX)]))
    r_half = float(np.nanmean(rr))
    r_sb = 2 * r_half / (1 + r_half) if r_half > -1 else float('nan')
    out['G0_reliability'] = {'within_layer_split_half': r_half, 'spearman_brown': r_sb,
                             'warn_below': RULE['G0_reliability_warn_below'],
                             'usable': bool(r_sb >= RULE['G0_reliability_warn_below'])}
    print(f"  G0 RELIABILITY FIRST: within-layer split-half r {r_half:.4f}  "
          f"Spearman-Brown {r_sb:.4f}   >= 0.70: {out['G0_reliability']['usable']}")

    # ── the estimate and its bootstrap resolution ──
    res = {}
    for partial in (True, False):
        name = 'partialled' if partial else 'raw'
        hat = crossfit_X(bf, ba, lay, np.random.default_rng(SEED), partial)
        boot = [crossfit_X(bf[:, i], ba[:, i], lay, rng, partial, n_split=8)
                for i in (rng.integers(0, nb, nb) for _ in range(N_BOOT // 10))]
        boot = np.array([x for x in boot if x == x])
        jack = np.array([crossfit_X(np.delete(bf, i, 1), np.delete(ba, i, 1), lay,
                                    np.random.default_rng(SEED + i), partial, n_split=8)
                         for i in range(nb)])
        RES = float(boot.std(ddof=1))
        T = max(RULE['T_floor'], 2 * RES)
        ci = bca(boot, hat, jack)
        res[name] = {'X': hat, 'RES': RES, 'T': T, 'bca_ci95': ci,
                     'ci_covers_zero': bool(ci[0] <= 0 <= ci[1]),
                     'abs_X_below_T': bool(abs(hat) < T), 'n_boot': len(boot)}
        print(f"  {name.upper():<11} X {hat:+.4f}   RES {RES:.4f}  T = max(0.15, 2*RES) = {T:.4f}   "
              f"BCa CI [{ci[0]:+.4f}, {ci[1]:+.4f}]   |X|<T {res[name]['abs_X_below_T']}   "
              f"CI covers 0 {res[name]['ci_covers_zero']}")
    out['results'] = res
    T = res['partialled']['T']

    # ── G1 POSITIVE CONTROL: inject rho = 0.30 on the REAL c_h vector ──
    aA = ba.mean(1)
    ch_real = np.abs(aA.sum(1)) / np.maximum(np.abs(aA).sum(1), 1e-300)
    tgt = RULE['G1_target_rho']
    hits = 0
    for _ in range(N_POWER):
        rs = []
        for L in range(LMAX):
            i = np.where(lay == L)[0]
            u = -ch_real[i]
            z = (u - u.mean()) / (u.std(ddof=1) + 1e-300)
            y = tgt * z + math.sqrt(max(1 - tgt ** 2, 0.0)) * rng.standard_normal(len(i))
            rs.append(spear(y, u))
        if abs(zpool(rs)) >= T:
            hits += 1
    rec = hits / N_POWER
    g1 = bool(rec >= RULE['G1_min_recovery'])
    out['G1_positive_control'] = {'target_rho': tgt, 'recovery': rec, 'n_draws': N_POWER,
                                  'threshold_used': T, 'passes': g1}
    print(f"  G1 POSITIVE CONTROL: injected rho {tgt}, recovered |X| >= T in {rec:.3f} of "
          f"{N_POWER} draws   >= {RULE['G1_min_recovery']}: {g1}")

    # ── G2 SHAM ──
    xs = crossfit_X(bf, ba, lay, np.random.default_rng(SEED + 1), True, n_split=20, sham=True)
    g2 = bool(abs(xs) < RULE['G2_max_sham'])
    out['G2_sham'] = {'X_sham': xs, 'max_allowed': RULE['G2_max_sham'], 'passes': g2}
    print(f"  G2 SHAM (position index permuted WITHIN each base instance): X {xs:+.4f}   "
          f"|X| < {RULE['G2_max_sham']}: {g2}")

    p = res['partialled']
    verdict = ('UNVERIFIED_INSTRUMENT_UNDERPOWERED' if not g1
               else 'UNVERIFIED_RECTIFICATION_CONFOUND' if not g2
               else 'CANCELLATION_DEAD' if (p['abs_X_below_T'] or p['ci_covers_zero'])
               else 'CANCELLATION_LIVES_NOT_A_RESULT_ONE_MODEL')
    out['verdict'] = verdict
    print(f'\n  VERDICT  {verdict}')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r37_amended_cancellation.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
