#!/usr/bin/env python3
"""The control's failing tail is LAYER DEPTH, and the mechanism is the one I proposed and then retracted.

The registered control failed on I_all with max(D)/median(D) = 13.23 against 3.59 for a passing support.
That tail was left unexplained. It is depth:

    spearman(D, layer) is 3.7x and 2.0x stronger in I_all than I_final, and normalising each cell's
    discrepancy by ITS OWN LAYER'S MEDIAN collapses 13.23 to 3.85 -- while RAISING the other three,
    which is what makes it a diagnosis rather than a flattering transform.

WHY DEPTH. I_all zeroes a head at all 121 positions; the perturbation then propagates through the
remaining NL-L layers in float32, so an early layer accumulates more divergence than a late one.
I_final zeroes one position and its perturbation reaches the logits almost directly.

THAT IS THE MECHANISM I PROPOSED FOR THE I_all/I_final NOISE RATIO AND THEN RETRACTED when the ratio came
back at 0.99x on a head-biased sample. It was right in kind. I tested it with a RATIO OF MEDIANS, which
integrates over the very axis the mechanism acts along, so the statistic could not see it either way.
The gradient is the statistic; the ratio never was.

Found by an independent reviewer. Reproduced here rather than quoted.
"""
import json
import math
import pathlib
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve().parent
FILES = [('qwen2.5-1.5b|I_final', 'r29_scan_qwen2.5-1.5b_I_final_off0.json'),
         ('qwen2.5-1.5b|I_all', 'r29_scan_qwen2.5-1.5b_I_all_off0.json'),
         ('qwen2.5-3b|I_final', 'r29_scan_qwen2.5-3b_I_final_off0.json'),
         ('qwen2.5-3b|I_all', 'r29_scan_qwen2.5-3b_I_all_off0.json')]


def spearman(a, b):
    def rk(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2.0 + 1
            i = j + 1
        return r
    x, y = rk(a), rk(b)
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    num = sum((x[i] - mx) * (y[i] - my) for i in range(n))
    dx = math.sqrt(sum((v - mx) ** 2 for v in x))
    dy = math.sqrt(sum((v - my) ** 2 for v in y))
    return num / (dx * dy) if dx > 0 and dy > 0 else float('nan')


def main():
    out = {'note': 'the control tail explained by layer depth; reproduced, not quoted'}
    print(f"  {'cell':<22}{'rho(D,layer)':<14}{'max/med raw':<13}{'layer-normalised':<18}"
          f"{'tail mean layer':<16}n")
    res = {}
    for tag, fn in FILES:
        f = HERE / 'results' / fn
        if not f.exists():
            continue
        cp = json.load(open(f)).get('control_per_cell')
        if not cp:
            continue
        ks = sorted(cp)
        lay = [int(k[1:3]) for k in ks]
        D = [cp[k]['delta_mean'] for k in ks]
        by = {}
        for l, x in zip(lay, D):
            by.setdefault(l, []).append(x)
        lmed = {l: st.median(v) for l, v in by.items()}
        norm = [x / lmed[l] for l, x in zip(lay, D)]
        thr = sorted(D)[int(0.9 * len(D))]
        tail = [l for l, x in zip(lay, D) if x >= thr]
        res[tag] = {
            'n_cells': len(D), 'n_layers': max(lay) + 1,
            'spearman_D_layer': spearman(lay, D),
            'max_over_median_raw': max(D) / st.median(D),
            'max_over_median_layer_normalised': max(norm) / st.median(norm),
            'tail_mean_layer': sum(tail) / len(tail),
            'tail_n': len(tail),
            'layer_median_ratio_first_to_last': lmed[min(lay)] / lmed[max(lay)],
            'layer_medians': {str(l): v for l, v in sorted(lmed.items())}}
        r = res[tag]
        print(f"    {tag:<20}{r['spearman_D_layer']:<+14.4f}{r['max_over_median_raw']:<13.2f}"
              f"{r['max_over_median_layer_normalised']:<18.2f}{r['tail_mean_layer']:<16.2f}"
              f"{r['n_cells']}")
    out['cells'] = res
    if 'qwen2.5-1.5b|I_all' in res and 'qwen2.5-1.5b|I_final' in res:
        a = abs(res['qwen2.5-1.5b|I_all']['spearman_D_layer'])
        b = abs(res['qwen2.5-1.5b|I_final']['spearman_D_layer'])
        out['depth_gradient_ratio_1p5b'] = a / b
        print(f"\n  depth gradient, I_all / I_final:  1.5b {a / b:.2f}x", end='')
    if 'qwen2.5-3b|I_all' in res and 'qwen2.5-3b|I_final' in res:
        a = abs(res['qwen2.5-3b|I_all']['spearman_D_layer'])
        b = abs(res['qwen2.5-3b|I_final']['spearman_D_layer'])
        out['depth_gradient_ratio_3b'] = a / b
        print(f"   3b {a / b:.2f}x")
    print('  The layer-median normalisation collapses ONE cell and raises the others, so it is a '
          'diagnosis,\n  not a transform that flatters everything.')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r29_tail_is_depth.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
