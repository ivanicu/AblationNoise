"""EMITTER for results/r19_split_structure.json -- D139, and the distinction it needs.

A reviewer found that bases 0-31 vs 32-63 is the ONE split balanced on both design factors, and that
splitting by ROOM gives a near-zero correlation. That is true. But it makes two different questions
look like one:

  REPLICATE RELIABILITY -- does a 32-base estimate replicate ANOTHER 32-base estimate drawn the same
  way? This is the ceiling disattenuation needs, and a BALANCED split is the correct one for it,
  because an unbalanced split confounds replicate noise with a design factor.

  CROSS-CONDITION GENERALISATION -- does the head profile survive changing a design factor? A
  room-split answers this. It is NOT a reliability, and using it as a disattenuation ceiling would
  correct for a real effect rather than for noise.

Both are computed here and labelled, because reporting only the maximum was the defect and reporting
only the minimum would be the same defect mirrored.

    python3 R19_crossed_position_support/tools/split_structure.py
"""
import json, math, os

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = json.load(open('R19_crossed_position_support/results/r19_crossed_qwen2.5-1.5b.json'))
C, NB = D['cells'], D['n_base']
BAND = [(L, h) for L in range(14, D['n_layers']) for h in range(D['n_heads_per_layer'])]
NAMES = D.get('eligible_query_names', [])
ROOMS = D['rooms']


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0] * len(v); i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]: j += 1
        a = (i + j) / 2.0 + 1
        for k in range(i, j + 1): r[o[k]] = a
        i = j + 1
    return r


def pear(x, y):
    n = len(x); mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x)); sy = math.sqrt(sum((b - my) ** 2 for b in y))
    return sum((x[i] - mx) * (y[i] - my) for i in range(n)) / (sx * sy) if sx and sy else 0.0


def spear(x, y): return pear(rank(x), rank(y))


def prof(scope, mi, idx):
    """|centred| head profile from a subset of bases -- the quantity analyze.py:187 correlates."""
    v = [sum(C['L%02dH%02d.%s' % (k[0], k[1], scope)]['base'][i][mi] for i in idx) / len(idx)
         for k in BAND]
    mu = sum(v) / len(v)
    return [abs(x - mu) for x in v]


# b % 8 fixes the query name; b % 4 fixes the answer room; the two are aliased
SPLITS = {
    'contiguous_balanced':   (list(range(0, 32)), list(range(32, 64)), 'BALANCED on name AND room'),
    'by_name_group':         ([b for b in range(NB) if (b % 8) < 4],
                              [b for b in range(NB) if (b % 8) >= 4], 'splits NAME, room balanced'),
    'by_room':               ([b for b in range(NB) if (b % 4) < 2],
                              [b for b in range(NB) if (b % 4) >= 2], 'splits ROOM and name'),
    'even_odd':              ([b for b in range(NB) if b % 2 == 0],
                              [b for b in range(NB) if b % 2 == 1], 'splits ROOM and name'),
}
out = {'n_base': NB, 'n_band': len(BAND), 'rooms': ROOMS, 'query_names': NAMES,
       'note': 'contiguous_balanced is the REPLICATE reliability and the only one admissible as a '
               'disattenuation ceiling; the others are CROSS-CONDITION GENERALISATION and are '
               'reported as findings about the task, not about noise.',
       'per_metric': {}}
for mi, name in enumerate(D['metrics']):
    e = {}
    for tag, (A, B, what) in SPLITS.items():
        e[tag] = {'what_it_measures': what,
                  'final': spear(prof('final', mi, A), prof('final', mi, B)),
                  'all': spear(prof('all', mi, A), prof('all', mi, B))}
    out['per_metric'][name] = e
json.dump(out, open('R19_crossed_position_support/results/r19_split_structure.json', 'w'), indent=1)
for n, e in out['per_metric'].items():
    print(n)
    for tag, v in e.items():
        print('   %-22s final %+.4f  all %+.4f   %s' % (tag, v['final'], v['all'], v['what_it_measures']))
