"""EMITTER for results/r19_clustered_ci.json -- the honest interval for D138.

An independent reviewer established that the 64 base instances are NOT exchangeable: run.py sets
`query = elig[b % 8]` and `want = rooms[b % 4]`, and since 4 divides 8 the query name perfectly
determines the answer room. There are 8 distinct (query, answer-room) cells, each replicated 8x, and
the base-level tau is dominated by which cell it is in -- measured ICC ~0.62, design effect ~5.35,
EFFECTIVE n about 12 rather than 64.

The published CI resampled 64 bases as if independent. This resamples the 8 GROUPS with replacement,
carrying all 8 of a group's bases together, which is what a cluster bootstrap on this design means.
With 8 clusters the interval is coarse BY CONSTRUCTION -- that coarseness is the finding, not a
defect of the method.

    python3 R19_crossed_position_support/tools/clustered_ci.py
"""
import json, math, os, random
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = json.load(open('R19_crossed_position_support/results/r19_crossed_qwen2.5-1.5b.json'))
C, NB = D['cells'], D['n_base']
BAND = [(L, h) for L in range(14, D['n_layers']) for h in range(D['n_heads_per_layer'])]
N_BOOT = 2000

def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i]); r = [0.0]*len(v); i = 0
    while i < len(o):
        j = i
        while j+1 < len(o) and v[o[j+1]] == v[o[i]]: j += 1
        a = (i+j)/2.0 + 1
        for k in range(i, j+1): r[o[k]] = a
        i = j+1
    return r

def pear(x, y):
    n = len(x); mx, my = sum(x)/n, sum(y)/n
    sx = math.sqrt(sum((a-mx)**2 for a in x)); sy = math.sqrt(sum((b-my)**2 for b in y))
    return sum((x[i]-mx)*(y[i]-my) for i in range(n))/(sx*sy) if sx and sy else 0.0

def spear(x, y): return pear(rank(x), rank(y))

# the 8 aliased cells: base b belongs to group b % 8, which fixes BOTH query name and answer room
GROUPS = {g: [b for b in range(NB) if b % 8 == g] for g in range(8)}
out = {'n_groups': len(GROUPS), 'group_size': len(GROUPS[0]), 'n_boot': N_BOOT,
       'grouping': 'b % 8 -- fixes query name AND answer room simultaneously', 'per_metric': {}}
rng = random.Random(20260728)
for mi, name in enumerate(D['metrics']):
    def rho_over(bases):
        tf, ta = {}, {}
        for k in BAND:
            cf = C['L%02dH%02d.final' % k]['base']; ca = C['L%02dH%02d.all' % k]['base']
            tf[k] = sum(cf[b][mi] for b in bases)/len(bases)
            ta[k] = sum(ca[b][mi] for b in bases)/len(bases)
        muf, mua = sum(tf.values())/len(tf), sum(ta.values())/len(ta)
        return spear([abs(tf[k]-muf) for k in BAND], [abs(ta[k]-mua) for k in BAND])
    point = rho_over(list(range(NB)))
    base_boot, grp_boot = [], []
    for _ in range(N_BOOT):
        base_boot.append(rho_over([rng.randrange(NB) for _ in range(NB)]))
        gs = [rng.randrange(8) for _ in range(8)]
        grp_boot.append(rho_over([b for g in gs for b in GROUPS[g]]))
    base_boot.sort(); grp_boot.sort()
    lo_b, hi_b = base_boot[int(.025*N_BOOT)], base_boot[int(.975*N_BOOT)]
    lo_g, hi_g = grp_boot[int(.025*N_BOOT)], grp_boot[int(.975*N_BOOT)]
    out['per_metric'][name] = {
        'point': point,
        'ci_base_resample': [lo_b, hi_b], 'width_base': hi_b - lo_b,
        'ci_group_clustered': [lo_g, hi_g], 'width_group': hi_g - lo_g,
        'width_ratio': (hi_g - lo_g)/(hi_b - lo_b) if hi_b > lo_b else float('nan'),
        'clustered_upper_reaches_0_9': hi_g >= 0.9}
json.dump(out, open('R19_crossed_position_support/results/r19_clustered_ci.json', 'w'), indent=1)
for n, v in out['per_metric'].items():
    print('%-20s point %.4f | base CI [%+.4f,%+.4f] w=%.4f | GROUP CI [%+.4f,%+.4f] w=%.4f  %.2fx wider  upper>=0.9: %s'
          % (n, v['point'], v['ci_base_resample'][0], v['ci_base_resample'][1], v['width_base'],
             v['ci_group_clustered'][0], v['ci_group_clustered'][1], v['width_group'],
             v['width_ratio'], v['clustered_upper_reaches_0_9']))
