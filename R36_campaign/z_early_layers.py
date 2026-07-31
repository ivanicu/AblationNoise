#!/usr/bin/env python3
"""Do early heads (layers 0-9) carry a positionally-localized final-token read? Zero forwards.

R35 established that changing the ablation SUPPORT destroys ~10x more of the within-layer ordering
than changing the entire item set, and that the destruction is confined to the early layers: X by
depth third is +0.2795 / +0.2525 / +0.7946 in 1.5b against a ceiling that is FLAT with depth. So in
layers 0-9 the same head reorders almost completely when the intervention moves by one axis.

The proposed generator: an early head's work is transacted at NON-FINAL positions. I_final samples
ONE point of a positional profile while I_all sums it, so two heads with equal totals and different
profiles must reorder. If that is right, early heads should have a MEASURABLY NON-FLAT profile.

    f_h = |e_final| / sum_t |e_t|      the fraction of a head's total positional effect sitting at
                                        the final query position. Dimensionless, from margin-nats.

═══ SUPPORT RULING, REGISTERED ═══
f_h comes from the `.final` cell, NOT `.all`.
  `.final` holds the intervention SITE fixed at one token, so the 8-vector varies only in the
  STIMULUS -- which item the prompt queries. f_h is then read-side positional selectivity of the
  head's final-token read, which is exactly what the name e_final asserts.
  `.all` ablates at every position, so each pos[t] sums the head's write-side contribution at item
  t's own token PLUS its read at the final token. Its denominator is not decomposable per mechanism
  and a large f_h under `.all` is unattributable -- two mechanisms, one number.
`.all` is NOT discarded: it is the SPECIFICATION-ROBUSTNESS arm. Registered: if the SIGN of the
layer-0-9 f_h trend differs between `.final` and `.all`, f_h is a property of the intervention
support rather than of the head, and is WITHDRAWN as a head statistic.

═══ THE FLOOR IS DATA-DERIVED, because parametric floors failed seven times in this project ═══
Permute the 8 POSITION LABELS within each head. This preserves that head's multiset of |e_t|
EXACTLY -- so it is norm-matched by construction, not by tuning -- and destroys only positional
localization. Its expectation is exactly 1/8 = 0.125 for every head, by symmetry, so the floor is
analytic AND measured, and the two must agree or the implementation is wrong.

═══ THE STATISTICAL UNIT IS THE BASE INSTANCE, n = 64 ═══
Not the 1024 prompts. base_pos is (64, 8, 3) per cell and its mean over axis 0 reproduces `pos` to
5.9e-08, verified. Every resample resamples BASE INSTANCES.

═══ REGISTERED BEFORE THE RUN. Resolution FIRST, threshold second, estimate last. ═══
  X   = Delta f_h = mean_h f_h(observed) - mean_h f_h(position-permuted floor), over layers 0-9
  CI  = 2000-resample BCa over the 64 base instances
  RES = the achievable resolution of Delta f_h, propagated from the `sem` column ALREADY IN THE
        DATA, computed and PRINTED BEFORE the CI. This is the 0.371-vs-0.4286 lesson: a threshold
        below the instrument's resolution is a null with no power.
  T   = max(0.05, RES)
  KILL: |X| < T, OR the 95% BCa CI covers 0
        -> "early heads (0-9) carry a positionally-localized final-token read" is DEAD, layers 0-9
           are dropped and the drop is logged, not revisited.

⚠ SCOPE, AND IT IS A HARD LIMIT ON THE VERDICT. The registered rule says "in BOTH models". Only
qwen2.5-1.5b has a crossed position x support scan; there is no 3b one on disk. So the kill clause
CANNOT be evaluated as registered, and whatever this file returns is a ONE-MODEL result labelled
PARTIAL. Under the standing standard a one-model result is not a result. The 3b crossed scan is a
forward pass queued BEHIND this statistic, not before it.
"""
import json
import math
import pathlib
import statistics as st
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
N_BOOT = 2000
LAYERS = range(0, 10)
RULE = {'T_floor': 0.05, 'n_boot': N_BOOT, 'layers': [0, 9],
        'unit': 'base instance, n=64', 'support_for_f': '.final',
        'floor': 'within-head permutation of the 8 position labels (norm-matched by construction, '
                 'analytic expectation exactly 1/8)'}
