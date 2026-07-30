#!/usr/bin/env python3
"""Does INDIVIDUAL head identity exist above KV-GROUP identity? Zero forwards.

R30 ended with WB withdrawn. The cross-item-set replicate of +0.9559 is reproduced exactly by a
surrogate carrying NO private rule -- one shared low-rank field with i.i.d. head loadings held fixed
across item sets returns +0.9556. So that statistic established only this much:

    HEAD LOADINGS ARE STABLE ACROSS DISJOINT ITEM SETS.

"Stable loadings" is not "private selectivity". A head's loading vector could be entirely a property
of its KV GROUP -- same k_g, v_g, 6 query heads reading one substrate -- in which case the object is
one global field whose loadings are a group-level quantity and individual head identity buys nothing.

This file asks the only question that separates them, and it is the last one the data on disk can
answer without a forward pass.

═══ THE OBJECT ═══
  A^(s)   336 x 5   = U . S[:5] of the rank-1-stripped two-way residual of cell s
Loadings are indexed by HEAD, so they are comparable across disjoint item sets up to a 5x5 orthogonal
rotation -- the item bases differ, the head axis does not.

═══ THE STATISTIC ═══
  1  Procrustes rotation Omega fit on a RANDOM HALF of the 336 head-cells
  2  scored ONLY on the held-out half -- fitting and scoring on the same heads is circular
  3  private part   P^(s)_h = A^(s)_h - mean over the heads of h's OWN KV GROUP
       1.5b: 12 query heads / 2 KV -> 6 per group -> 56 groups of 6
       3b:   16 query heads / 2 KV -> 8 per group -> 72 groups of 8
  4  rho_priv = corr over all held-out (head x 5) entries of P^(0) against Omega . P^(400)

═══ THE NULL ═══
Permute head indices WITHIN KV GROUP in off400 before alignment. This preserves layer identity AND
group identity exactly, and destroys only individual identity -- which is the whole proposition.
400 draws, p95.

═══ TWO CONTROLS, BOTH REQUIRED TO GATE THE VERDICT ═══
  C1  inject known private-loading reliability 0.0 / 0.3 / 0.6 / 0.9 -> rho_priv must recover it
      MONOTONICALLY, or the instrument cannot see private structure at all
  C2  a GROUP-ONLY arm where P == 0 by construction plus matched noise -> must return ~0
      C2 IS THE ARM EVERY EARLIER CONTROL IN THIS PROGRAMME LACKED. Three times this session I
      built a control that showed a statistic RISES when the effect is injected and never showed it
      FALLS when the effect is absent. A control that only spans one side of the threshold is not a
      control.

═══ REGISTERED BEFORE THE RUN. Not amended after any number is seen. ═══
  T0  GATE: C1 not monotone, OR |C2| >= 0.05  ->  UNVERIFIED, no world moves.
  T1  rho_priv < 0.15  OR inside the within-group null p95
      ->  PRIVACY_DEAD. Head-private selectivity beyond the KV group is dead; the object is one
          global rank->=5 field whose loadings are a KV-GROUP property, and WB collapses into WD.
  T2  rho_priv >= 0.15 AND outside the null p95 AND |C2| < 0.05
      ->  PRIVACY_REAL. Each head owns a stable private mixing vector beyond its group.
  Anything else -> UNVERIFIED_PARTIAL.

The 1.5b pair is the decision. The 3b pair is a free second replicate and is NOT gated on.
The LAYER-mean variant runs alongside for free, to price group identity against layer identity.
"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
RANK = 5
N_NULL = 400
RULE = {'T1_privacy_dead_below': 0.15, 'T0_c2_max_abs': 0.05, 'rank': RANK, 'n_null': N_NULL}
GQA = {'1.5b': 6, '3b': 8}


def two_way_resid(D):
    mu = D.mean()
    return D - mu - (D.mean(1) - mu)[:, None] - (D.mean(0) - mu)[None, :]


def loadings(D, rank=RANK):
    """A = U.S[:rank] of the RANK-1-STRIPPED two-way residual. Head-indexed, so cross-set comparable."""
    E = two_way_resid(D)
    U, S, Vt = np.linalg.svd(E, full_matrices=False)
    E1 = E - S[0] * np.outer(U[:, 0], Vt[0])
    U2, S2, _ = np.linalg.svd(E1, full_matrices=False)
    return U2[:, :rank] * S2[:rank]


def privatise(A, gid):
    """P_h = A_h - mean over h's own block. gid is the block label per head-cell."""
    P = A.copy()
    for g in np.unique(gid):
        m = gid == g
        P[m] -= A[m].mean(0)
    return P


def procrustes(X, Y):
    """Orthogonal Omega minimising ||X - Y.Omega||. Fit on the rows given, applied elsewhere."""
    U, _, Vt = np.linalg.svd(Y.T @ X)
    return U @ Vt


def rho_priv(A0, A4, gid, rng, fit_frac=0.5):
    n = A0.shape[0]
    idx = rng.permutation(n)
    fit, hold = idx[:int(n * fit_frac)], idx[int(n * fit_frac):]
    P0, P4 = privatise(A0, gid), privatise(A4, gid)
    Om = procrustes(P0[fit], P4[fit])
    a, b = P0[hold].ravel(), (P4[hold] @ Om).ravel()
    return float(np.corrcoef(a, b)[0, 1])


def within_block_perm(gid, rng):
    p = np.arange(len(gid))
    for g in np.unique(gid):
        i = np.where(gid == g)[0]
        p[i] = i[rng.permutation(len(i))]
    return p


