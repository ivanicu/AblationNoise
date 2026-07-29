#!/usr/bin/env python3
"""Attack the R23 depth result: does it measure anything, or is it an artifact of how it was computed?

Run on Ivan's instruction -- "does this measure a real thing, or is it shit?" -- and it is the reason
Amendment 3 exists. Five attacks, all at the object, all emitted so the retraction cites a generator
rather than a transcript:

  1  what the descriptors ACTUALLY compute at n=12 and n=16 (q99 is the MAXIMUM)
  2  delete the top 1/2/3 heads per cell -- does the effect survive being about the whole population?
  3  n-dependence of a max-like statistic between cells of 12 and 16
  4  an ADJACENCY-PRESERVING null, because adjacent layers are not independent cells
  5  the shallow/deep split points, swept

Attack 2 is the one that changed the claim.
"""
import json
import math
import pathlib
import random
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import run as R, depth as D
rng=random.Random(97)
cells,meta=R.load_cells()
dep=[c['depth_frac'] for c in meta]
K=R.DESCRIPTORS

def strip_top(c,k):
    s=sorted(c,key=lambda x:-abs(x)); keep=s[k:]
    return keep if len(keep)>=6 else None

print('=== 1. IS IT JUST THE TOP HEAD(S)? delete the largest |effect| per cell and re-test ===')
for k in (0,1,2,3):
    cs,ds=[],[]
    for c,d in zip(cells,dep):
        cc = c if k==0 else strip_top(c,k)
        if cc: cs.append(cc); ds.append(d)
    row=[]
    for key in K:
        r=D.group_test(cs,ds,key,rng,1500)
        row.append('%s p=%.4f'%(key.replace('_abs_z','').replace('_z',''),r['p']))
    print('  drop top %d  (cells %d)  %s'%(k,len(cs),'  '.join(row)))

print()
print('=== 2. n-DEPENDENCE: same descriptors on PURE NOISE at n=12 vs n=16 ===')
for key in K:
    a=[R.descriptor([rng.gauss(0,1) for _ in range(12)],key) for _ in range(4000)]
    b=[R.descriptor([rng.gauss(0,1) for _ in range(16)],key) for _ in range(4000)]
    a=[x for x in a if x==x]; b=[x for x in b if x==x]
    print('  %-16s n=12 median %+8.4f   n=16 median %+8.4f   bias %+.4f'%(key,R.q(a,.5),R.q(b,.5),R.q(b,.5)-R.q(a,.5)))
n_lo=[len(c) for c,d in zip(cells,dep) if d<1/3]; n_hi=[len(c) for c,d in zip(cells,dep) if d>=2/3]
print('  shallow cells: %d of size 12, %d of size 16'%(n_lo.count(12),n_lo.count(16)))
print('  deep    cells: %d of size 12, %d of size 16'%(n_hi.count(12),n_hi.count(16)))

print()
print('=== 3. PER STRATUM: does it hold in all four, or is it one? ===')
by={}
for i,c in enumerate(meta): by.setdefault((c['model'],c['support']),[]).append(i)
for s,idx in sorted(by.items()):
    cs=[cells[i] for i in idx]; ds=[dep[i] for i in idx]
    row=[]
    for key in ('q99_abs_z','kurt_z','sd_over_mad_z'):
        r=D.group_test(cs,ds,key,rng,1500)
        row.append('%s p=%.4f d=%+.3f'%(key.replace('_abs_z','').replace('_z',''),r['p'],r['delta']))
    print('  %-28s %s'%('%s | %s'%s,'  '.join(row)))

print()
print('=== 4. NULL VALIDITY: permute WHOLE MODELS/SUPPORTS and CONTIGUOUS BLOCKS, not free cells ===')
def block_test(key,blk,nperm=1500):
    lo=[i for i,d in enumerate(dep) if d<1/3]; hi=[i for i,d in enumerate(dep) if d>=2/3]
    obs=D.med_desc([cells[i] for i in hi],key)-D.med_desc([cells[i] for i in lo],key)
    idxs=lo+hi
    groups=[idxs[i:i+blk] for i in range(0,len(idxs),blk)]
    lab=[0]*len(lo)+[1]*len(hi)
    null=[]
    for _ in range(nperm):
        gl=[rng.randrange(2) for _ in groups]
        A=[cells[i] for g,l in zip(groups,gl) for i in g if l==0]
        B=[cells[i] for g,l in zip(groups,gl) for i in g if l==1]
        if len(A)<6 or len(B)<6: continue
        null.append(D.med_desc(B,key)-D.med_desc(A,key))
    null.sort()
    return obs,(1+sum(1 for x in null if abs(x)>=abs(obs)))/(1+len(null))
