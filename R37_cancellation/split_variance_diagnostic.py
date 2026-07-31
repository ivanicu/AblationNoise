import json, math, numpy as np, sys
sys.path.insert(0, '/home/ivan/AblationNoise/R37_cancellation')
from g1_injection_fixed import run_pipeline, LMAX
d = json.load(open('/home/ivan/AblationNoise/R19_crossed_position_support/results/r19_crossed_qwen2.5-1.5b.json'))
c = d['cells']; keys = sorted(k for k in c if k.endswith('.final'))
lay_all = np.array([int(k[1:3]) for k in keys]); m = lay_all < LMAX; lay = lay_all[m]
bf = np.stack([np.array(c[k]['base_pos'])[:,:,0] for k in keys])[m]
ba = np.stack([np.array(c[k.replace('.final','.all')]['base_pos'])[:,:,0] for k in keys])[m]
aA0 = ba.mean(1); ch0 = np.abs(aA0.sum(1))/np.maximum(np.abs(aA0).sum(1),1e-300)
zc = np.zeros(len(ch0))
for L in range(LMAX):
    i = np.where(lay==L)[0]; s = ch0[i].std(ddof=1)
    zc[i] = (ch0[i]-ch0[i].mean())/(s if s>0 else 1.0)
print('  DOES THE 4-SPLIT AVERAGING SHRINK THE REPORTED sd? measured, 800 draws each')
print('  %-10s %-12s %-12s %s' % ('n_split','mean X','sd X','sd ratio vs n_split=1'))
base = None
for ns in (1, 2, 4, 8, 16):
    rng = np.random.default_rng(20260730)
    xs = np.array([run_pipeline(bf, ba, lay, 0.0, zc, rng, sham=True, n_split=ns) for _ in range(800)])
    sd = float(np.nanstd(xs, ddof=1))
    if base is None: base = sd
    print('  %-10d %-12.4f %-12.4f %.3f   (1/sqrt(n) would be %.3f)' % (ns, float(np.nanmean(xs)), sd, sd/base, 1/math.sqrt(ns)))
