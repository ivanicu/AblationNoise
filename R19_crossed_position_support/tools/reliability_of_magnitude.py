"""EMITTER for results/r19_reliability_of_magnitude.json -- the CORRECTED ceiling (D133).

Checked in because an independent reviewer found that this file and its sibling -- the two
numbers closing R19's headline escape hatch -- were consumed by headline.py and generated
by NOTHING IN THE REPOSITORY. A result whose generator does not exist is indistinguishable
from a result that was never true; that is this repository's opening sentence, and it was
true of its own two most load-bearing files.

    python3 R19_crossed_position_support/tools/reliability_of_magnitude.py
"""
import json, math, os
os.chdir('/home/ivan/AblationNoise')
D = json.load(open('R19_crossed_position_support/results/r19_crossed_qwen2.5-1.5b.json'))
C, NB = D['cells'], D['n_base']
BAND = [(L, h) for L in range(14, D['n_layers']) for h in range(D['n_heads_per_layer'])]
A, B = list(range(0,32)), list(range(32,64))
def rank(v):
    o=sorted(range(len(v)),key=lambda i:v[i]); r=[0.0]*len(v); i=0
    while i<len(o):
        j=i
        while j+1<len(o) and v[o[j+1]]==v[o[i]]: j+=1
        a=(i+j)/2.0+1
        for k in range(i,j+1): r[o[k]]=a
        i=j+1
    return r
def pear(x,y):
    n=len(x); mx,my=sum(x)/n,sum(y)/n
    sx=math.sqrt(sum((a-mx)**2 for a in x)); sy=math.sqrt(sum((b-my)**2 for b in y))
    return sum((x[i]-mx)*(y[i]-my) for i in range(n))/(sx*sy) if sx and sy else 0.0
def spear(x,y): return pear(rank(x),rank(y))
def hm(scope,mi,idx): return [sum(C['L%02dH%02d.%s'%(k[0],k[1],scope)]['base'][i][mi] for i in idx)/len(idx) for k in BAND]
sb = lambda r: 2*r/(1+r)
out={'method':'split-half over bases 0-31 vs 32-63, Spearman-Brown to full length. '
              'ceiling_of_magnitude uses RANK correlations of |x - mean(half)|, matching '
              'analyze.py:187 which correlates |tau - mu|. ceiling_signed_pearson is the '
              'SUPERSEDED quantity: Pearson reliability of the SIGNED effect.',
     'n_band':len(BAND),'n_base':NB,'per_metric':{}}
for mi,name in enumerate(D['metrics']):
    e={}
    for scope in ('final','all'):
        a,b = hm(scope,mi,A), hm(scope,mi,B)
        ma,mb = sum(a)/len(a), sum(b)/len(b)
        e['pearson_signed_'+scope] = sb(pear(a,b))
        e['spearman_magnitude_'+scope] = sb(spear([abs(x-ma) for x in a],[abs(x-mb) for x in b]))
    e['ceiling_of_magnitude'] = math.sqrt(e['spearman_magnitude_final']*e['spearman_magnitude_all'])
    e['ceiling_signed_pearson'] = math.sqrt(e['pearson_signed_final']*e['pearson_signed_all'])
    out['per_metric'][name]=e
json.dump(out, open('R19_crossed_position_support/results/r19_reliability_of_magnitude.json','w'), indent=1)
print('frozen')
for n,e in out['per_metric'].items():
    print('  %-20s right ceiling %.4f   superseded %.4f' % (n, e['ceiling_of_magnitude'], e['ceiling_signed_pearson']))
