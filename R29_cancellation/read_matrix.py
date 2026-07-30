#!/usr/bin/env python3
"""Read R29's registered prediction matrix, per (model, support, item set). One cell per scan file.

The five coordinates and their thresholds are R29_cancellation/PREREGISTRATION.md's, unchanged:

    [ sd_w(Lambda | log rms) nats , lambda1/sum , split-half r(Lam1,Lam2 | log rms) ,
      med max|Delta|/rms , med sign frac ]

    W1 head property     >= 0.40   <= 0.60   >= 0.60   <= 4.5   >= 0.65
    W2 degenerate ratio  >= 0.40   <= 0.60   <= 0.25   <= 4.5   <= 0.55
    W3 few items         >= 0.40   <= 0.60   >= 0.60   >= 6.5   <= 0.55

No `or` anywhere: a world is read only if every one of its five conditions holds. All-miss is a fourth
outcome and is reported as such.

TWO GATES FROM THE REGISTRATION ARE ENFORCED HERE, NOT ASSUMED:
  · the scan's own positive control must have passed, or the cell contributes nothing;
  · if the median jackknife SE of Lambda exceeds 0.15 nats, coordinate 1's low side is below the
    instrument's floor and the cell returns UNVERIFIED on that coordinate rather than passing it.
The split-half correlation is gated on the RAW value; Spearman-Brown is reported beside it and never
decides, because a ceiling statement may not be the thing that passes.

The decision needs >= 3 of 4 cells and is NEVER pooled. With fewer than four scans on disk this file says
how many are missing and reads no verdict.
"""
import json
import math
import pathlib
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve().parent
JK_GATE = 0.15
W = {'W1_head_property': {'sd_w': ('ge', 0.40), 'lam1': ('le', 0.60), 'split': ('ge', 0.60),
                          'maxrms': ('le', 4.5), 'sign': ('ge', 0.65)},
     'W2_degenerate_ratio': {'sd_w': ('ge', 0.40), 'lam1': ('le', 0.60), 'split': ('le', 0.25),
                             'maxrms': ('le', 4.5), 'sign': ('le', 0.55)},
     'W3_few_items': {'sd_w': ('ge', 0.40), 'lam1': ('le', 0.60), 'split': ('ge', 0.60),
                      'maxrms': ('ge', 6.5), 'sign': ('le', 0.55)}}
N_CELLS_REQUIRED = 4
N_CELLS_TO_DECIDE = 3


def resid(y, x):
    n = len(y)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x)
    b = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / sxx if sxx > 0 else 0.0
    return [y[i] - my - b * (x[i] - mx) for i in range(n)]


def pear(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((a[i] - ma) * (b[i] - mb) for i in range(n))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((x - mb) ** 2 for x in b))
    return num / (da * db) if da > 0 and db > 0 else float('nan')


def coords(d):
    per = d['per_cell']
    lays = sorted({v['layer'] for v in per.values()})
    sds, rs = [], []
    for L in lays:
        g = [v for v in per.values() if v['layer'] == L and v['Lambda'] == v['Lambda']]
        if len(g) >= 5:
            r = resid([v['Lambda'] for v in g], [v['G'] for v in g])
            sds.append(math.sqrt(sum(x * x for x in r) / (len(r) - 1)))
        h = [v for v in g if v['lambda_half1'] == v['lambda_half1']
             and v['lambda_half2'] == v['lambda_half2']]
        if len(h) >= 5:
            c = pear(resid([v['lambda_half1'] for v in h], [v['G'] for v in h]),
                     resid([v['lambda_half2'] for v in h], [v['G'] for v in h]))
            if c == c:
                rs.append(c)
    eg = d['layer_eigen']
    raw = st.median([v['lambda1_share_raw'] for v in eg.values()])
    mp = [v['lambda1_share_mean_projected'] for v in eg.values()
          if v['lambda1_share_mean_projected']]
    r_raw = sum(rs) / len(rs)
    return {
        'sd_w': sum(sds) / len(sds),
        'lam1': raw,
        'lam1_mean_projected': st.median(mp) if mp else None,
        'lam1_null_iid': st.median([v['null_iid_median'] for v in eg.values()]),
        'lam1_null_resign': st.median([v['null_resign_median'] for v in eg.values()]),
        'split': r_raw,
        'split_spearman_brown_reported_only': 2 * r_raw / (1 + r_raw),
        'maxrms': st.median([v['max_over_rms'] for v in per.values()]),
        'sign': st.median([v['sign_frac'] for v in per.values()]),
        'jackknife_se_median_nats': d['median_lambda_jackknife_se_nats'],
        'n_cells': len(per)}


