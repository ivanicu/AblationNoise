#!/usr/bin/env python3
"""Does SIGN CANCELLATION generate R35's early-layer reordering? Zero forwards.

R35: changing the ablation SUPPORT destroys ~10x more of the within-layer ordering than changing
the entire item set, and the destruction is confined to layers 0-9. R36 killed FINAL-TOKEN
LOCALISATION as the generator -- and was then itself downgraded to UNVERIFIED, because at position 7
a flat profile, a margin-proportional profile and no-final-preference all predict the same number
to within 0.0098.

What survives, and it is a SIGNED effect that a sign-blind statistic was structurally unable to see:

    c_h = |sum_t e_t| / sum_t |e_t|     under `.all`, the fraction of a head's absolute positional
                                         mass that SURVIVES summation. 1 = no cancellation.

Measured on the object: mean c_h = 0.7341 (sd 0.3226, range [0.0195, 1.0000]) under `.all` against
0.8915 under `.final`. So 27% of the absolute positional mass cancels under exactly the support that
does the reordering. Two heads with equal sum_t|e_t| and different sign patterns get DIFFERENT
I_all totals and IDENTICAL I_final totals -- which mechanically forces reordering, with no
positional preference of any kind.

═══ A MECHANICAL DEPENDENCE I MEASURED BEFORE BUILDING, NOT AFTER ═══
c_h's DENOMINATOR IS m_h(.all), and m_h is the very quantity whose rank forms the outcome. Measured
within-layer over layers 0-9, H = 120:

    corr(c_h, m_h(.all))     +0.3839      <- the path is LIVE, not hypothetical
    corr(c_h, m_h(.final))   -0.1916
    corr(c_h, |Delta rank|)  +0.1462

So a raw rho(Delta r, -c_h) is contaminated by construction. BOTH forms are therefore computed and
BOTH are reported; the PARTIALLED one is the primary, because it is the only one whose predictor is
free of the outcome's own denominator:

    RAW        rho( Delta r_h , -c_h )
    PARTIALLED rho( resid(Delta r_h | rank m_h(.all)) , resid(-c_h | rank m_h(.all)) )   <- primary

═══ REGISTERED BEFORE THE RUN ═══
  unit        head, layers 0-9, qwen2.5-1.5b, H = 120; resampling unit = the 64 BASE INSTANCES
  outcome     Delta r_h = |rank_L(m_h | .final) - rank_L(m_h | .all)| / (n_L - 1)
  predictor   c_h under `.all`
  X           Spearman rho, Fisher-z averaged WITHIN layer, then pooled over layers 0-9
  null        permute c_h WITHIN layer, 2000 draws. ITS SPREAD IS PRINTED FIRST -- the last
              permutation null in this project was EXACTLY INVARIANT for the statistic it was
              supposed to test, so a null that cannot move is checked for before it is trusted.
  RES         base-instance bootstrap sd of X. NO propagated sem. The propagation is deleted from
              this project: it is the resolution of a different estimand.
  T           max(0.15, RES)
  KILL        |X_partialled| < T, OR the 95% BCa CI covers 0
              -> "support-dependent cancellation explains R35's early-layer reordering" is DEAD,
                 the whole positional generator for R35 is dropped, and the queued 3b crossed scan
                 stops being worth its GPU.

═══ REGISTERED ASYMMETRY, because one model is not a result ═══
A NEGATIVE here is a legitimate one-model finding, because it REMOVES work and cannot be inflated
into a claim. A POSITIVE is NOT a result; it only earns the 3b crossed scan. Stated before the run
so the asymmetry cannot be chosen afterwards.

═══ MANDATORY SAME-ITERATION CONTROL ═══
If the within-layer spread of head effects is below the instrument's noise, rank is near-random
under BOTH supports and X is uninterpretable whichever way it lands. Reported per layer 0-9 against
R11's measured floor.
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
N_NULL = 2000
N_BOOT = 2000
LMAX = 10
RULE = {'T_floor': 0.15, 'n_null': N_NULL, 'n_boot': N_BOOT, 'layers': [0, 9],
        'unit': 'base instance n=64', 'primary': 'partialled on rank m_h(.all)',
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


def resid(y, x):
    x = x - x.mean()
    v = (x * x).sum()
    return y - y.mean() - x * ((x * (y - y.mean())).sum() / v if v > 0 else 0.0)


def fisher_pool(rhos):
    z = [0.5 * math.log((1 + r) / (1 - r)) for r in rhos if r == r and abs(r) < 0.999999]
    if not z:
        return float('nan')
    zb = sum(z) / len(z)
    return float((math.exp(2 * zb) - 1) / (math.exp(2 * zb) + 1))


def stat(ef, ea, lay, partial):
    """X over layers 0-9. ef, ea are (H, 8) position means under .final / .all."""
    mf, ma = np.abs(ef).sum(1), np.abs(ea).sum(1)
    ch = np.abs(ea.sum(1)) / np.maximum(ma, 1e-300)
    rhos = []
    for L in range(LMAX):
        i = np.where(lay == L)[0]
        if len(i) < 4:
            continue
        dr = np.abs(rk(mf[i]) - rk(ma[i])) / (len(i) - 1)
        y, p = dr, -ch[i]
        if partial:
            g = rk(ma[i])
            y, p = resid(y, g), resid(p, g)
        rhos.append(spear(y, p))
    return fisher_pool(rhos), rhos, ch, mf, ma


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
    return out, float(z0), float(a)


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
    bf = np.stack([np.array(c[k]['base_pos'])[:, :, 0] for k in keys])[m]        # (H,64,8)
    ba = np.stack([np.array(c[k.replace('.final', '.all')]['base_pos'])[:, :, 0]
                   for k in keys])[m]
    ef, ea = bf.mean(1), ba.mean(1)
    H, nb = len(lay), bf.shape[1]
    print(f'  layers 0-{LMAX-1}, H = {H} heads, resampling unit = base instance n = {nb}')

    # ── the mechanical path, measured and stated before anything is read ──
    _, _, ch, mf, ma = stat(ef, ea, lay, False)
    dep = {'corr_c_vs_m_all': float(np.nanmean([spear(ch[lay == L], ma[lay == L])
                                                for L in range(LMAX)])),
           'corr_c_vs_m_final': float(np.nanmean([spear(ch[lay == L], mf[lay == L])
                                                  for L in range(LMAX)]))}
    print(f"  MECHANICAL PATH: corr(c_h, m_h(.all)) {dep['corr_c_vs_m_all']:+.4f}   "
          f"corr(c_h, m_h(.final)) {dep['corr_c_vs_m_final']:+.4f}  -> partialled form is PRIMARY")
    print(f"  c_h under .all: mean {ch.mean():.4f} sd {ch.std(ddof=1):.4f} "
          f"range [{ch.min():.4f}, {ch.max():.4f}]   m(.all)/m(.final) median "
          f"{np.median(ma/mf):.3f}x")
    out['mechanical_dependence'] = dep
    out['c_h'] = {'mean': float(ch.mean()), 'sd': float(ch.std(ddof=1)),
                  'min': float(ch.min()), 'max': float(ch.max())}

    res = {}
    for partial in (True, False):
        name = 'partialled' if partial else 'raw'
        hat, rhos, *_ = stat(ef, ea, lay, partial)

        # ── NULL FIRST, and its SPREAD, because the last one could not move ──
        nl = []
        for _ in range(N_NULL):
            ea2 = ea.copy()
            for L in range(LMAX):
                i = np.where(lay == L)[0]
                ea2[i] = ea2[i][rng.permutation(len(i))]
            nl.append(stat(ef, ea2, lay, partial)[0])
        nl = np.array([x for x in nl if x == x])
        degenerate = bool(nl.std(ddof=1) < 1e-6)
        print(f'\n  {name.upper()}')
        print(f"    NULL FIRST: within-layer permutation of c_h, {len(nl)} draws -> "
              f"mean {nl.mean():+.4f}  sd {nl.std(ddof=1):.4f}  "
              f"p95 {np.percentile(np.abs(nl), 95):.4f}   degenerate: {degenerate}")

        boot = []
        for _ in range(N_BOOT):
            idx = rng.integers(0, nb, nb)
            boot.append(stat(bf[:, idx].mean(1), ba[:, idx].mean(1), lay, partial)[0])
        boot = np.array([x for x in boot if x == x])
        jack = np.array([stat(np.delete(bf, i, 1).mean(1), np.delete(ba, i, 1).mean(1),
                              lay, partial)[0] for i in range(nb)])
        RES = float(boot.std(ddof=1))
        T = max(RULE['T_floor'], RES)
        ci, z0, a = bca(boot, hat, jack)
        covers = bool(ci[0] <= 0 <= ci[1])
        print(f"    RESOLUTION (base-instance bootstrap sd, no propagation) {RES:.4f}  -> "
              f"T = max(0.15, RES) = {T:.4f}")
        print(f"    X {hat:+.4f}   BCa 95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]   "
              f"|X| < T: {abs(hat) < T}   CI covers 0: {covers}")
        res[name] = {'X': hat, 'per_layer_rho': rhos, 'null_mean': float(nl.mean()),
                     'null_sd': float(nl.std(ddof=1)),
                     'null_abs_p95': float(np.percentile(np.abs(nl), 95)),
                     'null_degenerate': degenerate, 'RES': RES, 'T': T,
                     'bca_ci95': ci, 'ci_covers_zero': covers,
                     'abs_X_below_T': bool(abs(hat) < T)}
    out['results'] = res

    # ── mandatory control: within-layer spread vs the instrument floor ──
    try:
        r11 = json.load(open(REPO / 'R11_instrument_noise' / 'results' /
                             'measurability_qwen2.5-1.5b.json'))
        floor = float(r11.get('mean_sem_band', float('nan')))
    except (OSError, ValueError):
        floor = float('nan')
    spread = {int(L): float(np.std(ma[lay == L], ddof=1)) for L in range(LMAX)}
    below = [L for L, v in spread.items() if v < floor] if floor == floor else []
    out['instrument_control'] = {'r11_mean_sem_band': floor, 'within_layer_sd_m_all': spread,
                                 'layers_below_floor': below}
    print(f"\n  INSTRUMENT CONTROL: R11 mean_sem_band {floor:.5f} margin-nats; within-layer sd of "
          f"m_h(.all) ranges [{min(spread.values()):.4f}, {max(spread.values()):.4f}]")
    print(f"    layers whose spread is BELOW the noise floor: {below if below else 'none'}")

    p = res['partialled']
    verdict = ('CANCELLATION_DEAD' if (p['abs_X_below_T'] or p['ci_covers_zero'])
               else 'CANCELLATION_LIVES_NOT_A_RESULT_ONE_MODEL')
    out['verdict'] = verdict
    print(f'\n  VERDICT (read off the PARTIALLED form)  {verdict}')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r37_support_reordering.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