def measure(A0, A4, gid, rng, n_null=N_NULL, label=''):
    obs = rho_priv(A0, A4, gid, np.random.default_rng(SEED))
    nl = np.array([rho_priv(A0, A4[within_block_perm(gid, rng)], gid, np.random.default_rng(SEED))
                   for _ in range(n_null)])
    p95 = float(np.percentile(nl, 95))
    r = {'rho_priv': obs, 'null_median': float(np.median(nl)), 'null_p95': p95,
         'null_sd': float(np.std(nl, ddof=1)), 'inside_null_p95': bool(obs <= p95),
         'z': float((obs - np.median(nl)) / np.std(nl, ddof=1)) if np.std(nl, ddof=1) > 0 else float('nan')}
    if label:
        print(f"    {label:<26} rho_priv {obs:+.4f}   null med {r['null_median']:+.4f}  "
              f"p95 {p95:+.4f}  z {r['z']:+.1f}   inside {r['inside_null_p95']}")
    return r


# ───────────────────────── controls ─────────────────────────
def synth(rng, nh=336, ni=120, per_group=6, shared_rank=5, priv_rank=3, rel=0.9,
          priv_amp=1.0, noise=1.0):
    """Two disjoint item sets. Shared field with GROUP-level loadings, plus a per-head private
    loading reused across sets at reliability `rel`. priv_amp=0 gives the group-only arm."""
    ng = nh // per_group
    Gload = rng.standard_normal((ng, shared_rank))
    A_shared = np.repeat(Gload, per_group, axis=0)
    Wp = rng.standard_normal((nh, priv_rank))
    out = []
    for _ in range(2):
        Wps = rel * Wp + np.sqrt(max(1 - rel ** 2, 0.0)) * rng.standard_normal((nh, priv_rank))
        Vs = rng.standard_normal((shared_rank, ni))
        Vp = rng.standard_normal((priv_rank, ni))
        out.append(A_shared @ Vs + priv_amp * (Wps @ Vp) + noise * rng.standard_normal((nh, ni)))
    return out


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'question': "Does individual head identity exist above KV-group identity, in the "
                       "loadings that R30 showed are stable across disjoint item sets?"}
    gid_s = np.repeat(np.arange(56), 6)

    print('  C1 — injected private-loading reliability must be recovered MONOTONICALLY')
    c1 = {}
    for rel in (0.0, 0.3, 0.6, 0.9):
        Xa, Xb = synth(rng, rel=rel, priv_amp=1.0)
        c1[f'rel_{rel}'] = measure(loadings(Xa), loadings(Xb), gid_s, rng, n_null=60,
                                   label=f'injected rel={rel}')['rho_priv']
    vals = [c1[f'rel_{r}'] for r in (0.0, 0.3, 0.6, 0.9)]
    c1['monotone'] = bool(all(vals[i] < vals[i + 1] for i in range(3)))
    out['C1'] = c1
    print(f"    monotone: {c1['monotone']}")

    print('\n  C2 — GROUP-ONLY arm, P == 0 by construction, must return ~0')
    Xa, Xb = synth(rng, priv_amp=0.0)
    c2 = measure(loadings(Xa), loadings(Xb), gid_s, rng, n_null=60, label='group-only (no private)')
    out['C2'] = c2
    gate = c1['monotone'] and abs(c2['rho_priv']) < RULE['T0_c2_max_abs']
    out['gate_passed'] = bool(gate)
    print(f"    |rho| {abs(c2['rho_priv']):.4f} < {RULE['T0_c2_max_abs']} -> "
          f"{'GATE PASSES' if gate else 'GATE FAILS; ALL BELOW UNVERIFIED'}")

    print('\n  OBSERVED')
    res = {}
    for tag, per_group in (('1.5b', GQA['1.5b']), ('3b', GQA['3b'])):
        try:
            za = np.load(REPO / 'R29_cancellation' / 'results' /
                         f'r29_vectors_qwen2.5-{tag}_I_final_off0.npz')
            zb = np.load(REPO / 'R29_cancellation' / 'results' /
                         f'r29_vectors_qwen2.5-{tag}_I_final_off400.npz')
        except FileNotFoundError:
            print(f'    {tag}: no off400 replicate on disk — skipped, not gated on')
            continue
        A0, A4 = loadings(za['delta'].astype(np.float64)), loadings(zb['delta'].astype(np.float64))
        lay, hd = za['layer'], za['head']
        gid = lay.astype(np.int64) * 2 + (hd // per_group)
        lid = lay.astype(np.int64)
        print(f'    --- {tag}, {per_group} query heads per KV group ---')
        res[tag] = {'kv_group': measure(A0, A4, gid, rng, label='KV-group private'),
                    'layer': measure(A0, A4, lid, rng, label='LAYER private (free comparison)'),
                    'n_groups': int(len(np.unique(gid)))}
    out['observed'] = res

    if not gate:
        verdict = 'UNVERIFIED_GATE_FAILED'
    elif '1.5b' not in res:
        verdict = 'UNVERIFIED_NO_REPLICATE'
    else:
        r = res['1.5b']['kv_group']
        verdict = ('PRIVACY_DEAD' if (r['rho_priv'] < RULE['T1_privacy_dead_below']
                                      or r['inside_null_p95'])
                   else 'PRIVACY_REAL')
    out['verdict'] = verdict
    print(f'\n  VERDICT  {verdict}')

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r31_loading_privacy.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
