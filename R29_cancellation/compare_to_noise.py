#!/usr/bin/env python3
"""Is the replay's discrepancy distribution the batch-noise distribution? Shape against shape.

The registered control compared a MAX over 336 or 576 cells to a fixed absolute bound. That is the one
statistic numerical noise controls, so it could not distinguish "the pipeline is wrong" from "an extreme
value over many draws". The discriminating fact is elsewhere:

    a genuine implementation error moves the MEDIAN of the discrepancy distribution
    batch-vs-no-batch noise moves only its TAIL

So the comparison is `median(D) / M`, where D is the per-cell |replayed mean - published mean| the scan
already emits and M is the measured median chunk-1-vs-chunk-40 spread for that support and model. Both
are medians; the ratio is dimensionless; a wrong ablation site, a padded batch reading the wrong position,
or a slice on the wrong axis all move it by orders of magnitude.

M COMES FROM AN UNBIASED SAMPLE and that mattered: the first probe drew heads {0,1} only -- one whole KV
group -- and gave 8.484e-07 for I_final where 56 seeded-random cells give 1.541e-06, understating the
noise by 1.8x. A ratio is only as good as its denominator's population.

NO TOLERANCE IS APPLIED HERE. The ratios are the output; the rule that reads them is not this file's.
"""
import json
import pathlib
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve().parent
PAIRS = [('qwen2.5-1.5b', 'I_final', 'r29_scan_qwen2.5-1.5b_I_final_off0.json'),
         ('qwen2.5-1.5b', 'I_all', 'r29_scan_qwen2.5-1.5b_I_all_off0.json'),
         ('qwen2.5-3b', 'I_final', 'r29_scan_qwen2.5-3b_I_final_off0.json'),
         ('qwen2.5-3b', 'I_all', 'r29_scan_qwen2.5-3b_I_all_off0.json')]


def main():
    out = {'note': 'shape of the replay discrepancy against the measured batch-noise scale'}
    noise = {}
    for tag in ('qwen2.5-1.5b', 'qwen2.5-3b'):
        f = HERE / 'results' / f'r29_batch_noise_{tag}.json'
        if f.exists():
            d = json.load(open(f))
            noise[tag] = {k: v['median'] for k, v in d['supports'].items()}
            noise[tag]['n_cells_probed'] = d['n_cells_probed']
    out['noise_medians'] = noise
    print('  measured batch-noise medians M (chunk 1 vs 40, seeded random heads)')
    for tag, v in noise.items():
        print(f"    {tag:<14} I_final {v.get('I_final', float('nan')):.3e}   "
              f"I_all {v.get('I_all', float('nan')):.3e}   over {v['n_cells_probed']} cells")

    print(f"\n  {'cell':<24}{'n':<6}{'median(D)':<13}{'M':<13}{'med/M':<9}{'max/med':<10}"
          f"control")
    rows = {}
    for tag, sup, fn in PAIRS:
        f = HERE / 'results' / fn
        if not f.exists() or tag not in noise or sup not in noise[tag]:
            continue
        d = json.load(open(f))
        cp = d.get('control_per_cell')
        if not cp:
            continue
        D = sorted(v['delta_mean'] for v in cp.values())
        med, mx = st.median(D), D[-1]
        M = noise[tag][sup]
        rows[f'{tag}|{sup}'] = {
            'n_cells': len(D), 'median_D': med, 'max_D': mx, 'M': M,
            'median_over_M': med / M, 'max_over_median': mx / med,
            'p90_D': D[max(0, int(0.9 * len(D)) - 1)],
            'control_pass_as_registered': d['control']['pass'],
            'base_abs_delta': abs(d['base_margin_replayed'] - d['base_margin_frozen'])}
        r = rows[f'{tag}|{sup}']
        print(f"    {tag + '|' + sup:<24}{len(D):<6}{med:<13.3e}{M:<13.3e}"
              f"{r['median_over_M']:<9.2f}{r['max_over_median']:<10.2f}"
              f"{d['control']['pass']}")
    out['cells'] = rows
    if rows:
        mm = [v['median_over_M'] for v in rows.values()]
        out['median_over_M_range'] = [min(mm), max(mm)]
        print(f"\n  median(D)/M across cells: {min(mm):.2f} to {max(mm):.2f}")
        print('  A median at the noise scale means the TYPICAL cell reproduces the published mean to '
              'within\n  what batching alone moves it. Whatever fails, fails in the tail.')
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r29_compare_to_noise.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
