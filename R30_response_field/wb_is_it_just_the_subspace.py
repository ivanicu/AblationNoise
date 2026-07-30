#!/usr/bin/env python3
"""The attack on my own WB result, run before anyone asks me to. Zero forwards.

I committed 06f40a4 reading a cross-item-set replicate of +0.9559 as "head-private selectivity is a
reproducible property of heads". The statistic was built on the residual after stripping ONLY RANK 1.
But the same commit's rank sweep says the shared object is at least rank 5 -- excess(5)/excess(1) =
4.676 and 4.960. So the residual I correlated STILL CONTAINS RANKS 2..5 OF THE SHARED FIELD, and a
head's loadings on those directions are head-specific and would replicate across item sets for a
reason that has nothing to do with private selectivity.

    If the truth is "one shared rank-5 field, head-specific loadings, nothing else", my L1 returns
    ~0.95 anyway. The instrument as run CANNOT distinguish that from WB.

So the number is real and the READING may not be. This file measures which.

═══ THE MEASUREMENT ═══
Replicate statistic as a function of how many leading directions are stripped, k = 0..12. If the
0.9559 is the shared subspace, it must COLLAPSE to the head-identity null once k passes the shared
rank. If private selectivity is real, it must survive past it.

═══ THE GATE, AND IT IS THE POINT OF THE FILE ═══
A synthetic NULL ARM with a shared rank-5 field and NO private rule whatsoever:
    X_s = W @ V_s + iid noise          W shared across sets, V_s drawn fresh per item set
The statistic MUST fall inside the null band once k >= 5 on this arm. If it does not, the instrument
cannot separate the two worlds at any k and EVERYTHING BELOW IS UNVERIFIED. This is the arm the
previous file's L3 control lacked: L3 injected a private profile and showed the statistic RISES with
it; it never showed the statistic FALLS when there is none beyond a shared field.

═══ REGISTERED BEFORE THE RUN ═══
  G1  GATE. On the synthetic shared-only arm, replicate(k=8) must be inside that arm's own
      head-identity null p95. If not -> UNVERIFIED, no world moves.
  G2  If observed replicate(k=8) is inside the observed head-identity null p95
      ->  WB_IS_THE_SUBSPACE. The 0.9559 was ranks 2..5 of one shared field; the reading in
          06f40a4 is retracted and the object is a shared low-rank field with head-specific loadings.
  G3  If observed replicate(k=12) exceeds 3x the observed null p95
      ->  WB_SURVIVES_BEYOND_THE_SUBSPACE. Private selectivity is real past the shared field.
  Neither -> UNVERIFIED_PARTIAL. No amendment after any number is seen.
"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
N_NULL = 200
KMAX = 12
RULE = {'G1_gate_k': 8, 'G2_wb_is_subspace_if_inside_p95_at_k': 8,
        'G3_survives_if_ratio_over_p95_at_k12_atleast': 3.0, 'n_null': N_NULL}


def two_way_resid(D):
    mu = D.mean()
    return D - mu - (D.mean(1) - mu)[:, None] - (D.mean(0) - mu)[None, :]


def strip_k(E, k):
    if k <= 0:
        return E
    U, S, Vt = np.linalg.svd(E, full_matrices=False)
    return E - (U[:, :k] * S[:k]) @ Vt[:k]


def rowcorr(R):
    Z = R - R.mean(1, keepdims=True)
    Z /= np.linalg.norm(Z, axis=1, keepdims=True) + 1e-300
    return Z @ Z.T


def offdiag(C):
    return C[~np.eye(C.shape[0], dtype=bool)]


def within_layer_perm(lay, rng):
    p = np.arange(len(lay))
    for L in np.unique(lay):
        i = np.where(lay == L)[0]
        p[i] = i[rng.permutation(len(i))]
    return p


def sweep(Da, Db, lay, rng, kmax=KMAX, n_null=N_NULL):
    Ea, Eb = two_way_resid(Da), two_way_resid(Db)
    rows = {}
    for k in range(kmax + 1):
        Ca, Cb = rowcorr(strip_k(Ea, k)), rowcorr(strip_k(Eb, k))
        oa, ob = offdiag(Ca), offdiag(Cb)
        obs = float(np.corrcoef(oa, ob)[0, 1])
        nl = [float(np.corrcoef(oa, offdiag(Cb[np.ix_(p, p)]))[0, 1])
              for p in (within_layer_perm(lay, rng) for _ in range(n_null))]
        p95 = float(np.percentile(nl, 95))
        rows[f'k{k}'] = {'replicate': obs, 'null_median': float(np.median(nl)), 'null_p95': p95,
                         'inside_null_p95': bool(obs <= p95),
                         'over_p95': obs / p95 if p95 > 0 else float('inf')}
    return rows


def show(tag, rows):
    print(f'    {tag}')
    print(f"      {'k':<4}{'replicate':<13}{'null med':<12}{'null p95':<12}"
          f"{'obs/p95':<10}inside")
    for k in range(KMAX + 1):
        v = rows[f'k{k}']
        print(f"      {k:<4}{v['replicate']:<+13.4f}{v['null_median']:<+12.4f}"
              f"{v['null_p95']:<+12.4f}{v['over_p95']:<10.2f}{v['inside_null_p95']}")


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'question': "Is the +0.9559 cross-item-set replicate head-PRIVATE selectivity, or is it "
                       "ranks 2..5 of ONE shared field that my rank-1 strip failed to remove?"}

    # ── G1 GATE: synthetic shared rank-5 field, NO private rule beyond shared loadings ──
    print('  G1 GATE — synthetic arm: ONE shared rank-5 field, no private rule, disjoint item sets')
    nh, ni, r = 336, 120, 5
    lay_s = np.repeat(np.arange(28), 12)
    W = rng.standard_normal((nh, r))
    Xs = []
    for _ in range(2):
        V = rng.standard_normal((r, ni))          # item basis drawn FRESH per set, as disjoint sets are
        Xs.append(W @ V + 1.0 * rng.standard_normal((nh, ni)))
    g1 = sweep(Xs[0], Xs[1], lay_s, rng, n_null=100)
    show('shared-rank5-only', g1)
    gate = g1[f"k{RULE['G1_gate_k']}"]['inside_null_p95']
    out['G1_shared_only_arm'] = g1
    out['G1_passed'] = bool(gate)
    print(f"      GATE: replicate(k={RULE['G1_gate_k']}) inside its own null p95 -> {gate}"
          f"   {'INSTRUMENT SEPARATES' if gate else 'INSTRUMENT CANNOT SEPARATE; ALL BELOW UNVERIFIED'}")

    # ── the observed pair: the only disjoint-item-set replicate on disk ──
    print('\n  OBSERVED — qwen2.5-1.5b, off0 vs off400, 0 of 120 items in common')
    za = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off0.npz')
    zb = np.load(REPO / 'R29_cancellation' / 'results' / 'r29_vectors_qwen2.5-1.5b_I_final_off400.npz')
    obs = sweep(za['delta'].astype(np.float64), zb['delta'].astype(np.float64),
                za['layer'], rng)
    show('off0 vs off400', obs)
    out['observed'] = obs

    k8 = obs[f"k{RULE['G2_wb_is_subspace_if_inside_p95_at_k']}"]
    k12 = obs[f'k{KMAX}']
    if not gate:
        verdict = 'UNVERIFIED_GATE_FAILED'
    elif k8['inside_null_p95']:
        verdict = 'WB_IS_THE_SUBSPACE'
    elif k12['over_p95'] >= RULE['G3_survives_if_ratio_over_p95_at_k12_atleast']:
        verdict = 'WB_SURVIVES_BEYOND_THE_SUBSPACE'
    else:
        verdict = 'UNVERIFIED_PARTIAL'
    out['verdict'] = verdict
    print(f"\n  k=8  replicate {k8['replicate']:+.4f}  null p95 {k8['null_p95']:+.4f}  "
          f"inside {k8['inside_null_p95']}")
    print(f"  k=12 replicate {k12['replicate']:+.4f}  null p95 {k12['null_p95']:+.4f}  "
          f"obs/p95 {k12['over_p95']:.2f}")
    print(f"  VERDICT  {verdict}")

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r30_wb_subspace_attack.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
