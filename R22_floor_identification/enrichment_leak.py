#!/usr/bin/env python3
"""Does the central null's reference pool contain the set it is the null FOR? Yes -- by how much?

Registered in R22_floor_identification/ENRICHMENT_LEAK_PREREGISTRATION.md, with the DIRECTION
predicted before the run: p must INCREASE, because the eight are below the null median.

Positive control: with the eight left in the pool this must reproduce headline.set_enrichment()'s
published p_distinct_per_layer exactly, same seeds, same construction. Otherwise it is not the
published test.
"""
import collections, json, math, pathlib, random, sys
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
import headline as H                                                     # noqa: E402

N = 50000
N_CTRL = 2000
CTRL_SEED = 20260729
PUB = {'I_final': 0.8069038619227615, 'I_all': 0.6916861662766745}


def main():
    A = json.load(open(REPO / 'R18_all_positions' / 'results' / 'r18_allpos_qwen2.5-1.5b.json'))
    B = json.load(open(REPO / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'))
    LA = {int(k): v for k, v in A['layers'].items()}
    LB = {int(k): v for k, v in B['layers'].items()}
    NH = len(LA[0]['per_head'])
    band = [(x, h) for x in range(14, 28) for h in range(NH)]
    pe = H.r1_prior_effects()
    eight = sorted((int(k[1:k.index('H')]), int(k[k.index('H') + 1:])) for k in pe['effects'])
    eight = [k for k in eight if 14 <= k[0] < 28]
    cnt = collections.Counter(k[0] for k in eight)
    out = {'n_eight_in_band': len(eight), 'layer_multiset': dict(cnt),
           'expected_overlap': sum(c * c / NH for c in cnt.values())}

    def run(L, seed, excl):
        v = {k: L[k[0]]['per_head'][str(k[1])] for k in band}
        mu = sum(v.values()) / len(v)          # mu is NOT changed: only the POOL is under test
        pool = {}
        for k in band:
            if k not in excl:
                pool.setdefault(k[0], []).append(k)
        T = lambda st: sum(abs(v[k] - mu) for k in st) / len(st)
        rng = random.Random(seed)
        nl = sorted(T([x for lay, c in cnt.items() for x in rng.sample(pool[lay], c)])
                    for _ in range(N))
        t = T(eight)
        # THE PUBLISHED p USES (1 + count) / (1 + N), NOT count / N. My first version used the
        # latter and the positive control caught it instantly: 0.8069 against a published
        # 0.8069038619227615, which is exactly 40346/50001. A p quantised to 1/50000 cannot equal a
        # number that is not a multiple of it, and the control said so before any conclusion was
        # read. The +1 is the standard add-one bound on a permutation p.
        p = (1 + sum(1 for z in nl if z >= t)) / (1 + N)
        return {'T_pub': t, 'null_median': nl[N // 2], 'p': p}

    res = {}
    for tag, L, seed in (('I_final', LB, 19), ('I_all', LA, 20)):
        keep = run(L, seed, set())
        drop = run(L, seed, set(eight))
        ok = abs(keep['p'] - PUB[tag]) < 1e-12
        res[tag] = {'with_the_eight_in_pool': keep, 'with_them_removed': drop,
                    'delta_p': drop['p'] - keep['p'], 'published_p': PUB[tag],
                    'positive_control_reproduces_published': ok}
        print(f'  [{tag:7s}] CONTROL reproduces published {keep["p"]!r} vs {PUB[tag]!r} '
              f'-> {"PASS" if ok else "FAIL"}')
        print(f'            null median {keep["null_median"]:.6f} -> {drop["null_median"]:.6f}   '
              f'p {keep["p"]:.6f} -> {drop["p"]:.6f}   delta {drop["p"] - keep["p"]:+.6f}')

    out['arms'] = res
    if not all(r['positive_control_reproduces_published'] for r in res.values()):
        out['verdict'] = 'UNVERIFIED_CONTROL_FAILED'
        print('\n  -> UNVERIFIED: this is not the published test. Not an acquittal.')
        json.dump(out, open(HERE / 'results' / 'r22_enrichment_leak.json', 'w'), indent=1)
        return 3

    # ---- confound control: remove EIGHT RANDOM band heads with the same layer multiset
    rc = random.Random(CTRL_SEED)
    ctrl = {}
    for tag, L, seed in (('I_final', LB, 19), ('I_all', LA, 20)):
        base = res[tag]['with_the_eight_in_pool']['p']
        d = []
        for _ in range(N_CTRL):
            pick = set()
            for lay, c in cnt.items():
                pick |= set(rc.sample([(lay, h) for h in range(NH)], c))
            d.append(run(L, seed, pick)['p'] - base)
        d.sort()
        obs = res[tag]['delta_p']
        ctrl[tag] = {'n': N_CTRL, 'median': d[N_CTRL // 2], 'p05': d[int(0.05 * N_CTRL)],
                     'p95': d[int(0.95 * N_CTRL)],
                     'percentile_of_observed': sum(1 for z in d if z < obs) / N_CTRL}
        print(f'  [{tag:7s}] matched-multiset removal null: median {d[N_CTRL // 2]:+.6f}  '
              f'p95 {d[int(0.95 * N_CTRL)]:+.6f}  observed at percentile '
              f'{ctrl[tag]["percentile_of_observed"]:.4f}')
    out['matched_removal_null'] = ctrl

    deltas = [r['delta_p'] for r in res.values()]
    verdict = ('DIRECTION-WRONG' if any(d < 0 for d in deltas) else
               'LEAK-MATERIAL' if any(abs(d) >= 0.10 for d in deltas) else 'LEAK-IMMATERIAL')
    out['verdict'] = verdict
    print(f'\n  REGISTERED VERDICT: {verdict}   (predicted: p INCREASES in both arms)')
    op = HERE / 'results' / 'r22_enrichment_leak.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
