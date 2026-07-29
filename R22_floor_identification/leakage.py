#!/usr/bin/env python3
"""Recover WHICH heads were drawn into this repository's central reference distribution.

Registered in R22_floor_identification/LEAKAGE_PREREGISTRATION.md, committed before this file.

No GPU, no model. `R1_noise_floor/run.py` builds its draws from `random.Random(DRAW_SEED)` over a
deterministic pool, so the identities were never lost -- only the per-draw effect values were, and
those are supplied by `R10`'s exhaustive scan under the control below.

TWO CHAINED POSITIVE CONTROLS, BOTH EXACT:
  1. the replay must contain L16H3, because the stored `min` matches its effect to 1.589e-07
  2. substituting R10's per-head values for the recovered list must reproduce the stored
     sd = 0.22088667589755384 -- which validates the replay and the substitution at once
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
import headline as H                                                     # noqa: E402

DRAW_SEED = 20260727            # R1_noise_floor/run.py:82
N_DRAWS = 30                    # run.py:79
SET_SIZES = [1, 2, 5, 10, 20]   # run.py:78
STORED_SD = 0.22088667589755384
STORED_MIN = -0.4668109973271688
PUBLISHED_FLOOR = 0.4417733517951077
DECIDING_MARGIN_PCT = 5.667495896844854
N_NULL = 2000
NULL_SEED = 20260729


def sd(v):
    mu = sum(v) / len(v)
    return math.sqrt(sum((x - mu) ** 2 for x in v) / (len(v) - 1))


def main():
    a1 = json.load(open(REPO / 'R1_noise_floor' / 'results' / 'original_vocabulary'
                        / 'r1v1_atlas_qwen2.5-1.5b.json'))
    lo, hi = a1['band']
    slo, shi = a1['sham_band']
    NH = a1['n_heads']

    # ---- replay, in R1's exact construction order
    rng = random.Random(DRAW_SEED)
    band_pool = [(L, h) for L in range(lo, hi + 1) for h in range(NH)]
    sham_pool = [(L, h) for L in range(slo, shi + 1) for h in range(NH)]
    draws = {}
    for k in SET_SIZES:
        if k > len(band_pool):
            continue
        draws[('band', k)] = [rng.sample(band_pool, k) for _ in range(N_DRAWS)]
        draws[('sham', k)] = [rng.sample(sham_pool, min(k, len(sham_pool)))
                              for _ in range(N_DRAWS)]
    k1 = [d[0] for d in draws[('band', 1)]]
    tag = lambda t: 'L%02dH%02d' % t

    eff = H.r1_prior_effects()
    eight = sorted((int(k[1:k.index('H')]), int(k[k.index('H') + 1:])) for k in eff['effects'])
    leaked = [t for t in eight if t in k1]

    r10 = json.load(open(REPO / 'R10_exhaustive' / 'results'
                         / 'r10_exhaustive_qwen2.5-1.5b.json'))
    lay = {int(k): v for k, v in r10['layers'].items()}
    val = {(L, h): lay[L]['per_head'][str(h)] for L in range(lo, hi + 1) for h in range(NH)}

    out = {'draw_seed': DRAW_SEED, 'n_draws': N_DRAWS,
           'k1_draws': [tag(t) for t in k1],
           'n_distinct_drawn': len(set(k1)),
           'the_eight': [tag(t) for t in eight],
           'leaked': [tag(t) for t in leaked], 'k_leak': len(leaked),
           'expected_k_leak': len(eight) * (1 - (1 - 1 / len(band_pool)) ** N_DRAWS)}

    # ---- control 1
    c1 = (16, 3) in k1
    out['control_1_replay_contains_L16H3'] = c1
    print(f'  CONTROL 1  the replay contains L16H3: {c1}  -> {"PASS" if c1 else "FAIL"}')

    # ---- control 2
    sub = [val[t] for t in k1]
    sd_sub = sd(sub)
    err = abs(sd_sub - STORED_SD)
    c2 = err < 1e-6
    out['control_2'] = {'sd_substituted': sd_sub, 'sd_stored': STORED_SD, 'abs_err': err,
                        'passes_1e-6': c2, 'min_substituted': min(sub), 'min_stored': STORED_MIN}
    print(f'  CONTROL 2  substituted sd {sd_sub!r}  vs stored {STORED_SD!r}')
    print(f'             abs err {err:.3e}  -> {"PASS" if c2 else "FAIL"}')

    print(f'\n  k_leak {len(leaked)} of 8   expected under the design '
          f'{out["expected_k_leak"]:.4f}   leaked: {[tag(t) for t in leaked]}')
    print(f'  the 30 k=1 draws cover {len(set(k1))} distinct heads of {len(band_pool)}')

    if not (c1 and c2):
        out['verdict'] = 'UNVERIFIED_CONTROL_FAILED'
        print('\n  -> UNVERIFIED: a chained control failed, so the leave-out floor is not an '
              'estimate. Not an acquittal.')
        json.dump(out, open(HERE / 'results' / 'r22_leakage.json', 'w'), indent=1)
        return 3

    # ---- the registered statistic: leave ALL EIGHT out of the reference
    keep = [val[t] for t in k1 if t not in eight]
    floor_out = 2 * sd(keep) if len(keep) > 1 else float('nan')
    E = {k: v['drop'] for k, v in eff['effects'].items()}
    n_in = sum(1 for x in E.values() if abs(x) <= floor_out)
    shift_pct = 100 * abs(floor_out - PUBLISHED_FLOOR) / PUBLISHED_FLOOR

    # ---- the confound control: matched-rank random removals
    centred = {t: abs(val[t] - sum(val.values()) / len(val)) for t in band_pool}
    ranked = sorted(band_pool, key=lambda t: centred[t])
    pos = sorted(ranked.index(t) for t in eight)
    rng2 = random.Random(NULL_SEED)
    null = []
    for _ in range(N_NULL):
        # match the RANK PROFILE of the real eight, jittering each within +-5 ranks
        pick, used = [], set()
        for p in pos:
            for _try in range(50):
                j = min(len(ranked) - 1, max(0, p + rng2.randint(-5, 5)))
                if ranked[j] not in used:
                    used.add(ranked[j]); pick.append(ranked[j]); break
        kp = [val[t] for t in k1 if t not in used]
        if len(kp) > 1:
            null.append(100 * abs(2 * sd(kp) - PUBLISHED_FLOOR) / PUBLISHED_FLOOR)
    null.sort()
    pctile = sum(1 for z in null if z < shift_pct) / len(null)

    verdict = ('CONTAMINATION-MATERIAL'
               if (shift_pct >= DECIDING_MARGIN_PCT or n_in != eff['n_inside'])
               else 'CONTAMINATION-IMMATERIAL')
    out.update({'floor_published': PUBLISHED_FLOOR, 'floor_leave_all_eight_out': floor_out,
                'n_kept': len(keep), 'shift_pct': shift_pct,
                'deciding_margin_pct': DECIDING_MARGIN_PCT,
                'n_inside_leave_out': n_in, 'n_inside_published': eff['n_inside'],
                'matched_null': {'n': len(null), 'median': null[len(null) // 2],
                                 'p95': null[int(0.95 * len(null))],
                                 'percentile_of_observed': pctile, 'n_draw': N_NULL,
                                 'seed': NULL_SEED},
                'verdict': verdict})
    print(f'\n  floor {PUBLISHED_FLOOR:.6f} -> leave-all-eight-out {floor_out:.6f} '
          f'({len(keep)} draws kept)   shift {shift_pct:.4f}%  '
          f'vs deciding margin {DECIDING_MARGIN_PCT:.4f}%')
    print(f'  n_inside {eff["n_inside"]} -> {n_in}')
    print(f'  MATCHED-RANK NULL  median {null[len(null) // 2]:.4f}%  '
          f'p95 {null[int(0.95 * len(null))]:.4f}%  observed at percentile {pctile:.4f}')
    print(f'\n  REGISTERED VERDICT: {verdict}')
    op = HERE / 'results' / 'r22_leakage.json'
    op.parent.mkdir(exist_ok=True)
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