for key in ('q99_abs_z','kurt_z','sd_over_mad_z','q90_abs_z'):
    o1,p1=block_test(key,1); o4,p4=block_test(key,4); o9,p9=block_test(key,9)
    print('  %-16s free-cell p=%.4f   block4 p=%.4f   block9 p=%.4f'%(key,p1,p4,p9))

print()
print('=== 5. SPLIT-POINT SWEEP ===')
for lo_t,hi_t in ((0.25,0.75),(1/3,2/3),(0.4,0.6),(0.5,0.5)):
    row=[]
    for key in ('q99_abs_z','kurt_z'):
        D.SHALLOW,D.DEEP=lo_t,hi_t
        r=D.group_test(cells,dep,key,rng,1500)
        row.append('%s p=%.4f (n %d/%d)'%(key.replace('_abs_z','').replace('_z',''),r['p'],r['n_shallow_cells'],r['n_deep_cells']))
    print('  shallow<%.2f deep>=%.2f   %s'%(lo_t,hi_t,'  '.join(row)))
D.SHALLOW,D.DEEP=1/3,2/3


# ---- emit, so the page quotes a generator
def emit():
    res = {'q_at_n': {n: {'q90': R.q(list(range(1, n + 1)), .90),
                          'q99': R.q(list(range(1, n + 1)), .99), 'max': n} for n in (12, 16)}}
    res['drop_top'] = {}
    for k in (0, 1, 2, 3):
        cs, ds = [], []
        for c, d in zip(cells, dep):
            cc = c if k == 0 else strip_top(c, k)
            if cc:
                cs.append(cc); ds.append(d)
        res['drop_top'][k] = {key: D.group_test(cs, ds, key, rng, 1500)['p'] for key in K}
    res['n_bias'] = {}
    for key in K:
        a = [x for x in (R.descriptor([rng.gauss(0, 1) for _ in range(12)], key)
                         for _ in range(4000)) if x == x]
        b = [x for x in (R.descriptor([rng.gauss(0, 1) for _ in range(16)], key)
                         for _ in range(4000)) if x == x]
        res['n_bias'][key] = {'n12_median': R.q(a, .5), 'n16_median': R.q(b, .5),
                              'bias': R.q(b, .5) - R.q(a, .5)}
    nl = [len(c) for c, d in zip(cells, dep) if d < 1 / 3]
    nh = [len(c) for c, d in zip(cells, dep) if d >= 2 / 3]
    res['group_composition'] = {'shallow_12': nl.count(12), 'shallow_16': nl.count(16),
                                'deep_12': nh.count(12), 'deep_16': nh.count(16)}
    res['per_stratum'] = {}
    for s, idx in sorted(by.items()):
        cs = [cells[i] for i in idx]; ds = [dep[i] for i in idx]
        res['per_stratum']['%s|%s' % s] = {
            key: {'p': D.group_test(cs, ds, key, rng, 1500)['p'],
                  'delta': D.group_test(cs, ds, key, rng, 1500)['delta']}
            for key in ('q99_abs_z', 'kurt_z', 'sd_over_mad_z')}
    res['block_null'] = {}
    for key in ('q99_abs_z', 'kurt_z', 'sd_over_mad_z', 'q90_abs_z'):
        res['block_null'][key] = {'free_cell': block_test(key, 1)[1],
                                  'block4': block_test(key, 4)[1],
                                  'block9': block_test(key, 9)[1]}
    res['split_sweep'] = {}
    for lo_t, hi_t in ((0.25, 0.75), (1 / 3, 2 / 3), (0.4, 0.6), (0.5, 0.5)):
        D.SHALLOW, D.DEEP = lo_t, hi_t
        res['split_sweep']['%.2f_%.2f' % (lo_t, hi_t)] = {
            key: D.group_test(cells, dep, key, rng, 1500)['p']
            for key in ('q99_abs_z', 'kurt_z')}
    D.SHALLOW, D.DEEP = 1 / 3, 2 / 3
    # --- the five an independent reviewer found that I did not, all re-derived here
    def grp(lo, hi, key, nperm=4000):
        a = [c for c, d in zip(cells, dep) if lo[0] <= d < lo[1]]
        b = [c for c, d in zip(cells, dep) if hi[0] <= d < hi[1]]
        obs = D.med_desc(b, key) - D.med_desc(a, key)
        lab = [0] * len(a) + [1] * len(b); pool = a + b; null = []
        for _ in range(nperm):
            rng.shuffle(lab)
            A = [c for c, l in zip(pool, lab) if l == 0]
            B = [c for c, l in zip(pool, lab) if l == 1]
            null.append(D.med_desc(B, key) - D.med_desc(A, key))
        return obs, (1 + sum(1 for x in null if abs(x) >= abs(obs))) / (1 + nperm)

    # NON-MONOTONICITY: the round compared two endpoints and DELETED the middle third by design,
    # so it was structurally incapable of finding this.
    res['by_third'] = {}
    res['shallow_vs_middle'] = {}
    for key in K:
        res['by_third'][key] = {
            'shallow': D.med_desc([c for c, d in zip(cells, dep) if d < 1/3], key),
            'middle': D.med_desc([c for c, d in zip(cells, dep) if 1/3 <= d < 2/3], key),
            'deep': D.med_desc([c for c, d in zip(cells, dep) if d >= 2/3], key)}
        o, pv = grp((0, 1/3), (1/3, 2/3), key)
        res['shallow_vs_middle'][key] = {'delta': o, 'p': pv}
    res['by_quarter'] = {key: [D.med_desc([c for c, d in zip(cells, dep)
                                           if q/4 <= d < (q+1)/4 or (q == 3 and d == 1)], key)
                               for q in range(4)] for key in K}

    # REDUNDANCY: four "independent" descriptors, or one statistic counted four times?
    sys.path.insert(0, '/home/ivan/AblationNoise')
    import headline as H
    mx = [max(abs(x) for x in R.standardise(c)) for c in cells]
    res['spearman_vs_max_abs_z'] = {key: H._spearman([R.descriptor(c, key) for c in cells], mx)
                                    for key in K}

    # TOP-OF-STACK: drop the last k layers of every stratum
    res['drop_last_layers'] = {}
    for k in (0, 1, 2, 3, 4):
        keep = []
        for s_, idx in by.items():
            ii = sorted(idx, key=lambda i: meta[i]['layer'])
            keep += ii[:len(ii) - k] if k else ii
        cs = [cells[i] for i in keep]; ds = [dep[i] for i in keep]
        res['drop_last_layers'][k] = {key: D.group_test(cs, ds, key, rng, 1500)['p']
                                      for key in ('q99_abs_z', 'kurt_z', 'sd_over_mad_z',
                                                  'q90_abs_z')}

    # LEAVE ONE MODEL OUT
    res['leave_one_model_out'] = {}
    for m in ('qwen2.5-1.5b', 'qwen2.5-3b'):
        idx = [i for i, c in enumerate(meta) if c['model'] == m]
        cs = [cells[i] for i in idx]; ds = [dep[i] for i in idx]
        res['leave_one_model_out'][m] = {
            key: {'p': (r := D.group_test(cs, ds, key, rng, 1500))['p'], 'm_break': r['m_break']}
            for key in ('q99_abs_z', 'kurt_z', 'sd_over_mad_z', 'q90_abs_z')}

    # THE SCALE ESTIMATOR WAS A CHOICE: redo standardised by sd instead of MAD
    orig = R.standardise

    def sd_std(v):
        m = R.med(v); _, sdv, _, _ = R.moments(v)
        return [(x - m) / (sdv if sdv > 0 else 1.0) for x in v]
    R.standardise = sd_std
    res['standardised_by_sd'] = {key: {**{k2: v2 for k2, v2 in
                                          D.group_test(cells, dep, key, rng, 1500).items()
                                          if k2 in ('shallow', 'deep', 'delta', 'p')}}
                                 for key in ('q90_abs_z', 'q99_abs_z')}
    R.standardise = orig

    op = pathlib.Path(__file__).resolve().parent.parent / 'results' / 'r23_attack.json'
    json.dump(res, open(op, 'w'), indent=1)
    print('  wrote', op)


emit()
