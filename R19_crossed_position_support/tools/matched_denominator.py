#!/usr/bin/env python3
"""D145 -- recompute the cross-task floor comparison with BOTH terms conditioned the same way.

`headline.margin_normalisation()` compares `floor_A / margin_A` against `floor_B / margin_B`.
Task A is R10, whose runner drops an item whose unablated argmax over the four rooms is wrong
(`R10_exhaustive/run.py:273`), so BOTH its terms are baseline-correct-only. Task B is R19, whose
runner deliberately does not filter (`R19_crossed_position_support/run.py:356`, citing R15's
finding that filtering selects on position), so BOTH its terms are over all 1024 items.

The comparison therefore never held either term fixed. This emits three versions:

    published            floor_B(all cells)  / margin_B(all items)
    denominator-matched  floor_B(all cells)  / margin_B(correct items)
    fully-matched        floor_B(2/2 cells)  / margin_B(correct items)

R19's own design choice is NOT being second-guessed -- the round's verdicts stand on the
unfiltered numbers. What is repaired is a CROSS-TASK RATIO that silently mixed two estimands.

THE CONTROL IS THE POINT. Restricting to the 315 fully-correct cells of 512 makes every per-head
mean noisier, and `2 sd` across heads of a noisier quantity is larger BY DEFAULT. A matched-count
random restriction (2000 draws, same 315 cells kept, drawn without regard to correctness) gives
the distribution that no-effect predicts, and the observed floor is quoted as a percentile of it.
Registered in MARGIN_DENOMINATOR_PREREGISTRATION.md Amendment 1, before this file existed.
"""
import json
import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
ROUND = HERE.parent
REPO = ROUND.parent
BAND_LO, BAND_HI = 14, 28          # identical to analyze.py:45
MI = 0                             # signed_margin_drop, METRICS[0]
N_DROP = 2000                      # registered
SEED = 20260728                    # registered


def floor2sd(v):
    """The floor, exactly as analyze.py:183 defines it: 2 sd over the band heads."""
    mu = float(np.mean(v))
    return 2.0 * math.sqrt(float(np.sum((v - mu) ** 2)) / (len(v) - 1))


