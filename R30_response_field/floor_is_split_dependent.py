#!/usr/bin/env python3
"""The floor anomaly that gates the 4.676 ratio. Zero forwards.

R30's rank sweep produced null-A floors that disagree between two cells under IDENTICAL code:

    k          1       2       3       4       5
    off0    0.0192  0.0412  0.0559  0.0701  0.0776      = 2.0-2.3x k/120
    off400  0.0082  0.0173  0.0267  0.0381  0.0459      = 1.0x k/120
    k/120   0.0083  0.0167  0.0250  0.0333  0.0417

The floor is the denominator of excess(5)/excess(1) = 4.676 and 4.960, which is what killed WA. An
unexplained 2.3x in that denominator makes the ratio unquotable.

FIRST HYPOTHESIS, MEASURED AND DEAD. Heavy-tailed rows have effective dimension well below 120, so a
random direction captures ~1/n_eff rather than 1/120. Participation ratio of the two-way residual:

    off0    n_eff median 41.39   median(1/n_eff) 0.02416
    off400  n_eff median 38.28   median(1/n_eff) 0.02612

Nearly identical, and off400 is slightly MORE concentrated -- so if n_eff drove the floor, off400's
would be the HIGHER one. It is the lower one. The hypothesis predicts the opposite of the data and is
dead. It also REFRAMES the anomaly: 1/n_eff says BOTH floors should sit near 0.024-0.026, which is
where off0 is. The cell needing explanation is off400 being LOW, not off0 being high.

SECOND HYPOTHESIS, TESTED HERE. The floor was computed on ONE head split per cell -- `j =
rng.permutation(n)` once, then the same (ra, rb) reused for every k and every null draw, with the two
cells getting different splits because the rng advanced between them. A pooled statistic on one head
split has already swung 3.4x in this project (0.6591 -> 0.2396 on rng ORDER alone) and I have fixed
that defect twice today on other paths. This is the third path.

If that is the cause, averaging the floor over independent splits must collapse the 2.3x gap.

This file recomputes BOTH the floor and the observed median-head R2 over the SAME 30 independent
splits, so the excess ratio is finally computed consistently rather than from two single draws.

═══ REGISTERED BEFORE THE RUN ═══
  H1  If the off0/off400 floor ratio at k=1 falls below 1.5 once averaged over 30 splits, the
      anomaly IS split dependence and the single-split floor is retracted.
  H2  The excess ratio is re-reported from the 30-split means with its own sd. If the 30-split
      excess(5)/excess(1) crosses BELOW the registered kill of 3.0 in either cell, then WA_DEAD as
      read in 06f40a4 does not survive its own floor correction and reverts to UNVERIFIED.
  No threshold is amended after any number is seen.
"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
N_SPLIT = 30
N_FLOOR = 20
KS = (1, 2, 3, 4, 5)
RULE = {'H1_anomaly_is_split_if_ratio_below': 1.5, 'H2_wa_kill_threshold': 3.0,
        'n_splits': N_SPLIT, 'n_floor_draws_per_split': N_FLOOR}


def two_way_resid(D):
    mu = D.mean()
    return D - mu - (D.mean(1) - mu)[:, None] - (D.mean(0) - mu)[None, :]


def null_A(D, rng):
    return np.array([row[rng.permutation(D.shape[1])] for row in D])


def median_head_r2(E, ra, rb, k):
    A, B = E[ra], E[rb]
    _, _, Vt = np.linalg.svd(A, full_matrices=False)
    V = Vt[:k].T
    P = B @ V @ V.T
    per = [1 - ((B[j] - P[j]) ** 2).sum() / (B[j] ** 2).sum()
           for j in range(B.shape[0]) if (B[j] ** 2).sum() > 0]
    return float(np.median(per))


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'dead_hypothesis': {'name': 'effective dimension (participation ratio)',
                               'off0_median_n_eff': 41.39, 'off400_median_n_eff': 38.28,
                               'why_dead': 'predicts off400 floor HIGHER than off0; observed lower'}}
    res = {}
    for tag in ('off0', 'off400'):
        D = np.load(REPO / 'R29_cancellation' / 'results' /
                    f'r29_vectors_qwen2.5-1.5b_I_final_{tag}.npz')['delta'].astype(np.float64)
        E = two_way_resid(D)
        n = D.shape[0]
        obs = {k: [] for k in KS}
        flo = {k: [] for k in KS}
        for _ in range(N_SPLIT):
            j = rng.permutation(n)
            ra, rb = j[:n // 2], j[n // 2:]
            for k in KS:
                obs[k].append(median_head_r2(E, ra, rb, k))
            fl = {k: [] for k in KS}
            for _ in range(N_FLOOR):
                En = two_way_resid(null_A(D, rng))
                for k in KS:
                    fl[k].append(median_head_r2(En, ra, rb, k))
            for k in KS:
                flo[k].append(float(np.mean(fl[k])))
        row = {}
        for k in KS:
            o, f = np.array(obs[k]), np.array(flo[k])
            row[f'k{k}'] = {'r2_median_head': float(o.mean()), 'r2_sd': float(o.std(ddof=1)),
                            'floor': float(f.mean()), 'floor_sd': float(f.std(ddof=1)),
                            'floor_over_k_div_120': float(f.mean() / (k / 120)),
                            'excess': float(o.mean() - f.mean())}
        # excess ratio per split, so its spread is honest
        rr = [(obs[5][i] - flo[5][i]) / (obs[1][i] - flo[1][i])
              for i in range(N_SPLIT) if (obs[1][i] - flo[1][i]) > 0]
        row['excess_ratio_5_over_1'] = float(np.mean(rr))
        row['excess_ratio_sd'] = float(np.std(rr, ddof=1))
        row['excess_ratio_min'] = float(min(rr))
        row['excess_ratio_max'] = float(max(rr))
        res[tag] = row
        print(f'\n  {tag}   {N_SPLIT} independent head splits, {N_FLOOR} null draws each')
        print(f"    {'k':<4}{'median-head R2':<20}{'floor':<22}{'floor/(k/120)':<16}excess")
        for k in KS:
            v = row[f'k{k}']
            print(f"    {k:<4}{v['r2_median_head']:+.4f}+-{v['r2_sd']:.4f}     "
                  f"{v['floor']:+.4f}+-{v['floor_sd']:.4f}      {v['floor_over_k_div_120']:<16.2f}"
                  f"{v['excess']:+.4f}")
        print(f"    excess(5)/excess(1) = {row['excess_ratio_5_over_1']:.3f} "
              f"+-{row['excess_ratio_sd']:.3f}  [{row['excess_ratio_min']:.3f}, "
              f"{row['excess_ratio_max']:.3f}]")
    out['cells'] = res

    r1 = res['off0']['k1']['floor'] / res['off400']['k1']['floor']
    out['floor_ratio_k1_off0_over_off400'] = r1
    out['H1_anomaly_is_split_dependence'] = bool(r1 < RULE['H1_anomaly_is_split_if_ratio_below'])
    ratios = [res[t]['excess_ratio_5_over_1'] for t in res]
    out['H2_wa_kill_survives'] = bool(all(x >= RULE['H2_wa_kill_threshold'] for x in ratios))
    print(f"\n  H1  floor ratio off0/off400 at k=1, 30-split: {r1:.2f}  "
          f"(single-split was {0.0192 / 0.0082:.2f})  -> "
          f"{'SPLIT DEPENDENCE' if out['H1_anomaly_is_split_dependence'] else 'NOT split dependence'}")
    print(f"  H2  excess(5)/excess(1) = {ratios[0]:.3f} and {ratios[1]:.3f} vs kill at "
          f"{RULE['H2_wa_kill_threshold']}  -> WA_DEAD "
          f"{'SURVIVES its floor correction' if out['H2_wa_kill_survives'] else 'REVERTS TO UNVERIFIED'}")

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r30_floor_split_dependence.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
