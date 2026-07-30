#!/usr/bin/env python3
"""What actually carries the forced-choice identification? Four measurements. Zero forwards.

R32 got top1 0.9107 on a 6-way choice among KV group-mates from a disjoint item set. Two things are
now established about that number and both narrow it:

  - split='head' is optimistically biased by construction (the fit set contains candidates, and
    sum_m P = 0 inside a group makes that bias one-directional). 0.9107 is RETRACTED. The admissible
    number is the whole-group split, 0.8631.
  - the no-private surrogate that was supposed to price it removes 98.6% of loading energy with its
    group mean, against 0.1468 in the data. It never tested "no private rule"; it tested "no private
    rule AND group-dominance 6.7x higher than reality".

So 0.8631 is UNVERIFIED, and this file is what would clear or kill it.

═══ REGISTERED BEFORE THE RUN. Four thresholds, none amended after any number is seen. ═══

  M1  MATCHED MEASURED NULL. 1000 draws of the no-private surrogate, with its noise tuned FIRST so
      that variance_fraction_removed_by_block_mean lands in 0.147 +- 0.02 -- the data's own value --
      then scored with split='block', the same split as the headline.
      IF 0.8631 <= the null's 99.9th percentile  ->  THE PRIVACY CLAIM IS DEAD AND THIS LINE CLOSES.

  M2  SCALAR-ONLY BASELINE. Rank the same six candidates by |per-head scalar difference| for
      ||delta_h||_2, participation ratio n_eff, row kurtosis. A permanent per-head scale is a fixed
      function of head index and replicates across item sets trivially; it is not a private rule.
      IF ANY single scalar reaches top1 >= 0.50  ->  the finding is DOWNGRADED to per-head SCALE.
      (head index itself is included as a DEGENERATE REFERENCE: it must return exactly 1.0, because
       the index IS the label. If it does not, the indexing in this file is broken.)

  M3  POSITIONAL CONTROL. Hold within-group position fixed and vary group: candidates are the heads
      at the same position p in five other groups, plus the true head.
      IF top1 >= 0.40  ->  contiguous head indexing is a carrier and the group-mate result is
      contaminated by it.

  M4  LAYER-12WAY DECOMPOSITION. R32's layer 12-way used the same label for the privatisation AND
      the candidate set, so it removed the LAYER mean and left KV-group identity inside P -- a head
      could be picked partly by which of its layer's two groups it is in. Split its top-1 into
      P(correct group) and P(correct head | correct group).
      IF P(correct head | correct group) <= M1's 99.9th percentile  ->  privacy is GROUP-level only,
      WB collapses into WD, and the head-level claim is retracted.

═══ SCOPE, UNCHANGED ═══
No 3b off400 exists on disk, so there is no second disjoint-item-set replicate. Everything here is
n = 1 MODEL and may not be stated as a property of Qwen2.5 or of GQA.
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
RULE = {'M1_n_draws': N_NULL, 'M1_percentile': 99.9, 'M1_headline': 0.8631,
        'M2_downgrade_if_scalar_top1_atleast': 0.50, 'M3_contaminated_if_atleast': 0.40,
        'target_frac0': 0.1468, 'frac0_tol': 0.02, 'rank': RANK}


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


def choice(A0, A4, blk, rng, cand_fn=None):
    """Whole-group split always. cand_fn(h) overrides the candidate set (used by M3)."""
    P0, frac = privatise(A0, blk)
    P4, _ = privatise(A4, blk)
    fit, hold = block_split(blk, rng)
    R = P4 @ procrustes(P0[fit], P4[fit])
    Pn = P0 / (np.linalg.norm(P0, axis=1, keepdims=True) + 1e-300)
    Rn = R / (np.linalg.norm(R, axis=1, keepdims=True) + 1e-300)
    hits = 0
    for h in hold:
        cand = cand_fn(h) if cand_fn else np.where(blk == blk[h])[0]
        hits += int(cand[int(np.argmax(Rn[cand] @ Pn[h]))] == h)
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


def scalar_choice(s0, s4, blk, rng):
    """Rank candidates by |scalar difference|. Nearest wins."""
    _, hold = block_split(blk, rng)
    hits = 0
    for h in hold:
        cand = np.where(blk == blk[h])[0]
        hits += int(cand[int(np.argmin(np.abs(s4[cand] - s0[h])))] == h)
    return hits / len(hold)


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
    obs, frac_obs = choice(A0, A4, gblk, np.random.default_rng(SEED))
    out['observed_groupsplit_top1'] = obs
    out['observed_frac0'] = frac_obs
    print(f'  observed (whole-group split): top1 {obs:.4f}   frac0 {frac_obs:.4f}')

    # ── M1: match the surrogate on frac0 FIRST, then draw 1000 ──
    print(f"\n  M1 — matching the surrogate's frac0 to the data's {RULE['target_frac0']:.4f}")
    best = None
    for nz in (1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0):
        Xa, Xb = synth(rng, priv_amp=0.0, noise=nz)
        _, f = choice(loadings(Xa), loadings(Xb), np.repeat(np.arange(56), 6),
                      np.random.default_rng(SEED))
        print(f'    noise {nz:<6} frac0 {f:.4f}')
        if best is None or abs(f - RULE['target_frac0']) < abs(best[1] - RULE['target_frac0']):
            best = (nz, f)
    nz, fbest = best
    matched = abs(fbest - RULE['target_frac0']) <= RULE['frac0_tol']
    print(f"    chosen noise {nz}, frac0 {fbest:.4f}   matched within "
          f"{RULE['frac0_tol']}: {matched}")
    blk_s = np.repeat(np.arange(56), 6)
    nulls = []
    for _ in range(N_NULL):
        Xa, Xb = synth(rng, priv_amp=0.0, noise=nz)
        t, _ = choice(loadings(Xa), loadings(Xb), blk_s, np.random.default_rng(SEED))
        nulls.append(t)
    nulls = np.array(nulls)
    q999 = float(np.percentile(nulls, RULE['M1_percentile']))
    m1 = {'chosen_noise': nz, 'achieved_frac0': fbest, 'frac0_matched': bool(matched),
          'null_mean': float(nulls.mean()), 'null_sd': float(nulls.std(ddof=1)),
          'null_median': float(np.median(nulls)), 'null_p999': q999,
          'null_max': float(nulls.max()), 'n_draws': N_NULL,
          'observed_clears_p999': bool(obs > q999)}
    out['M1_matched_null'] = m1
    print(f"    null over {N_NULL} draws: mean {m1['null_mean']:.4f} sd {m1['null_sd']:.4f} "
          f"median {m1['null_median']:.4f} p99.9 {q999:.4f} max {m1['null_max']:.4f}")
    print(f"    observed {obs:.4f} clears p99.9 -> {m1['observed_clears_p999']}")

    # ── M2: scalar-only baselines ──
    print('\n  M2 — scalar-only baselines (a permanent per-head scale is not a private rule)')
    E0, E4 = two_way_resid(D0), two_way_resid(D4)
    def neff(E):
        return (E ** 2).sum(1) ** 2 / (E ** 4).sum(1)
    def kurt(E):
        z = (E - E.mean(1, keepdims=True)) / E.std(1, ddof=1, keepdims=True)
        return (z ** 4).mean(1)
    scal = {'norm_l2': (np.linalg.norm(E0, axis=1), np.linalg.norm(E4, axis=1)),
            'n_eff': (neff(E0), neff(E4)), 'row_kurtosis': (kurt(E0), kurt(E4)),
            'head_index_DEGENERATE_REFERENCE': (hd.astype(float), hd.astype(float))}
    m2 = {}
    for name, (s0, s4) in scal.items():
        t = scalar_choice(s0, s4, gblk, np.random.default_rng(SEED))
        m2[name] = {'top1': t, 'reaches_downgrade': bool(t >= RULE['M2_downgrade_if_scalar_top1_atleast'])}
        print(f"    {name:<34} top1 {t:.4f}   >= 0.50 -> {m2[name]['reaches_downgrade']}")
    out['M2_scalar_baselines'] = m2
    idx_ok = abs(m2['head_index_DEGENERATE_REFERENCE']['top1'] - 1.0) < 1e-9
    out['M2_indexing_selfcheck_passed'] = bool(idx_ok)
    print(f"    indexing self-check (head index must be exactly 1.0): {idx_ok}")
    real_scalars = [v['top1'] for k, v in m2.items() if 'DEGENERATE' not in k]
    m2_downgrade = any(t >= RULE['M2_downgrade_if_scalar_top1_atleast'] for t in real_scalars)

    # ── M3: positional control ──
    print('\n  M3 — positional control: hold within-group position fixed, vary group')
    pos = hd % 6
    rng3 = np.random.default_rng(SEED + 7)
    same_pos = {p: np.where(pos == p)[0] for p in range(6)}
    def cand_pos(h):
        pool = same_pos[pos[h]]
        pool = pool[pool != h]
        return np.concatenate([[h], rng3.choice(pool, 5, replace=False)])
    m3top, _ = choice(A0, A4, gblk, np.random.default_rng(SEED), cand_fn=cand_pos)
    out['M3_positional'] = {'top1': m3top, 'contaminated': bool(m3top >= RULE['M3_contaminated_if_atleast'])}
    print(f"    top1 {m3top:.4f}   >= 0.40 -> contaminated {out['M3_positional']['contaminated']}")

    # ── M4: layer 12-way decomposition ──
    print('\n  M4 — layer 12-way split into P(correct group) and P(correct head | correct group)')
    lblk = lay
    P0, _ = privatise(A0, lblk)
    P4, _ = privatise(A4, lblk)
    fit, hold = block_split(lblk, np.random.default_rng(SEED))
    R = P4 @ procrustes(P0[fit], P4[fit])
    Pn = P0 / (np.linalg.norm(P0, axis=1, keepdims=True) + 1e-300)
    Rn = R / (np.linalg.norm(R, axis=1, keepdims=True) + 1e-300)
    hit_all = hit_grp = hit_head_given = n_given = 0
    for h in hold:
        cand = np.where(lblk == lblk[h])[0]
        pick = cand[int(np.argmax(Rn[cand] @ Pn[h]))]
        hit_all += int(pick == h)
        same_g = (hd[pick] // 6) == (hd[h] // 6)
        hit_grp += int(same_g)
        if same_g:
            n_given += 1
            hit_head_given += int(pick == h)
    m4 = {'top1_12way': hit_all / len(hold), 'p_correct_group': hit_grp / len(hold),
          'p_correct_head_given_group': hit_head_given / n_given if n_given else float('nan'),
          'n_given_correct_group': n_given,
          'chance_group': 0.5, 'chance_head_given_group': 1 / 6}
    m4['group_level_only'] = bool(m4['p_correct_head_given_group'] <= q999)
    out['M4_layer_decomposition'] = m4
    print(f"    top1 12-way {m4['top1_12way']:.4f}   P(correct group) {m4['p_correct_group']:.4f} "
          f"(chance 0.5)   P(correct head | correct group) {m4['p_correct_head_given_group']:.4f} "
          f"(chance 0.1667, n={n_given})")

    if not matched or not idx_ok:
        verdict = 'UNVERIFIED_SURROGATE_UNMATCHED' if not matched else 'UNVERIFIED_INDEXING_BROKEN'
    elif not m1['observed_clears_p999']:
        verdict = 'PRIVACY_DEAD_M1'
    elif m2_downgrade:
        verdict = 'DOWNGRADED_TO_PER_HEAD_SCALE'
    elif out['M3_positional']['contaminated']:
        verdict = 'CONTAMINATED_BY_POSITION'
    elif m4['group_level_only']:
        verdict = 'PRIVACY_IS_GROUP_LEVEL_ONLY'
    else:
        verdict = 'PRIVACY_SURVIVES_ALL_FOUR'
    out['verdict'] = verdict
    print(f'\n  VERDICT  {verdict}')

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r32_what_carries_it.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
