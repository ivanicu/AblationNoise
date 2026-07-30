#!/usr/bin/env python3
"""Can a head be identified among its own KV group-mates, from a DIFFERENT item set? Zero forwards.

Every privacy statistic in this programme so far has been a pooled correlation, and every one of them
has been demolished the same way: a surrogate with no private rule reproduces it. R30's +0.9559 was
matched at +0.9556 by i.i.d. loadings. R31's rho_priv +0.9402 turned out to be mostly the +0.9649
that was already there before any group mean was removed -- group-mean removal deletes only 14.7% of
the loading energy, layer-mean 8.0%, so the +0.9402 / +0.9406 "agreement" between them prices nothing.

A forced choice cannot be reproduced that way, because it removes by CONSTRUCTION the thing that
carried the pooled statistics:

    for each held-out head h, rank h's OWN off400 private vector against its 5 GROUP-MATES

All six candidates carry the identical group mean, so the shared term cancels in the ranking rather
than being subtracted and hoped about. All six live in the same layer and the same KV group, so
layer identity and group identity are held exactly fixed. And it is a per-head statistic, so it
cannot be carried by a handful of high-norm heads the way a pooled correlation can.

═══ METHOD ═══
  A^(s) = U.S[:5] of the rank-1-stripped two-way residual, 336 x 5, head-indexed
  P^(s) = A^(s) - mean over each head's own KV group
  Omega = orthogonal Procrustes, fit ONCE on a random half of heads with the TRUE pairing
          (R31 refit Omega inside every null draw, so its null destroyed identity AND rotation
           estimability jointly -- a confounded null. Fitting once removes that confound.)
  score = for each HELD-OUT head h: argmax over h's 6 group members m of cos(P0_h, (P4 . Omega)_m)
  top1  = fraction where the argmax is h itself.  CHANCE = 1/6 = 0.16667, exact binomial. No
          permutation null is needed or used.

═══ REGISTERED BEFORE THE RUN. Not amended after any number is seen. ═══
  T1  top1 < 0.30                       ->  PRIVACY_DEAD. Head-private identity beyond the KV group
                                            is dead, WB collapses into WD, this line closes.
  T2  top1 >= 0.30 AND both controls pass ->  PRIVACY_REAL.
  C1  GATE, priv_amp = 0 (no private rule at all): top1 must land INSIDE [0.11, 0.23].
  C2  GATE, rel = 0.9 (strong private rule):       top1 must EXCEED 0.60.
  Either control outside its band -> UNVERIFIED, no world moves.
  (Chance 0.16667; the binomial 95% upper bound at n=168 is 0.214, so T1 = 0.30 carries real margin.)

═══ REPORTED, NOT GATED ═══
  - layer-block 12-way forced choice, chance 1/12 = 0.08333: the group-vs-layer price that R31's
    vacuous 3-decimal tie failed to deliver
  - mean reciprocal rank beside top-1
  - the variance fraction each block-mean removes, so no future round reads a tie as meaningful
  - a GROUP-LEVEL split companion, where whole KV groups are held out so that no candidate was ever
    seen while fitting Omega. The navigator specified a head-level split; this is strictly cleaner
    and is reported beside it rather than replacing it.

═══ SCOPE, FIXED IN ADVANCE ═══
There is no 3b off400 on disk, so there is NO disjoint-item-set replicate for the second model. Every
privacy claim from this line is n = 1 MODEL and may not be stated as a property of Qwen2.5 or of GQA.
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
RULE = {'T1_dead_below': 0.30, 'C1_noprivate_band': [0.11, 0.23], 'C2_strong_private_min': 0.60,
        'chance_group': 1 / 6, 'chance_layer': 1 / 12, 'rank': RANK}


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


def forced_choice(A0, A4, blk, rng, split='head'):
    """Fit Omega once on a random half with the TRUE pairing; score only held-out heads."""
    P0, frac0 = privatise(A0, blk)
    P4, _ = privatise(A4, blk)
    n = A0.shape[0]
    if split == 'head':
        idx = rng.permutation(n)
        fit, hold = idx[:n // 2], idx[n // 2:]
    else:                                      # hold out WHOLE blocks: no candidate seen in the fit
        gs = np.unique(blk)
        gp = gs[rng.permutation(len(gs))]
        fg = set(gp[:len(gp) // 2].tolist())
        fit = np.array([i for i in range(n) if blk[i] in fg])
        hold = np.array([i for i in range(n) if blk[i] not in fg])
    Om = procrustes(P0[fit], P4[fit])
    R = P4 @ Om
    Pn = P0 / (np.linalg.norm(P0, axis=1, keepdims=True) + 1e-300)
    Rn = R / (np.linalg.norm(R, axis=1, keepdims=True) + 1e-300)
    hits, ranks = 0, []
    for h in hold:
        cand = np.where(blk == blk[h])[0]
        sims = Rn[cand] @ Pn[h]
        order = cand[np.argsort(-sims)]
        pos = int(np.where(order == h)[0][0])
        ranks.append(1.0 / (pos + 1))
        hits += int(pos == 0)
    return {'top1': hits / len(hold), 'mrr': float(np.mean(ranks)), 'n_scored': int(len(hold)),
            'n_candidates_per_choice': int(np.median([(blk == blk[h]).sum() for h in hold])),
            'variance_fraction_removed_by_block_mean': frac0}


def synth(rng, nh=336, ni=120, per_group=6, shared_rank=5, priv_rank=3, rel=0.9,
          priv_amp=1.0, noise=1.0):
    ng = nh // per_group
    A_shared = np.repeat(rng.standard_normal((ng, shared_rank)), per_group, axis=0)
    Wp = rng.standard_normal((nh, priv_rank))
    out = []
    for _ in range(2):
        Wps = rel * Wp + math.sqrt(max(1 - rel ** 2, 0.0)) * rng.standard_normal((nh, priv_rank))
        out.append(A_shared @ rng.standard_normal((shared_rank, ni))
                   + priv_amp * (Wps @ rng.standard_normal((priv_rank, ni)))
                   + noise * rng.standard_normal((nh, ni)))
    return out


def binom_p(k, n, p):
    """Exact one-sided P(X >= k). No permutation null: the chance level is known by construction."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'scope': "no 3b off400 on disk -> no disjoint-item-set replicate for the second model; "
                    "every privacy claim from this line is n=1 MODEL, not a property of GQA"}
    blk_s = np.repeat(np.arange(56), 6)

    print('  C1 GATE — priv_amp = 0, no private rule at all. Must land inside [0.11, 0.23]')
    Xa, Xb = synth(rng, priv_amp=0.0)
    c1 = forced_choice(loadings(Xa), loadings(Xb), blk_s, np.random.default_rng(SEED))
    lo, hi = RULE['C1_noprivate_band']
    c1['passes'] = bool(lo <= c1['top1'] <= hi)
    print(f"    top1 {c1['top1']:.4f}  mrr {c1['mrr']:.4f}  n {c1['n_scored']}  -> {c1['passes']}")

    print('  C2 GATE — rel = 0.9, strong private rule. Must exceed 0.60')
    Xa, Xb = synth(rng, priv_amp=1.0, rel=0.9)
    c2 = forced_choice(loadings(Xa), loadings(Xb), blk_s, np.random.default_rng(SEED))
    c2['passes'] = bool(c2['top1'] > RULE['C2_strong_private_min'])
    print(f"    top1 {c2['top1']:.4f}  mrr {c2['mrr']:.4f}  n {c2['n_scored']}  -> {c2['passes']}")
    out['C1_no_private'], out['C2_strong_private'] = c1, c2
    gate = c1['passes'] and c2['passes']
    out['gate_passed'] = bool(gate)
    print(f"  GATE: {'PASSES' if gate else 'FAILS; ALL BELOW UNVERIFIED'}")

    print('\n  OBSERVED — qwen2.5-1.5b, off0 vs off400, 0 of 120 items in common')
    za = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off0.npz')
    zb = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off400.npz')
    A0, A4 = loadings(za['delta'].astype(np.float64)), loadings(zb['delta'].astype(np.float64))
    lay, hd = za['layer'].astype(np.int64), za['head'].astype(np.int64)
    gblk, lblk = lay * 2 + hd // 6, lay
    res = {}
    for name, blk, chance, sp in (('kv_group_6way', gblk, RULE['chance_group'], 'head'),
                                  ('kv_group_6way_GROUPSPLIT', gblk, RULE['chance_group'], 'block'),
                                  ('layer_12way', lblk, RULE['chance_layer'], 'head')):
        r = forced_choice(A0, A4, blk, np.random.default_rng(SEED), split=sp)
        k = int(round(r['top1'] * r['n_scored']))
        r['chance'] = chance
        r['lift_over_chance'] = r['top1'] / chance
        r['binomial_p_one_sided'] = binom_p(k, r['n_scored'], chance)
        res[name] = r
        print(f"    {name:<26} top1 {r['top1']:.4f}  chance {chance:.4f}  lift "
              f"{r['lift_over_chance']:.2f}x  mrr {r['mrr']:.4f}  n {r['n_scored']}  "
              f"p {r['binomial_p_one_sided']:.3e}   var removed {r['variance_fraction_removed_by_block_mean']:.4f}")
    out['observed'] = res

    t1 = res['kv_group_6way']['top1']
    verdict = ('UNVERIFIED_GATE_FAILED' if not gate
               else 'PRIVACY_DEAD' if t1 < RULE['T1_dead_below'] else 'PRIVACY_REAL')
    out['verdict'] = verdict
    print(f"\n  registered T1: top1 {t1:.4f} vs kill at {RULE['T1_dead_below']}  ->  {verdict}")

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r32_who_am_i.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