N = st.NormalDist()


def f_from(e):
    """f_h = |e_final| / sum_t |e_t|. e is an (..., 8) array of position effects in margin-nats."""
    a = np.abs(e)
    s = a.sum(-1)
    return np.where(s > 0, a[..., -1] / np.maximum(s, 1e-300), np.nan)


def bca(theta_boot, theta_hat, jack):
    """Bias-corrected and accelerated interval. The jackknife supplies ONLY the acceleration
    constant; the precision is the bootstrap's, because a jackknife precision estimate was
    measured 4.19x optimistic in this project and is not trusted for width."""
    b = np.asarray(theta_boot)
    prop = float((b < theta_hat).mean())
    prop = min(max(prop, 1.0 / (2 * len(b))), 1 - 1.0 / (2 * len(b)))
    z0 = N.inv_cdf(prop)
    jm = np.mean(jack)
    num = ((jm - jack) ** 3).sum()
    den = 6.0 * (((jm - jack) ** 2).sum() ** 1.5)
    a = num / den if den > 0 else 0.0
    out = []
    for q in (0.025, 0.975):
        z = N.inv_cdf(q)
        adj = z0 + (z0 + z) / max(1 - a * (z0 + z), 1e-12)
        out.append(float(np.percentile(b, 100 * N.cdf(adj))))
    return out, float(z0), float(a)


def load(model):
    f = REPO / 'R19_crossed_position_support' / 'results' / f'r19_crossed_qwen2.5-{model}.json'
    if not f.exists():
        return None
    d = json.load(open(f))
    cells = d['cells']
    out = {}
    for sup in ('final', 'all'):
        keys = sorted(k for k in cells if k.endswith('.' + sup))
        lay = np.array([int(k[1:3]) for k in keys])
        bp = np.stack([np.array(cells[k]['base_pos'])[:, :, 0] for k in keys])   # (H, 64, 8)
        sem = np.stack([np.array(cells[k]['pos'])[:, 1] for k in keys])          # (H, 8)
        out[sup] = {'keys': keys, 'layer': lay, 'base_pos': bp, 'sem': sem}
    out['n_base'] = d['n_base']
    out['n_positions'] = d['n_positions']
    return out


def delta_f(bp, rng=None):
    """mean_h f(observed) - mean_h f(position-permuted). bp is (H, 8) of position means."""
    fo = f_from(bp)
    if rng is None:                       # analytic floor: every permutation, in expectation, 1/8
        fl = np.full(len(bp), 1.0 / bp.shape[-1])
    else:
        fl = f_from(np.stack([r[rng.permutation(len(r))] for r in bp]))
    return float(np.nanmean(fo) - np.nanmean(fl))