def main():
    files = sorted((HERE / 'results').glob('r29_scan_*.json'))
    out = {'jk_gate_nats': JK_GATE, 'n_cells_required': N_CELLS_REQUIRED,
           'n_cells_to_decide': N_CELLS_TO_DECIDE, 'cells': {}}
    print(f'  scan files on disk: {len(files)} of {N_CELLS_REQUIRED} required')
    for f in files:
        d = json.load(open(f))
        key = f'{d["model"]}|{d["support"]}|off{d["seed_offset"]}'
        if not d.get('control', {}).get('pass'):
            out['cells'][key] = {'contributes': False,
                                 'reason': 'positive control did not pass'}
            print(f'    {key:<34} control FAILED -> contributes nothing')
            continue
        c = coords(d)
        jk_ok = c['jackknife_se_median_nats'] <= JK_GATE
        hits = {}
        for wn, conds in W.items():
            ok = all((c[k] >= v) if op == 'ge' else (c[k] <= v)
                     for k, (op, v) in conds.items())
            hits[wn] = ok
        n_true = sum(hits.values())
        read = ([k for k, v in hits.items() if v][0] if n_true == 1
                else 'ALL_MISS' if n_true == 0 else 'MULTIPLE_WORLDS_UNVERIFIED')
        out['cells'][key] = {'contributes': True, 'coords': c,
                             'coordinate1_above_instrument_floor': jk_ok,
                             'coordinate1_verdict': 'read' if jk_ok else 'UNVERIFIED',
                             'worlds_satisfied': hits, 'reading': read}
        print(f'\n    {key}   cells {c["n_cells"]}')
        print(f'      sd_w(Lambda|log rms) {c["sd_w"]:.4f} nats   jackknife floor '
              f'{c["jackknife_se_median_nats"]:.4f}  -> coordinate 1 '
              f'{"read" if jk_ok else "UNVERIFIED"}')
        print(f'      lambda1 share {c["lam1"]:.4f}  (mean-projected '
              f'{c["lam1_mean_projected"]:.4f}, iid null {c["lam1_null_iid"]:.4f}, '
              f'resign null {c["lam1_null_resign"]:.4f})')
        print(f'      split-half r RAW {c["split"]:.4f}  (Spearman-Brown '
              f'{c["split_spearman_brown_reported_only"]:.4f}, reported not gated)')
        print(f'      med max|Delta|/rms {c["maxrms"]:.4f}   med sign frac {c["sign"]:.4f}')
        print(f'      worlds satisfied: ' + ', '.join(k for k, v in hits.items() if v) +
              (f'   -> {read}' if n_true != 1 else f'   -> {read}'))

    # ⚠ A CELL IS (model x support), NOT A FILE. The first version counted scan files, so item set 0
    # and item set 400 of the SAME (model, support) counted as two cells -- which would let one
    # (model, support) supply two thirds of the required majority on its own. The registration lists
    # four cells, {1.5b, 3b} x {I_final, I_all}, and names the two item sets as REPLICATIONS for 1.5b.
    # Item sets are collapsed within a cell and must AGREE, or the cell is UNVERIFIED.
    bycell = {}
    for key, v in out['cells'].items():
        if not v.get('contributes'):
            continue
        model, support, off = key.split('|')
        bycell.setdefault(f'{model}|{support}', {})[off] = v['reading']
    collapsed = {}
    for cell, offs in bycell.items():
        rr = set(offs.values())
        collapsed[cell] = {'item_sets': offs,
                           'reading': (next(iter(rr)) if len(rr) == 1
                                       else 'ITEM_SETS_DISAGREE_UNVERIFIED')}
        print(f'    cell {cell:<26} item sets {offs}  -> {collapsed[cell]["reading"]}')
    out['collapsed_cells'] = collapsed
    agree = {}
    for v in collapsed.values():
        agree[v['reading']] = agree.get(v['reading'], 0) + 1
    out['readings_by_cell'] = agree
    good = list(collapsed.values())
    enough = len(good) >= N_CELLS_TO_DECIDE
    out['enough_cells_to_decide'] = enough
    if not enough:
        out['verdict'] = 'INCOMPLETE'
        print(f'\n  {len(good)} contributing cell(s). The registered rule needs '
              f'{N_CELLS_TO_DECIDE} of {N_CELLS_REQUIRED} and is NOT satisfiable yet. '
              f'NO VERDICT IS READ.')
    else:
        top = max(agree, key=agree.get)
        out['verdict'] = top if agree[top] >= N_CELLS_TO_DECIDE else 'NO_MAJORITY'
        print(f'\n  readings: {agree}   -> {out["verdict"]}')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r29_matrix.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
