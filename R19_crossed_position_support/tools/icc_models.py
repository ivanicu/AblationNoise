"""EMITTER for results/r19_icc_models.json -- D140.

An independent reviewer established that analyze.py::icc1 is ICC(1,1), the ONE-WAY model, valid when
each subject is rated by a DIFFERENT randomly drawn set of raters. R19's design is fully CROSSED --
every base is measured at the SAME 8 positions -- so ICC(3,1) is the appropriate estimator. ICC(1,1)
charges the position MAIN EFFECT to the error term, and there is a large one:
baseline_margin_by_pos spans 4.02 to 0.51.

THE PRE-REGISTRATION NAMED ICC(1,1) EXPLICITLY (Amendment 1), so the registered verdict stands and is
NOT switched here. What this shows is that the pre-registration registered the wrong MODEL for its
own design -- a different failure from a wrong number, and one a threshold cannot protect against.

    python3 R19_crossed_position_support/tools/icc_models.py
"""
import json, os, statistics

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = json.load(open('R19_crossed_position_support/results/r19_crossed_qwen2.5-1.5b.json'))
C = D['cells']
BAND = [(L, h) for L in range(14, D['n_layers']) for h in range(D['n_heads_per_layer'])]
THRESH = 0.50                       # registered in PREREGISTRATION.md Amendment 1


def components(rows):
    """Two-way ANOVA on a subjects x raters table with one observation per cell."""
    nb, npos = len(rows), len(rows[0])
    grand = sum(sum(r) for r in rows) / (nb * npos)
    rowm = [sum(r) / npos for r in rows]
    colm = [sum(rows[b][p] for b in range(nb)) / nb for p in range(npos)]
    msb = npos * sum((m - grand) ** 2 for m in rowm) / (nb - 1)
    mse = sum((rows[b][p] - rowm[b] - colm[p] + grand) ** 2
              for b in range(nb) for p in range(npos)) / ((nb - 1) * (npos - 1))
    msw = sum(sum((v - rowm[b]) ** 2 for v in rows[b]) for b in range(nb)) / (nb * (npos - 1))
    return nb, npos, msb, mse, msw


out = {'threshold': THRESH, 'n_band': len(BAND), 'per_metric': {}}
for mi, name in enumerate(D['metrics']):
    i11, i31 = [], []
    for k in BAND:
        # THE SCOPE MUST MATCH analyze.py:215, WHICH USES '.all'. The first version of this
        # tool read '.final' and produced 0.4906 / 0.5871 against the analysis's 0.4737 --
        # a discrepancy that looked like implementations disagreeing and was me comparing
        # unlike with unlike, the same defect a reviewer had just caught in
        # margin_normalisation(). Read the object: analyze.py names the scope on line 215.
        rows = [[c[mi] for c in row] for row in C['L%02dH%02d.all' % k]['base_pos']]
        nb, npos, msb, mse, msw = components(rows)
        den1 = msb + (npos - 1) * msw
        i11.append((msb - msw) / den1 if den1 else float('nan'))
        den3 = msb + (npos - 1) * mse
        i31.append((msb - mse) / den3 if den3 else float('nan'))
    m1, m3 = statistics.median(i11), statistics.median(i31)
    out['per_metric'][name] = {
        'icc_1_1_median': m1, 'icc_3_1_median': m3, 'delta': m3 - m1,
        'registered_estimator': 'ICC(1,1)',
        'crosses_threshold_under_3_1': m3 >= THRESH,
        'crosses_threshold_under_1_1': m1 >= THRESH,
        'verdict_would_change': (m3 >= THRESH) != (m1 >= THRESH)}
json.dump(out, open('R19_crossed_position_support/results/r19_icc_models.json', 'w'), indent=1)
for n, v in out['per_metric'].items():
    print('%-20s ICC(1,1) %.4f  ICC(3,1) %.4f  delta %+.4f  | crosses under 1,1: %s  under 3,1: %s'
          '  component verdict changes: %s'
          % (n, v['icc_1_1_median'], v['icc_3_1_median'], v['delta'],
             v['crosses_threshold_under_1_1'], v['crosses_threshold_under_3_1'],
             v['verdict_would_change']))
