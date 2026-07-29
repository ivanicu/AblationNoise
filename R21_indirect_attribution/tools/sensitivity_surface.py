#!/usr/bin/env python3
"""R21's class share across every defensible population x denominator. NO VERDICT IS COMPUTED.

Two reviews established that `ATT 0.4845` is one cell of a grid, and that the registered `0.50`
threshold sits inside the grid's range. A quantity that moves from one side of its own threshold to
the other under choices the pre-registration never justified is not identified, and reporting a point
value for it would be the repository's own overshoot -- a number reported without the scope over
which it holds.

So this emits the surface and stops. It is POST HOC: the grid's shape was seen (in a reviewer's
report) before this file was written, which is why no threshold is applied to it here and why the
verdict stays `UNVERIFIED` on control 1 rather than being recovered from a cell that looks better.

The three denominators, all of which are defensible readings of "share":

    abs        |c| / SUM|c|      the registered one. Caps every share; no class can exceed 0.50
                                 unless it exceeds the sum of the absolute values of all others.
    signed      c  / SUM c       shares sum to 1 and the denominator IS the indirect term.
    abs_signed |c  / SUM c|      as above, magnitude only.
"""
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROUND = HERE.parent
REPO = ROUND.parent
NL, NH = 28, 12
BAND = [(L, h) for L in range(14, 28) for h in range(NH)]
K = lambda t: 'L%02dH%02d' % t
CLASSES = ('att', 'mlp', 'emb', 'norm')


def med(v):
    w = sorted(v)
    n = len(w)
    return w[n // 2] if n % 2 else 0.5 * (w[n // 2 - 1] + w[n // 2])


def main():
    C = json.load(open(ROUND / 'results' / 'r21_indirect_qwen2.5-1.5b.json'))['cells']
    r20 = json.load(open(REPO / 'R20_direct_indirect' / 'results'
                         / 'r20_direct_indirect_qwen2.5-1.5b.json'))['cells']
    r10 = json.load(open(REPO / 'R10_exhaustive' / 'results'
                         / 'r10_exhaustive_qwen2.5-1.5b.json'))['layers']
    lay = {int(k): v for k, v in r10.items()}
    bm = abs(json.load(open(REPO / 'R10_exhaustive' / 'results'
                            / 'r10_exhaustive_qwen2.5-1.5b.json'))['base_margin'])

    tot = {k: C[K(k)]['total_r10'] for k in BAND}
    # R10 stores `floor` as sd/|base_margin|, a FRACTION; `total_r10` is an absolute drop. Both
    # conventions are used in this repository -- R7's operative test is |pc| > sd -- so both are
    # applied, and the disagreement between them is part of the surface.
    floor_frac = {k: lay[k[0]]['floor'] for k in BAND}
    floor_sd = {k: lay[k[0]]['sd'] for k in BAND}
    q = sorted(BAND, key=lambda k: abs(tot[k]))
    pops = {
        'band168_registered': BAND,
        'stable44_control_passes': [k for k in BAND if r20[K(k)]['comparator_flip_rate'] == 0.0],
        'usable122_R20_rule': [k for k in BAND if abs(r20[K(k)]['direct_renorm']) >= 0.01],
        'above_floor_frac': [k for k in BAND if abs(tot[k]) / bm > floor_frac[k]],
        'below_floor_frac': [k for k in BAND if abs(tot[k]) / bm <= floor_frac[k]],
        'above_layer_sd_R7': [k for k in BAND if abs(tot[k]) > floor_sd[k]],
        'Q4_largest_quarter': q[126:],
        'Q1_smallest_quarter': q[:42],
    }

    def shares(pop, mode):
        out = {}
        for c in CLASSES:
            v = []
            for k in pop:
                cell = C[K(k)]
                d = (sum(abs(cell[x]) for x in CLASSES) if mode == 'abs'
                     else sum(cell[x] for x in CLASSES))
                if d == 0:
                    continue
                s = cell[c] / d
                v.append(abs(s) if mode in ('abs', 'abs_signed') else s)
            out[c] = med(v) if v else float('nan')
        return out

    grid, att_all = {}, []
    print(f'  {"population":<26} {"n":>4}   {"denominator":<11} '
          f'{"ATT":>8} {"MLP":>8} {"NORM":>8}   top')
    for pname, pop in pops.items():
        grid[pname] = {'n': len(pop), 'cells': {}}
        for mode in ('abs', 'signed', 'abs_signed'):
            sh = shares(pop, mode)
            top = max(CLASSES, key=lambda c: sh[c])
            grid[pname]['cells'][mode] = {**sh, 'top': top}
            att_all.append(sh['att'])
            print(f'  {pname:<26} {len(pop):>4}   {mode:<11} '
                  f'{sh["att"]:8.4f} {sh["mlp"]:8.4f} {sh["norm"]:8.4f}   {top.upper()}')
    lo, hi = min(att_all), max(att_all)
    n_above = sum(1 for x in att_all if x >= 0.50)
    n_top = sum(1 for p in grid.values() for c in p['cells'].values() if c['top'] == 'att')
    out = {'grid': grid, 'n_cells': len(att_all),
           'att_share_min': lo, 'att_share_max': hi, 'att_share_range': hi - lo,
           'n_cells_att_at_or_above_half': n_above,
           'n_cells_att_is_top_class': n_top,
           'registered_threshold_inside_range': lo < 0.50 < hi,
           'registered_cell_att': grid['band168_registered']['cells']['abs']['att'],
           'control_passing_cell_att': grid['stable44_control_passes']['cells']['abs']['att'],
           'note': 'no verdict is computed here; the surface is the result'}
    op = ROUND / 'results' / 'r21_sensitivity_surface.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  ATT share over {len(att_all)} cells: min {lo:.4f}  max {hi:.4f}  range {hi - lo:.4f}')
    print(f'  cells where ATT >= 0.50: {n_above} of {len(att_all)}   '
          f'cells where ATT is the top class: {n_top}')
    print(f'  the registered 0.50 threshold lies INSIDE the range: '
          f'{out["registered_threshold_inside_range"]}')
    print(f'  registered cell {out["registered_cell_att"]:.4f}   '
          f'control-passing cell {out["control_passing_cell_att"]:.4f}')
    print('  NO VERDICT IS COMPUTED. The surface is the result.')
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
