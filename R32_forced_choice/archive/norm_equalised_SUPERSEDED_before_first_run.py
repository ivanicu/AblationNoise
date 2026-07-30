#!/usr/bin/env python3
"""Does anything survive when the norm route is removed BY CONSTRUCTION? Zero forwards.

R32's M2 fired: ||delta_h||_2 alone scores top1 0.6905 on the same 6-way choice that the full
directional statistic scores 0.8631. A permanent per-head magnitude replicates across item sets for
free, so the registered rule downgraded the finding to per-head SCALE.

My commit for that named the only honest continuation, and this is it:

    build candidate sets that are MATCHED ON NORM, so the scalar carries no information at all,
    and see what is left.

TWO MEASUREMENTS, both owed.

  N1  NORM-MATCHED CANDIDATE SETS. For each held-out head h, the 5 distractors are the heads --
      from ANY group -- whose ||delta|| is nearest to h's. Norm is then constant-by-construction
      across the choice, so a norm-based ranker is at chance by definition. Anything above the
      measured null is directional.
      Its own scalar baseline runs beside it and MUST come back at chance, or the matching failed.

  N2  M4's MISSING SCALAR BASELINE. R32 reported P(correct head | correct group) = 0.8693 at n=153
      as the last head-level number standing, and never ran the scalar baseline on that same
      conditional. Both the cosine ranker and the ||delta|| ranker are decomposed into
      P(correct group) and P(correct head | correct group) here, so the comparison is like for like.

═══ CONTROL FORM, applied as the standing rule now requires ═══
A control is a QUANTILE OF THE STATISTIC'S OWN MEASURED NULL over 1000 surrogate draws, with the
surrogate MATCHED FIRST to the data's variance_fraction_removed_by_block_mean (0.1468 +- 0.02).
No analytic chance level is used as a threshold anywhere in this file.

═══ REGISTERED BEFORE THE RUN ═══
  T1  N1's norm-matched top1 <= the matched null's 99.9th percentile
      ->  DIRECTIONAL_IDENTITY_DEAD. Everything reproducible about a head is its magnitude, and the
          privacy line closes on a measured negative rather than on an unpriced downgrade.
  T2  N1's norm-matched top1 > that percentile AND N1's own scalar baseline is <= it
      ->  DIRECTIONAL_IDENTITY_SURVIVES_NORM_MATCHING.
  T3  N1's scalar baseline exceeds the percentile -> the norm matching FAILED, UNVERIFIED, no world
      moves. (This is the arm that makes T1 readable: a norm-matched set where norm still works is
      not norm-matched.)
  Reported, not gated: N2's two decompositions.
  Scope unchanged: n = 1 MODEL, no 3b off400 exists, nothing here is a property of GQA.
"""
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
RANK = 5
N_NULL = 1000
RULE = {'n_draws': N_NULL, 'percentile': 99.9, 'target_frac0': 0.1468, 'frac0_tol': 0.02,
        'n_candidates': 6, 'rank': RANK}


def two_way_resid(D):
    mu = D.mean()
    return D - mu - (D.mean(1) - mu)[:, None] - (D.mean(0) - mu)[None, :]


def loadings(D, rank=RANK):
    E = two_way_resid(D)
    U, S, Vt = np.linalg.svd(E, full_matrices=False)
    E1 = E - S[0] * np.outer(U[:, 0], Vt[0])
    U2, S2, _ = np.linalg.svd(E1, full_matrices=False)
    return U2[:, :rank] * S2[:rank]


def privatise(A, blk):
    P = A.copy()
    for g in np.unique(blk):
        m = blk == g
        P[m] -= A[m].mean(0)
    return P, float(1 - (P ** 2).sum() / (A ** 2).sum())


def procrustes(X, Y):
    U, _, Vt = np.linalg.svd(Y.T @ X)
    return U @ Vt