def main():
    rng = np.random.default_rng(SEED)
    out = {'seed': SEED, 'registered_rule': RULE,
           'scope': 'ONE MODEL ONLY — no 3b crossed scan exists, so the registered "both models" '
                    'clause cannot be evaluated. PARTIAL by construction.'}
    res = {}
    for model in ('1.5b', '3b'):
        d = load(model)
        if d is None:
            print(f'  {model}: no crossed scan on disk — skipped, and the verdict stays PARTIAL')
            continue
        row = {}
        for sup in ('final', 'all'):
            s = d[sup]
            m = np.isin(s['layer'], list(LAYERS))
            bp = s['base_pos'][m]                       # (H, 64, 8)
            sem = s['sem'][m]                            # (H, 8)
            e = bp.mean(1)                                # (H, 8) position means
            H = len(e)

            # ── RESOLUTION FIRST, before any estimate is looked at ──
            a = np.abs(e)
            S = a.sum(1, keepdims=True)
            # d f/d e_t : final term (S - a_final)/S^2 ; others -a_final/S^2, times sign
            g = np.where(np.arange(8)[None, :] == 7, (S - a[:, 7:8]) / S ** 2,
                         -a[:, 7:8] / S ** 2)
            sd_f = np.sqrt(((g * sem) ** 2).sum(1))
            res_delta = float(np.median(sd_f) / math.sqrt(H))
            T = max(RULE['T_floor'], res_delta)
            print(f'\n  {model} .{sup}   layers 0-9, {H} heads, unit = base instance n={d["n_base"]}')
            print(f"    RESOLUTION FIRST: median per-head sd(f_h) {np.median(sd_f):.5f}, "
                  f"resolution of Delta f_h {res_delta:.5f}  ->  T = max(0.05, RES) = {T:.5f}")

            # ── floor: analytic and measured, which must agree ──
            fl_meas = [float(np.nanmean(f_from(np.stack([r[rng.permutation(8)] for r in e]))))
                       for _ in range(400)]
            print(f"    floor: analytic 1/8 = {1/8:.5f}   measured over 400 permutations "
                  f"{np.mean(fl_meas):.5f} +- {np.std(fl_meas, ddof=1):.5f}   "
                  f"agree: {abs(np.mean(fl_meas) - 0.125) < 0.01}")

            # ── the estimate, and a BCa CI over the 64 base instances ──
            hat = delta_f(e)
            nb = bp.shape[1]
            boot = []
            for _ in range(N_BOOT):
                idx = rng.integers(0, nb, nb)
                boot.append(delta_f(bp[:, idx, :].mean(1)))
            jack = np.array([delta_f(np.delete(bp, i, axis=1).mean(1)) for i in range(nb)])
            ci, z0, acc = bca(boot, hat, jack)
            covers0 = bool(ci[0] <= 0 <= ci[1])
            row[sup] = {'n_heads': H, 'mean_f_observed': float(np.nanmean(f_from(e))),
                        'floor_analytic': 0.125,
                        'floor_measured': float(np.mean(fl_meas)),
                        'delta_f': hat, 'bca_ci95': ci, 'ci_covers_zero': covers0,
                        'bca_z0': z0, 'bca_accel': acc,
                        'resolution_delta_f': res_delta, 'T_registered': T,
                        'abs_delta_below_T': bool(abs(hat) < T),
                        'boot_sd': float(np.std(boot, ddof=1))}
            print(f"    mean f_h observed {row[sup]['mean_f_observed']:.5f}   "
                  f"Delta f_h {hat:+.5f}   BCa 95% CI [{ci[0]:+.5f}, {ci[1]:+.5f}]   "
                  f"boot sd {row[sup]['boot_sd']:.5f}")
            print(f"    |Delta| < T: {row[sup]['abs_delta_below_T']}   CI covers 0: {covers0}")
        # specification robustness: does the SIGN agree between supports?
        if 'final' in row and 'all' in row:
            row['sign_agrees_across_support'] = bool(
                np.sign(row['final']['delta_f']) == np.sign(row['all']['delta_f']))
            print(f"    SPEC ROBUSTNESS: sign(.final) {np.sign(row['final']['delta_f']):+.0f} vs "
                  f"sign(.all) {np.sign(row['all']['delta_f']):+.0f}  -> agrees "
                  f"{row['sign_agrees_across_support']}")
        res[model] = row
    out['cells'] = res

    if '1.5b' not in res:
        verdict = 'UNVERIFIED_NO_DATA'
    else:
        r = res['1.5b']['final']
        dead = r['abs_delta_below_T'] or r['ci_covers_zero']
        withdrawn = not res['1.5b'].get('sign_agrees_across_support', True)
        verdict = ('F_H_WITHDRAWN_SUPPORT_PROPERTY' if withdrawn
                   else 'POSITIONAL_LOCALISATION_DEAD_PARTIAL' if dead
                   else 'POSITIONAL_LOCALISATION_LIVES_PARTIAL')
    out['verdict'] = verdict
    out['partial_because'] = 'registered rule requires BOTH models; only 1.5b has a crossed scan'
    print(f'\n  VERDICT  {verdict}   (PARTIAL — one model, and the standard says that is not a result)')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r36_z_early_layers.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