def main():
    res = ROUND / 'results' / 'r19_crossed_qwen2.5-1.5b.json'
    bm = ROUND / 'results' / 'r19_baseline_margin_qwen2.5-1.5b.json'
    r10 = REPO / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    r18 = REPO / 'R18_all_positions' / 'results' / 'r18_allpos_qwen2.5-1.5b.json'
    for p in (res, bm, r10, r18):
        if not p.exists():
            print(f'REFUSED_MISSING_INPUT: {p}')
            return 3

    d = json.load(open(res))
    b = json.load(open(bm))
    NH, NL, NB = d['n_heads_per_layer'], d['n_layers'], d['n_base']
    NP = d['n_positions']
    band = [(L, h) for L in range(BAND_LO, min(BAND_HI, NL)) for h in range(NH)]

    # THE TWO FILES MUST DESCRIBE THE SAME EXPERIMENT. The cell counts come from a RERUN of the
    # baseline pass; if it built a different dataset, every number below is about something else.
    if not (b['n_prompts'] == d['n_prompts'] and b['n_base'] == NB
            and b['baseline_accuracy'] == d['baseline_accuracy']):
        print('REFUSED_DATASET_MISMATCH: the baseline rerun does not match the frozen result '
              f"({b['n_prompts']}/{b['n_base']}/{b['baseline_accuracy']} vs "
              f"{d['n_prompts']}/{NB}/{d['baseline_accuracy']})")
        return 3

    nc = np.array(b['n_correct_by_base_pos'])                       # (NB, NP), values 0..2
    keep = (nc == b['n_nuisance'])                                  # fully baseline-correct cells
    n_keep = int(keep.sum())

    out = {'n_cells': NB * NP, 'n_cells_kept': n_keep,
           'cells_by_n_correct': {str(v): int((nc == v).sum()) for v in range(b['n_nuisance'] + 1)},
           'position_composition_kept': [int(keep[:, p].sum()) for p in range(NP)],
           'position_composition_all': [NB] * NP,
           'margin_all_items': b['margin_all_items'],
           'margin_correct_only': b['margin_baseline_correct_only'],
           'margin_wrong_only': b['margin_baseline_wrong_only'],
           'max_margin_wrong': b['max_margin_wrong'],
           'n_perm_random_drop': N_DROP, 'seed': SEED, 'scopes': {}}

    rng = np.random.default_rng(SEED)
    flat_keep = keep.reshape(-1)

    for scope in ('final', 'all'):
        # (n_band, NB*NP) -- one row per head, one column per (base, position) cell
        M = np.array([[d['cells'][f'L{L:02d}H{h:02d}.{scope}']['base_pos'][bi][pj][MI]
                       for bi in range(NB) for pj in range(NP)] for (L, h) in band])
        tau_full_cells = M.mean(axis=1)
        # POSITIVE CONTROL: reconstructing the published per-head statistic from the (base, pos)
        # grid must reproduce the one analyze.py computes from the coarser `base` array. The design
        # is balanced, so these are the same mean -- any disagreement beyond JSON's 7-dp rounding
        # means the grid is not what it is assumed to be.
        # `['base']` rows are 3-vectors, one per metric. The first version of this line averaged
        # the WHOLE (64, 3) array instead of column MI, so the control reported a 0.455 mismatch
        # against a grid that is in fact consistent to 6e-08. The control caught its own harness --
        # which is the only reason the harness is trustworthy now.
        tau_pub = np.array([float(np.mean([row[MI]
                                           for row in d['cells'][f'L{L:02d}H{h:02d}.{scope}']['base']]))
                            for (L, h) in band])
        recon = float(np.max(np.abs(tau_full_cells - tau_pub)))

        tau_keep = M[:, flat_keep].mean(axis=1)
        f_full, f_keep = floor2sd(tau_full_cells), floor2sd(tau_keep)

        # matched-count random restriction: the null the observed restriction must beat
        null = np.empty(N_DROP)
        for i in range(N_DROP):
            idx = rng.choice(NB * NP, size=n_keep, replace=False)
            null[i] = floor2sd(M[:, idx].mean(axis=1))
        pct = float((null < f_keep).mean())
        lo, hi = float(np.percentile(null, 2.5)), float(np.percentile(null, 97.5))

        # POST HOC, NOT REGISTERED, AND IT CAN ONLY WEAKEN THE FINDING -- which is the only
        # direction an unregistered control is allowed to move it. The kept cells are heavily
        # position-skewed (that is R15's finding, restated), so the uniform null above conflates
        # "correctness matters" with "position composition changed". This null draws the SAME
        # per-position counts, uniformly within each position, so position composition is held
        # fixed and only the correctness selection remains.
        col_pos = np.tile(np.arange(NP), NB)
        per_pos = [int(keep[:, p].sum()) for p in range(NP)]
        cols_by_pos = [np.flatnonzero(col_pos == p) for p in range(NP)]
        null_s = np.empty(N_DROP)
        for i in range(N_DROP):
            idx = np.concatenate([rng.choice(cols_by_pos[p], size=per_pos[p], replace=False)
                                  for p in range(NP) if per_pos[p] > 0])
            null_s[i] = floor2sd(M[:, idx].mean(axis=1))
        pct_s = float((null_s < f_keep).mean())
        lo_s, hi_s = float(np.percentile(null_s, 2.5)), float(np.percentile(null_s, 97.5))

        out['scopes'][scope] = {
            'floor_full': f_full, 'floor_restricted': f_keep,
            'reconstruction_max_abs_err': recon,
            'reconstruction_ok': recon < 1e-6,
            'random_drop_mean': float(null.mean()),
            'random_drop_ci95': [lo, hi],
            'restricted_percentile_of_random': pct,
            'outside_central_95': not (lo <= f_keep <= hi),
            'posmatched_drop_mean': float(null_s.mean()),
            'posmatched_drop_ci95': [lo_s, hi_s],
            'restricted_percentile_of_posmatched': pct_s,
            'outside_central_95_posmatched': not (lo_s <= f_keep <= hi_s),
            'posmatched_is_post_hoc': True}

    # ---- the three residuals
    def band_floor_A(path):
        dd = json.load(open(path))
        L = {int(k): v for k, v in dd['layers'].items()}
        nh = len(L[BAND_LO]['per_head'])
        v = np.array([L[x]['per_head'][str(h)]
                      for x in range(BAND_LO, BAND_HI) for h in range(nh)])
        return floor2sd(v), abs(dd['base_margin'])

    ff10, m10 = band_floor_A(r10)
    fa10, _ = band_floor_A(r18)
    m_all, m_cor = b['margin_all_items'], b['margin_baseline_correct_only']
    out['task_A'] = {'floor_final': ff10, 'floor_all': fa10, 'margin': m10,
                     'margin_definition': 'baseline-correct-only (R10 run.py:273)'}

    res_rows = {}
    for scope, f10 in (('final', ff10), ('all', fa10)):
        s = out['scopes'][scope]
        A = f10 / m10
        res_rows[scope] = {
            'published': (s['floor_full'] / m_all) / A,
            'denominator_matched': (s['floor_full'] / m_cor) / A,
            'fully_matched': (s['floor_restricted'] / m_cor) / A}
    out['residuals'] = res_rows
    out['margin_ratio_published'] = m_all / m10
    out['margin_ratio_matched'] = m_cor / m10
    out['same_direction_published'] = ((res_rows['final']['published'] - 1)
                                       * (res_rows['all']['published'] - 1) > 0)
    out['same_direction_denominator_matched'] = ((res_rows['final']['denominator_matched'] - 1)
                                                 * (res_rows['all']['denominator_matched'] - 1) > 0)
    out['same_direction_fully_matched'] = ((res_rows['final']['fully_matched'] - 1)
                                           * (res_rows['all']['fully_matched'] - 1) > 0)

    # registered verdict on the numerator question
    any_outside = any(out['scopes'][s]['outside_central_95'] for s in ('final', 'all'))
    out['numerator_verdict'] = 'NUMERATOR-MATTERS' if any_outside else 'NUMERATOR-IS-CELL-COUNT'
    if not all(out['scopes'][s]['reconstruction_ok'] for s in ('final', 'all')):
        out['numerator_verdict'] = 'UNVERIFIED_RECONSTRUCTION_FAILED'

    op = ROUND / 'results' / 'r19_matched_denominator.json'
    json.dump(out, open(op, 'w'), indent=1)

    print(f'  cells kept {n_keep}/{NB * NP}   by n_correct {out["cells_by_n_correct"]}')
    print(f'  position composition kept {out["position_composition_kept"]} of {[NB] * NP}')
    print(f'  margin  all {m_all:+.4f}   correct-only {m_cor:+.4f}   '
          f'wrong-only {out["margin_wrong_only"]:+.4f}')
    for scope in ('final', 'all'):
        s = out['scopes'][scope]
        print(f'  [{scope:5s}] recon err {s["reconstruction_max_abs_err"]:.2e} '
              f'({"OK" if s["reconstruction_ok"] else "FAILED"})   '
              f'floor {s["floor_full"]:.6f} -> {s["floor_restricted"]:.6f}   '
              f'random-drop {s["random_drop_mean"]:.6f} '
              f'[{s["random_drop_ci95"][0]:.6f},{s["random_drop_ci95"][1]:.6f}]   '
              f'pct {s["restricted_percentile_of_random"]:.4f}   '
              f'outside95 {s["outside_central_95"]}')
        print(f'          POST HOC position-matched null {s["posmatched_drop_mean"]:.6f} '
              f'[{s["posmatched_drop_ci95"][0]:.6f},{s["posmatched_drop_ci95"][1]:.6f}]   '
              f'pct {s["restricted_percentile_of_posmatched"]:.4f}   '
              f'outside95 {s["outside_central_95_posmatched"]}')
        r = res_rows[scope]
        print(f'          residual  published {r["published"]:.4f}   '
              f'denominator-matched {r["denominator_matched"]:.4f}   '
              f'fully-matched {r["fully_matched"]:.4f}')
    print(f'  margin ratio B/A  published {out["margin_ratio_published"]:.4f} -> '
          f'matched {out["margin_ratio_matched"]:.4f}')
    print(f'  same direction in both scopes:  published {out["same_direction_published"]}  '
          f'denom-matched {out["same_direction_denominator_matched"]}  '
          f'fully-matched {out["same_direction_fully_matched"]}')
    print(f'  NUMERATOR VERDICT: {out["numerator_verdict"]}')
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