def block_split(blk, rng):
    gs = np.unique(blk)
    gp = gs[rng.permutation(len(gs))]
    fg = set(gp[:len(gp) // 2].tolist())
    fit = np.array([i for i in range(len(blk)) if blk[i] in fg])
    hold = np.array([i for i in range(len(blk)) if blk[i] not in fg])
    return fit, hold


def norm_matched_sets(norms, blk, k=6):
    """5 distractors from ANY OTHER group whose ||delta|| is nearest to h's. Norm is then flat."""
    order = np.argsort(norms)
    rank_of = np.empty(len(norms), dtype=int)
    rank_of[order] = np.arange(len(norms))
    sets = {}
    for h in range(len(norms)):
        pool = [j for j in order if blk[j] != blk[h]]
        pool.sort(key=lambda j: abs(rank_of[j] - rank_of[h]))
        sets[h] = np.array([h] + pool[:k - 1])
    return sets


def run_choice(A0, A4, blk, rng, sets=None, scalar=None):
    """One pass. If scalar is given, rank by |scalar difference|; else by cosine of private parts."""
    P0, frac = privatise(A0, blk)
    P4, _ = privatise(A4, blk)
    fit, hold = block_split(blk, rng)
    if scalar is None:
        R = P4 @ procrustes(P0[fit], P4[fit])
        Pn = P0 / (np.linalg.norm(P0, axis=1, keepdims=True) + 1e-300)
        Rn = R / (np.linalg.norm(R, axis=1, keepdims=True) + 1e-300)
    hits = 0
    for h in hold:
        cand = sets[h] if sets is not None else np.where(blk == blk[h])[0]
        if scalar is None:
            pick = cand[int(np.argmax(Rn[cand] @ Pn[h]))]
        else:
            pick = cand[int(np.argmin(np.abs(scalar[1][cand] - scalar[0][h])))]
        hits += int(pick == h)
    return hits / len(hold), frac


def synth(rng, nh=336, per_group=6, ni=120, shared_rank=5, priv_rank=3, rel=0.9,
          priv_amp=1.0, noise=1.0):
    A_shared = np.repeat(rng.standard_normal((nh // per_group, shared_rank)), per_group, axis=0)
    Wp = rng.standard_normal((nh, priv_rank))
    out = []
    for _ in range(2):
        Wps = rel * Wp + math.sqrt(max(1 - rel ** 2, 0.0)) * rng.standard_normal((nh, priv_rank))
        out.append(A_shared @ rng.standard_normal((shared_rank, ni))
                   + priv_amp * (Wps @ rng.standard_normal((priv_rank, ni)))
                   + noise * rng.standard_normal((nh, ni)))
    return out


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'scope': 'n = 1 MODEL; no 3b off400 -> no second disjoint-item-set replicate'}
    za = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off0.npz')
    zb = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off400.npz')
    D0, D4 = za['delta'].astype(np.float64), zb['delta'].astype(np.float64)
    lay, hd = za['layer'].astype(np.int64), za['head'].astype(np.int64)
    gblk = lay * 2 + hd // 6
    A0, A4 = loadings(D0), loadings(D4)
    E0, E4 = two_way_resid(D0), two_way_resid(D4)
    n0, n4 = np.linalg.norm(E0, axis=1), np.linalg.norm(E4, axis=1)

    # ── the matched measured null, built once and reused by both arms ──
    print(f"  matching the surrogate's frac0 to the data's {RULE['target_frac0']:.4f}")
    best = None
    for nz in (8.0, 16.0, 32.0, 64.0):
        Xa, Xb = synth(rng, priv_amp=0.0, noise=nz)
        _, f = run_choice(loadings(Xa), loadings(Xb), np.repeat(np.arange(56), 6),
                          np.random.default_rng(SEED))
        if best is None or abs(f - RULE['target_frac0']) < abs(best[1] - RULE['target_frac0']):
            best = (nz, f)
    nz, fbest = best
    matched = abs(fbest - RULE['target_frac0']) <= RULE['frac0_tol']
    print(f'    chosen noise {nz}, frac0 {fbest:.4f}, matched {matched}')
    blk_s = np.repeat(np.arange(56), 6)
    nulls = []
    for _ in range(N_NULL):
        Xa, Xb = synth(rng, priv_amp=0.0, noise=nz)
        La, Lb = loadings(Xa), loadings(Xb)
        ns = norm_matched_sets(np.linalg.norm(two_way_resid(Xa), axis=1), blk_s)
        t, _ = run_choice(La, Lb, blk_s, np.random.default_rng(SEED), sets=ns)
        nulls.append(t)
    nulls = np.array(nulls)
    q = float(np.percentile(nulls, RULE['percentile']))
    out['matched_null'] = {'noise': nz, 'frac0': fbest, 'matched': bool(matched),
                           'mean': float(nulls.mean()), 'sd': float(nulls.std(ddof=1)),
                           'median': float(np.median(nulls)), 'p999': q,
                           'max': float(nulls.max()), 'n_draws': N_NULL}
    print(f"    null over {N_NULL} draws on NORM-MATCHED sets: mean {nulls.mean():.4f} "
          f"sd {nulls.std(ddof=1):.4f} median {np.median(nulls):.4f} p99.9 {q:.4f} "
          f"max {nulls.max():.4f}")

    # ── N1 ──
    print('\n  N1 — norm-matched candidate sets (5 nearest-||delta|| heads from OTHER groups)')
    sets = norm_matched_sets(n0, gblk)
    spread = np.median([np.ptp(n0[sets[h]]) / n0[h] for h in range(len(n0))])
    t_cos, _ = run_choice(A0, A4, gblk, np.random.default_rng(SEED), sets=sets)
    t_sca, _ = run_choice(A0, A4, gblk, np.random.default_rng(SEED), sets=sets, scalar=(n0, n4))
    n1 = {'top1_cosine': t_cos, 'top1_scalar_baseline': t_sca,
          'median_relative_norm_spread_within_candidate_set': float(spread),
          'cosine_clears_p999': bool(t_cos > q), 'scalar_clears_p999': bool(t_sca > q)}
    out['N1_norm_matched'] = n1
    print(f"    median relative ||delta|| spread within a candidate set: {spread:.4f}")
    print(f"    cosine          top1 {t_cos:.4f}   clears p99.9 ({q:.4f}) -> {n1['cosine_clears_p999']}")
    print(f"    scalar baseline top1 {t_sca:.4f}   clears p99.9 ({q:.4f}) -> {n1['scalar_clears_p999']}"
          f"   (MUST be False, or the matching failed)")

    # ── N2: M4's missing scalar baseline, like for like ──
    print('\n  N2 — layer 12-way decomposition, cosine AND scalar, the comparison R32 omitted')
    P0, _ = privatise(A0, lay)
    P4, _ = privatise(A4, lay)
    fit, hold = block_split(lay, np.random.default_rng(SEED))
    R = P4 @ procrustes(P0[fit], P4[fit])
    Pn = P0 / (np.linalg.norm(P0, axis=1, keepdims=True) + 1e-300)
    Rn = R / (np.linalg.norm(R, axis=1, keepdims=True) + 1e-300)
    n2 = {}
    for name in ('cosine', 'scalar_norm'):
        ha = hg = hh = ng = 0
        for h in hold:
            cand = np.where(lay == lay[h])[0]
            pick = (cand[int(np.argmax(Rn[cand] @ Pn[h]))] if name == 'cosine'
                    else cand[int(np.argmin(np.abs(n4[cand] - n0[h])))])
            ha += int(pick == h)
            same = (hd[pick] // 6) == (hd[h] // 6)
            hg += int(same)
            if same:
                ng += 1
                hh += int(pick == h)
        n2[name] = {'top1_12way': ha / len(hold), 'p_correct_group': hg / len(hold),
                    'p_correct_head_given_group': hh / ng if ng else float('nan'),
                    'n_given': ng}
        v = n2[name]
        print(f"    {name:<12} top1 {v['top1_12way']:.4f}   P(group) {v['p_correct_group']:.4f}"
              f"   P(head|group) {v['p_correct_head_given_group']:.4f}  n={ng}")
    out['N2_layer_decomposition'] = n2

    verdict = ('UNVERIFIED_SURROGATE_UNMATCHED' if not matched
               else 'UNVERIFIED_NORM_MATCHING_FAILED' if n1['scalar_clears_p999']
               else 'DIRECTIONAL_IDENTITY_SURVIVES_NORM_MATCHING' if n1['cosine_clears_p999']
               else 'DIRECTIONAL_IDENTITY_DEAD')
    out['verdict'] = verdict
    print(f'\n  VERDICT  {verdict}')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r32_norm_equalised.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
