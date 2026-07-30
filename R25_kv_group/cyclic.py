#!/usr/bin/env python3
"""The shape-matched confound pool, per AMENDMENT_1, plus every figure that amendment took on trust.

`attack_partition.py`'s contiguous pool had exactly ONE shape-matched member and it was the KV
partition itself, so contiguity and KV grouping were perfectly collinear inside it. The replacement is
the cyclic-block pool: n/2 contiguous heads on the ring, 6 partitions for n=12 and 8 for n=16. Every
member is shape-matched AND contiguous, so the pool asks WHICH contiguous half rather than WHETHER the
split is contiguous -- the only version of the question that can separate the two explanations.

SIX FIGURES IN THAT AMENDMENT ARE THE REVIEWER'S, MEASURED WITH ITS OWN IMPLEMENTATION. This file
reproduces every one of them. A number taken on trust from another agent is the thing this repository
refuses everywhere else, and twelve agents agreeing is one hallucination twelve times.

The joint null permutes head labels within each (model, layer) and applies THE SAME permutation to
both supports, because the two supports are not independent -- they correlate about 0.5 and are
bit-identical at the last layer of both models. Treating them as independent would understate the
joint base rate, i.e. would flatter the finding.
"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import icc as I                                                          # noqa: E402

SEED = 20260729
N_JOINT = 40000
N_CELL = 20000
N_CELL_BIG = 2000            # pools of 6435: the rate is 1/|pool| and 2000 draws resolve 1.6e-4
PRIMARY = 'abs'                     # named in AMENDMENT_1, chosen post hoc, penalty paid at 8 cells


def cyclic_blocks(n):
    """The reviewer's pool, verbatim: 6 partitions for n=12, 8 for n=16."""
    seen = {}
    for st in range(n):
        c = {(st + j) % n for j in range(n // 2)}
        lab = tuple(1 if i in c else 0 for i in range(n))
        seen[lab if lab[0] == 1 else tuple(1 - x for x in lab)] = st
    return [list(l) for l in seen]


def eta_rows(E, g):
    """eta squared per row of E (layers x heads) for one label vector. Vectorised."""
    g = np.asarray(g)
    gm = E.mean(1, keepdims=True)
    tot = ((E - gm) ** 2).sum(1)
    btw = np.zeros(E.shape[0])
    for lab in np.unique(g):
        m = g == lab
        btw += m.sum() * (E[:, m].mean(1) - gm[:, 0]) ** 2
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(tot > 0, btw / tot, np.nan)


def pool_sums(E, pool):
    """Sum of eta squared over layers, one value per partition in the pool."""
    return np.array([np.nansum(eta_rows(E, g)) for g in pool])


def load_matrix(model, support, absolute):
    prof = I.load(model, support, absolute)
    return np.array(prof, dtype=np.float64) if prof is not None else None


def permute_rows(E, rng):
    """Independent within-row permutation. Returns a permuted copy."""
    idx = np.argsort(rng.random(E.shape), axis=1)
    return np.take_along_axis(E, idx, axis=1), idx


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'n_joint_draws': N_JOINT, 'n_cell_draws': N_CELL,
           'primary_transform': PRIMARY,
           'primary_chosen_post_hoc': True,
           'honest_family_size': 8}

    cells = {}
    for model, cfg in I.GQA.items():
        nh = cfg['n_heads']
        kv = I.groups(nh, cfg['n_kv'])
        pool = cyclic_blocks(nh)
        bal = None
        for support in ('I_final', 'I_all'):
            for absolute in (True, False):
                E = load_matrix(model, support, absolute)
                if E is None:
                    continue
                cells[f'{model}|{support}|{"abs" if absolute else "signed"}'] = {
                    'E': E, 'kv': kv, 'pool': pool, 'n_heads': nh, 'model': model,
                    'support': support, 'transform': 'abs' if absolute else 'signed'}
        del bal

    # ---------- 1. the cyclic-pool rank, the replacement control ----------
    print(f'  CYCLIC POOL, shape-matched: {len(cyclic_blocks(12))} partitions at n=12, '
          f'{len(cyclic_blocks(16))} at n=16')
    print(f'    {"cell":<34}{"kv sum":<10}{"pool max":<11}{"argmax?":<10}{"floor":<9}rank',
          flush=True)
    rows = {}
    for k, c in cells.items():
        ps = pool_sums(c['E'], c['pool'])
        kvv = np.nansum(eta_rows(c['E'], c['kv']))
        is_arg = bool(kvv >= ps.max() - 1e-12)
        rank = float((ps <= kvv).sum() / len(ps))
        rows[k] = {'kv_sum_eta_sq': float(kvv), 'pool_max': float(ps.max()),
                   'pool_size': len(c['pool']), 'is_argmax': is_arg, 'rank': rank,
                   'per_cell_floor': 1.0 / len(c['pool'])}
        print(f'    {k:<34}{kvv:<10.3f}{ps.max():<11.3f}{str(is_arg):<10}'
              f'{1.0 / len(c["pool"]):<9.4f}{rank:.4f}', flush=True)
    out['cyclic_pool'] = rows

    prim = [k for k in rows if k.endswith('|' + PRIMARY)]
    n_arg = sum(1 for k in prim if rows[k]['is_argmax'])
    out['registered_rule'] = {
        'rule': f'KV is the argmax of the cyclic pool in all four {PRIMARY} cells',
        'n_argmax': n_arg, 'n_cells': len(prim), 'satisfied': n_arg == len(prim),
        'cells_failing': [k for k in prim if not rows[k]['is_argmax']]}
    print(f"\n    registered rule -- argmax in all {len(prim)} {PRIMARY} cells: "
          f"{n_arg} of {len(prim)}  -> {'SATISFIED' if n_arg == len(prim) else 'NOT SATISFIED'}")
    for k in out['registered_rule']['cells_failing']:
        c = cells[k]
        ps = pool_sums(c['E'], c['pool'])
        w = c['pool'][int(np.argmax(ps))]
        print(f"      {k} loses to {''.join(str(x) for x in w)}")
        out['cyclic_pool'][k]['winning_partition'] = ''.join(str(x) for x in w)

    # ---------- 2. the joint base rate, both pools, dependence preserved ----------
    # the header said "both pools" while only the cyclic pool is swept here; three variables existed
    # to hold a balanced-pool joint rate, were never incremented, and were deleted before use. The
    # balanced pool's joint rate is not computed -- said plainly rather than implied by dead names.
    print(f'\n  JOINT BASE RATE for the CYCLIC pool only, {N_JOINT} draws, one permutation per '
          f'(model, layer) shared across BOTH supports')
    hit_cyc_prim = hit_cyc_all8 = 0
    per_model = {m: [k for k in cells if cells[k]['model'] == m] for m in I.GQA}
    for _ in range(N_JOINT):
        argm = {}
        for m, keys in per_model.items():
            if not keys:
                continue
            E0 = cells[keys[0]]['E']
            idx = np.argsort(rng.random(E0.shape), axis=1)
            for k in keys:
                c = cells[k]
                Ep = np.take_along_axis(c['E'], idx, axis=1)
                ps = pool_sums(Ep, c['pool'])
                kvv = np.nansum(eta_rows(Ep, c['kv']))
                argm[k] = bool(kvv >= ps.max() - 1e-12)
        pr = [k for k in argm if k.endswith('|' + PRIMARY)]
        sg = [k for k in argm if not k.endswith('|' + PRIMARY)]
        a_pr = all(argm[k] for k in pr) if pr else False
        a_sg = all(argm[k] for k in sg) if sg else False
        hit_cyc_prim += a_pr
        hit_cyc_all8 += (a_pr or a_sg)
    out['joint_base_rate'] = {
        'cyclic_all_four_primary': hit_cyc_prim / N_JOINT,
        'cyclic_either_transform_all_four': hit_cyc_all8 / N_JOINT,
        'n_draws': N_JOINT}
    print(f"    P(KV argmax of cyclic pool in all four {PRIMARY} cells)      "
          f"{hit_cyc_prim / N_JOINT:.5f}")
    print(f"    P(same for EITHER transform -- pays the post-hoc choice)   "
          f"{hit_cyc_all8 / N_JOINT:.5f}", flush=True)

    # ---------- 3. P(KV = argmax of the BALANCED pool), against the analytic 1/462 ----------
    print(f'\n  P(KV = argmax of the balanced pool), {N_CELL} draws vs analytic 1/n_pool')
    import itertools

    def balanced(n):
        half = n // 2
        return [[0 if i in set(c) else 1 for i in range(n)]
                for c in itertools.combinations(range(n), half) if 0 in set(c)]

    bal_rate = {}
    for k, c in cells.items():
        pool = balanced(c['n_heads'])
        # UNDER EXCHANGEABILITY THIS RATE IS A PROPERTY OF THE POOL, NOT OF THE DATA: a within-layer
        # permutation makes every shape-matched partition equally likely to win, so P(KV = argmax) is
        # 1/|pool|. That is the claim being checked, so it is checked at full resolution where it is
        # cheap (462) and at reduced resolution where it is not (6435 partitions x 36 layers).
        nd = N_CELL if len(pool) < 1000 else N_CELL_BIG
        hits = 0
        for _ in range(nd):
            Ep, _ = permute_rows(c['E'], rng)
            ps = pool_sums(Ep, pool)
            kvv = np.nansum(eta_rows(Ep, c['kv']))
            hits += bool(kvv >= ps.max() - 1e-12)
        bal_rate[k] = {'measured': hits / nd, 'analytic': 1.0 / len(pool),
                       'pool_size': len(pool), 'n_draws': nd}
        print(f'    {k:<34} measured {hits / nd:.5f}   analytic {1.0 / len(pool):.5f}   '
              f'({nd} draws, pool {len(pool)})', flush=True)
    out['balanced_argmax_base_rate'] = bal_rate

    # ---------- 4. is it "where the biggest head sits"? two independent kills ----------
    print('\n  DROP EACH LAYER\'S TOP HEAD, and a WITHIN-LAYER RANK TRANSFORM')
    robust = {}
    for k, c in cells.items():
        E, kv = c['E'], np.asarray(c['kv'])
        # drop the top-|effect| head of every layer; group sizes go unequal, eta2 handles it
        drop_eta, drop_null = [], []
        keep = np.ones(E.shape, dtype=bool)
        keep[np.arange(E.shape[0]), np.argmax(np.abs(E), axis=1)] = False
        obs = 0.0
        for r in range(E.shape[0]):
            v, g = E[r][keep[r]], kv[keep[r]]
            e = eta_rows(v[None, :], g)[0]
            if e == e:
                obs += e
        hits = 0
        for _ in range(4000):
            s = 0.0
            for r in range(E.shape[0]):
                v = E[r][keep[r]]
                g = kv[keep[r]][rng.permutation(v.size)]
                e = eta_rows(v[None, :], g)[0]
                if e == e:
                    s += e
            hits += (s >= obs)
        p_drop = (1 + hits) / 4001
        # within-layer rank transform: destroys magnitudes, keeps the ordering
        R = np.argsort(np.argsort(E, axis=1), axis=1).astype(float)
        obs_r = np.nansum(eta_rows(R, kv))
        hr = 0
        for _ in range(4000):
            Rp, _ = permute_rows(R, rng)
            hr += (np.nansum(eta_rows(Rp, kv)) >= obs_r)
        p_rank = (1 + hr) / 4001
        robust[k] = {'p_drop_top_head': p_drop, 'p_rank_transform': p_rank,
                     'sum_eta_sq_drop_top': obs, 'sum_eta_sq_rank': float(obs_r)}
        print(f'    {k:<34} p(drop top head) {p_drop:.4f}   p(rank transform) {p_rank:.4f}',
              flush=True)
    out['robustness'] = robust

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r25_cyclic.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
