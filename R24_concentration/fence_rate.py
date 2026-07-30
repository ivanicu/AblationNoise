#!/usr/bin/env python3
"""How often does `best_step`'s argmax land on its own search-window fence, under pure noise?

`best_step` in run.py maximises |mean(after) - mean(before)| / sqrt(SS_within/(n-2)). The maximum-
likelihood changepoint maximises |delta| / (s * sqrt(1/na + 1/nb)). Dropping the balance factor
removes the penalty on unbalanced splits, so the estimator is drawn toward the ends of its own
permitted range -- which is exactly where R24 reported the step, at c=24 of n=28 with min_side=4.

An independent reviewer measured this. The two figures are load-bearing: they are the reason no
location claim in R24 survives, and no generator in this repository emitted them. Reproduced here with
an independent implementation, because a number taken on trust from another agent is the thing this
repository refuses everywhere else.

The ML-weighted variant is measured in the same run, so the comparison is like-for-like rather than
as-coded against a hoped-for alternative.
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run as C                                                          # noqa: E402

SEED = 20260729
N_DRAWS = 20000
N, MIN_SIDE = 28, 4


def best_step_ml(y, min_side=MIN_SIDE):
    """The same scan with the balance factor restored."""
    n = len(y)
    best, at = -1.0, None
    for c in range(min_side, n - min_side + 1):
        a, b = y[:c], y[c:]
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        va = sum((x - ma) ** 2 for x in a) + sum((x - mb) ** 2 for x in b)
        sd = math.sqrt(va / (n - 2)) if n > 2 else 0.0
        if sd <= 0:
            continue
        t = abs(mb - ma) / (sd * math.sqrt(1.0 / len(a) + 1.0 / len(b)))
        if t > best:
            best, at = t, c
    return best, at


def main():
    rng = random.Random(SEED)
    lo, hi = MIN_SIDE, N - MIN_SIDE
    n_candidates = hi - lo + 1
    uniform = 2.0 / n_candidates                 # the two fences out of all permitted splits
    hits_asc, hits_ml = 0, 0
    at_asc = {c: 0 for c in range(lo, hi + 1)}
    for _ in range(N_DRAWS):
        y = [rng.gauss(0, 1) for _ in range(N)]
        _, c1 = C.best_step(y, MIN_SIDE)
        _, c2 = best_step_ml(y, MIN_SIDE)
        at_asc[c1] += 1
        hits_asc += (c1 in (lo, hi))
        hits_ml += (c2 in (lo, hi))
    out = {'seed': SEED, 'n_draws': N_DRAWS, 'n_layers': N, 'min_side': MIN_SIDE,
           'n_candidate_splits': n_candidates,
           'uniform_fence_rate': uniform,
           'as_coded_fence_rate': hits_asc / N_DRAWS,
           'ml_weighted_fence_rate': hits_ml / N_DRAWS,
           'inflation_over_uniform': (hits_asc / N_DRAWS) / uniform,
           'fence_rate_at_lo': at_asc[lo] / N_DRAWS,
           'fence_rate_at_hi': at_asc[hi] / N_DRAWS,
           'argmax_histogram': {str(k): v / N_DRAWS for k, v in at_asc.items()}}
    print(f'  pure Gaussian noise, n={N}, min_side={MIN_SIDE}, {N_DRAWS} draws')
    print(f'    permitted splits c in [{lo}, {hi}]  ->  {n_candidates} candidates, '
          f'uniform fence rate {uniform:.4f}')
    print(f'    as coded (no balance factor)   argmax on a fence in {hits_asc / N_DRAWS:.4f}'
          f'   = {(hits_asc / N_DRAWS) / uniform:.2f}x uniform')
    print(f'    balance factor restored        argmax on a fence in {hits_ml / N_DRAWS:.4f}')
    print(f'    argmax at c={lo}: {at_asc[lo] / N_DRAWS:.4f}   at c={hi}: '
          f'{at_asc[hi] / N_DRAWS:.4f}')
    (HERE / 'results').mkdir(exist_ok=True)
    op = HERE / 'results' / 'r24_fence_rate.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
