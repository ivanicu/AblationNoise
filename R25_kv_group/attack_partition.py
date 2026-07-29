#!/usr/bin/env python3
"""Is it the KV GROUP, or is it any contiguous block of head indices?

The claim committed alongside this file says the grouped-query partition explains 4 to 9 points of a
layer's ablation-effect spread. The partition it used is heads 0..5 against 6..11 -- a CONTIGUOUS
BLOCK. Any reason for nearby head indices to resemble each other reproduces that number without any
key/value stream being involved.

PROPERTY  the KV group structures the effects
PROXY     the block partition 0..5 | 6..11 explains variance
DIRECTION KV grouping implies this partition explains variance. The converse does NOT hold.

So the test is not whether the KV partition explains variance -- already measured -- but whether it
is EXCEPTIONAL among partitions of the same shape. Two references, both exhaustive, no sampling:

  1. every balanced partition into two halves    462 for 12 heads, 6435 for 16
  2. every contiguous split point                11 for 12 heads, 15 for 16

If the KV partition sits mid-pack in (1), a layer merely has SOME half-half structure and the
architecture is not what found it. If it is exceptional in (1) but ordinary among (2), the finding is
about contiguity, not about key/value sharing.

NO VERDICT IS EMITTED. Percentile ranks are the output.
"""
import itertools
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import icc as I                                                          # noqa: E402


def balanced_partitions(n):
    """Every split of n indices into two equal halves, each counted once."""
    half = n // 2
    out = []
    for c in itertools.combinations(range(n), half):
        if 0 not in c:                       # canonical: index 0 always in the first half
            continue
        s = set(c)
        out.append([0 if i in s else 1 for i in range(n)])
    return out


def contiguous_splits(n):
    return [[0 if i < c else 1 for i in range(n)] for c in range(1, n)]


def rank(value, pool):
    """Fraction of the pool at or below `value`. 1.0 means nothing beat it."""
    return sum(1 for x in pool if x <= value) / len(pool)


def main():
    out = {'note': 'percentile ranks only, no verdict'}
    print('  KV partition against EVERY partition of the same shape, exhaustive, no sampling')
    print(f'    {"cell":<32}{"kv sum":<10}{"rank vs balanced":<19}{"rank vs contiguous":<20}'
          f'{"n_bal":<8}best-balanced')
    res = {}
    for model, cfg in I.GQA.items():
        nh, nkv = cfg['n_heads'], cfg['n_kv']
        kv = I.groups(nh, nkv)
        bal = balanced_partitions(nh)
        con = contiguous_splits(nh)
        for support in ('I_final', 'I_all'):
            for absolute in (True, False):
                prof = I.load(model, support, absolute)
                if prof is None:
                    continue
                key = f'{model}|{support}|{"abs" if absolute else "signed"}'

                def total(g):
                    return sum(e for e in (I.eta_sq(v, g) for v in prof) if e == e)

                kv_v = total(kv)
                bal_v = [total(g) for g in bal]
                con_v = [total(g) for g in con]
                rb, rc = rank(kv_v, bal_v), rank(kv_v, con_v)
                best = max(range(len(bal)), key=lambda i: bal_v[i])
                bestg = ''.join(str(x) for x in bal[best])
                res[key] = {'kv_sum_eta_sq': kv_v, 'rank_vs_balanced': rb,
                            'rank_vs_contiguous': rc, 'n_balanced': len(bal),
                            'n_contiguous': len(con),
                            'balanced_max': max(bal_v), 'balanced_median': sorted(bal_v)[len(bal_v) // 2],
                            'best_balanced_labels': bestg,
                            'n_balanced_beating_kv': sum(1 for x in bal_v if x > kv_v),
                            'contiguous_max': max(con_v),
                            'contiguous_at_kv_split': con_v[nh // 2 - 1]}
                print(f'    {key:<32}{kv_v:<10.3f}{rb:<19.4f}{rc:<20.4f}{len(bal):<8}{bestg}')
    out['tests'] = res
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r25_attack_partition.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
