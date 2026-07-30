#!/usr/bin/env python3
"""Ivan's GQA-envelope hypothesis, tested on the half I never measured. Zero forwards.

⚠⚠ ANNOTATED 2026-07-30 AFTER THE FIRST RUN. The navigator overturned this file's null and its
framing. The original text is kept below unedited; read this block first, because the first run's
p-values were wrong and this file's own headline number already contradicted its hypothesis.

  DEFECT 1 — THE NULL WAS ANTI-CONSERVATIVE BY ~sqrt(L).
  combined() drew a FRESH permutation for every layer inside the null loop, while the observed
  statistic uses ONE g across all 28 (or 36) layers. Summing L independently-permuted eta^2 values
  concentrates: the null's sd shrinks by ~sqrt(L) ~ 5.3x, so every p the first run printed
  (0.000050 to 0.000150) was inflated. The MEAN of the null was correct, hence the `excess`
  column survives unchanged; only the p-values were wrong. Fixed: one joint permutation per draw.

  DEFECT 2 — THE PERMUTATION NULL TESTS THE WRONG LABEL SET.
  g = h // rep is a CONTIGUOUS BLOCK of head indices. A head-label permutation destroys index
  contiguity, so any smooth or blockwise trend in raw head index registers as "GQA group". The
  shape-matched null is the CYCLIC-SHIFT SHAM FAMILY: g_s(h) = ((h - s) mod n_h) // rep for
  s = 0..rep-1, which holds block size, block count and contiguity fixed and moves only where the
  KV boundary falls. It is now the PRIMARY null and the permutation p is retained only as the
  labelled anti-conservative comparison. (R25's cyclic.py already used this family; not reusing it
  here was the error.)

  DEFECT 3 — DECLARED BUT NOT IMPLEMENTED.
  The docstring below says the identity check "RUNS FIRST". It was never in the file. It is now,
  and it is exact algebra rather than a regression: log_var_i = 2*log(per_head_sem) + log(n),
  identically, because sem = sd_i/sqrt(n). The check reports max|residual| and it is ~0.

  WHAT THE FIRST RUN ALREADY SAID, AND I MISREAD.
  The ratio (Var_i excess)/(|mean| excess) came back 0.74 / 0.74 / 2.25. Below 1 means Var_i is
  LESS grouped than the signed mean -- the OPPOSITE of the envelope's directional prediction -- in
  both 1.5b cells. I reported this as "your mechanism confirmed, in a stronger form". It is not.

═══ REGISTERED BEFORE THIS RUN, by the navigator, thresholds fixed here and not amended ═══
  BOTH legs must hold or the GQA-envelope hypothesis is dead:
    LEG A  TRUE's mean_eta2(log_var_i) exceeds the MAXIMUM of the sham shifts, in >=2 of 3 cells
    LEG B  ratio (Var_i excess)/(|mean| excess) >= 1.0, in >=2 of 3 cells
  Either leg failing in >=2 of 3 cells -> ENVELOPE_DEAD, and the file ships as a negative.

───────────────────────────── ORIGINAL DOCSTRING, UNEDITED ─────────────────────────────

He writes it as a precise, separable prediction:

    E_i[Delta_{h,i}^2 | g(h)=g]     CAN be modulated by the GQA group
    E_i[Delta_{h,i}   | g(h)=g]     need NOT be
    Corr_i(Delta_h, Delta_h')       need NOT rise within a group

Mechanism: same-group query heads share k_g and v_g but NOT q_h or W_O^(h). Shared KV decides what
common information substrate a head can read from, so it constrains the SCALE of a potential effect;
the private query and output map decide what it reads on a given item, where it writes, and which way
the margin moves.

R25 measured eta^2 on |mean_i Delta| -- the signed item mean -- and found structure in magnitude and
none in orientation. R29 measured the CORRELATION half and found null. NOBODY MEASURED Var_i, which is
the quantity the envelope hypothesis actually names.

Three quantities per cell, all from the persisted per-item tensors:

    log_var_i     log Var_i(Delta_{h,i})     the envelope's own coordinate
    log_absmean   log |mean_i Delta|         what R25 used
    log_rms       log rms_i(Delta)

The null is a within-layer head-label permutation, identical to R25's, so the layer's own distribution
is held exactly fixed and only the group assignment moves.

AND THE IDENTITY CHECK RUNS FIRST, because that is how the last two coordinates died: log_var_i is
regressed on per_head, per_head_sem, layer and head, and the residual is reported. A coordinate with no
residual is a reparameterisation. Note in advance that log_var_i is NOT expected to be free of them --
sem is sd_i/sqrt(n), so log_var_i is essentially 2*log(sem) + const. THAT IS THE POINT: if the envelope
lives in Var_i, R25's eta^2 on the MEAN and an eta^2 on Var_i are different tests of one hypothesis, and
the second one is available from two published columns at zero cost.

NO VERDICT IS EMITTED.
"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
SEED = 20260730
N_PERM = 20000
GQA = {'qwen2.5-1.5b': {'n_heads': 12, 'n_kv': 2}, 'qwen2.5-3b': {'n_heads': 16, 'n_kv': 2}}
RULE = {'legA_true_beats_all_shams_in_cells': 2, 'legB_ratio_atleast': 1.0,
        'legB_holds_in_cells': 2, 'n_cells': 3}


def eta_sq(v, g):
    gm = v.mean()
    tot = ((v - gm) ** 2).sum()
    if tot <= 0:
        return float('nan')
    return sum(((g == lab).sum() * (v[g == lab].mean() - gm) ** 2) for lab in np.unique(g)) / tot


def mean_eta(per_layer, g):
    e = [eta_sq(v, g) for v in per_layer]
    e = [x for x in e if x == x]
    return float(np.mean(e)) if e else float('nan')


def joint_perm_p(per_layer, g, rng, nperm=N_PERM):
    """ONE permutation per draw, applied to every layer -- the null the docstring always claimed."""
    obs = mean_eta(per_layer, g)
    hits = 0
    for _ in range(nperm):
        gp = g[rng.permutation(len(g))]
        if mean_eta(per_layer, gp) >= obs:
            hits += 1
    return obs, (1 + hits) / (1 + nperm)


def sham_family(per_layer, nh, rep):
    """Cyclic-shift shams: same block size, same block count, same contiguity, wrong KV boundary."""
    out = []
    for s in range(rep):
        g = np.array([((h - s) % nh) // rep for h in range(nh)])
        out.append((s, mean_eta(per_layer, g)))
    return out


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'n_perm': N_PERM, 'registered_rule': RULE,
           'hypothesis': "Ivan 2026-07-30: shared KV constrains the SCALE of a potential effect "
                         "(Var_i), private q_h and W_O^(h) decide item selectivity and sign, so "
                         "Var_i may be grouped while Corr_i and the signed mean need not be"}
    res = {}
    for f in sorted((HERE.parent / 'R29_cancellation' / 'results').glob('r29_vectors_*.npz')):
        stem = f.name[len('r29_vectors_'):-4]
        tag = 'qwen2.5-3b' if '3b' in stem else 'qwen2.5-1.5b'
        nh, nkv = GQA[tag]['n_heads'], GQA[tag]['n_kv']
        rep = nh // nkv
        g_true = np.array([h // rep for h in range(nh)])
        z = np.load(f)
        d, lay, hd = z['delta'], z['layer'], z['head']
        coords = {'log_var_i': [], 'log_absmean': [], 'log_rms': []}
        idmax = 0.0
        for L in sorted(set(lay.tolist())):
            X = d[lay == L][np.argsort(hd[lay == L])].astype(np.float64)
            if X.shape[0] != nh:
                continue
            n = X.shape[1]
            v, m, r = X.var(1, ddof=1), np.abs(X.mean(1)), np.sqrt((X * X).mean(1))
            sem = X.std(1, ddof=1) / np.sqrt(n)
            # DEFECT 3 FIX: the identity check, as exact algebra. log_var_i == 2*log(sem)+log(n).
            idmax = max(idmax, float(np.max(np.abs(np.log(v) - (2 * np.log(sem) + np.log(n))))))
            coords['log_var_i'].append(np.log(np.where(v > 0, v, np.nan)))
            coords['log_absmean'].append(np.log(np.where(m > 0, m, np.nan)))
            coords['log_rms'].append(np.log(np.where(r > 0, r, np.nan)))
        nl = len(coords['log_var_i'])
        null_exp = (nkv - 1) / (nh - 1)
        cell = {'n_layers': nl, 'null_expected': null_exp, 'n_sham_members': rep,
                'identity_max_abs_residual_nats': idmax}
        print(f'\n  {stem}   {nl} layers, {nh} heads, {rep} sham members')
        print(f"    IDENTITY CHECK  log_var_i vs 2*log(sem)+log(n):  max|resid| {idmax:.3e} nats"
              f"   -> {'REPARAMETERISATION, banned family' if idmax < 1e-6 else 'not an identity'}")
        for name, layers in coords.items():
            obs, p_perm = joint_perm_p(layers, g_true, rng)
            shams = sham_family(layers, nh, rep)
            sv = [x for s, x in shams if s != 0]
            rank = 1 + sum(1 for x in sv if x >= obs)
            cell[name] = {'mean_eta_sq': obs, 'excess': obs - null_exp,
                          'p_headlabel_perm_ANTICONSERVATIVE': p_perm,
                          'sham_shifts': {str(s): x for s, x in shams},
                          'sham_max': float(max(sv)), 'sham_mean': float(np.mean(sv)),
                          'rank_of_true_among_family': rank,
                          'p_exact_sham_family': rank / rep,
                          'true_beats_all_shams': bool(obs > max(sv))}
            c = cell[name]
            print(f"    {name:<14} eta2 {obs:.5f}  null {null_exp:.5f}  excess {c['excess']:+.5f}"
                  f"   sham max {c['sham_max']:.5f} mean {c['sham_mean']:.5f}"
                  f"   rank {rank}/{rep}  p_exact {c['p_exact_sham_family']:.3f}"
                  f"   p_perm {p_perm:.5f}[anticons]")
        res[stem] = cell
    out['cells'] = res

    print('\n  THE TWO REGISTERED LEGS')
    print(f"    {'cell':<30}{'legA true>shams':<18}{'Var excess':<13}{'|mean| excess':<15}"
          f"{'ratio':<9}legB")
    legA = legB = 0
    sep = {}
    for k, v in res.items():
        a, b = v['log_var_i']['excess'], v['log_absmean']['excess']
        ratio = a / b if b != 0 else float('nan')
        A = v['log_var_i']['true_beats_all_shams']
        B = bool(ratio >= RULE['legB_ratio_atleast'])
        legA += A
        legB += B
        sep[k] = {'var_excess': a, 'absmean_excess': b, 'ratio': ratio, 'legA': A, 'legB': B}
        print(f"    {k:<30}{str(A):<18}{a:<+13.5f}{b:<+15.5f}{ratio:<9.2f}{B}")
    out['separation'] = sep
    out['legA_cells'] = legA
    out['legB_cells'] = legB
    verdict = ('ENVELOPE_SURVIVES' if legA >= RULE['legA_true_beats_all_shams_in_cells']
               and legB >= RULE['legB_holds_in_cells'] else 'ENVELOPE_DEAD')
    out['verdict'] = verdict
    print(f"\n  legA {legA}/3 (need >=2)   legB {legB}/3 (need >=2)   ->  {verdict}")

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r30_envelope_vs_channel.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
