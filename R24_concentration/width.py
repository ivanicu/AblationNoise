#!/usr/bin/env python3
"""How many layers wide is the transition? Registered in AMENDMENT_3_width_not_a_verdict.md.

Step and ramp are w=1 and w=n of one family. Everything between them was never drawn, and the world
the previous amendment actually named -- a broad elevation over the last several layers -- lives
there. The deliverable is an INTERVAL ON w, in layers, per model x support x statistic. A verdict
word cannot be compared across cells; a number in layers can.

The confound is written into the design, not appended to it: spreading a fixed jump over more layers
also WEAKENS it, so arm B retunes amplitude per w to hold fitted t at the observed value. If the arms
disagree, sharpness cannot separate width from strength and the answer is UNVERIFIED.
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run as C                                                          # noqa: E402
import boundary as B                                                     # noqa: E402
import power as P                                                        # noqa: E402

SEED = 20260729
NREP = 400
WGRID = (1, 2, 3, 4, 6, 8, 14, 28)
MIN_SIDE = 4
PLANT_W = 3


def plant_width(rng, n, split, jump, s, w):
    """Flat, a linear rise over w layers centred on `split`, flat. w=1 is a step, w=n a ramp."""
    lo = split - w / 2.0
    out = []
    for i in range(n):
        f = (i - lo) / w
        f = 0.0 if f < 0 else (1.0 if f > 1 else f)
        out.append(jump * f + rng.gauss(0, s))
    return out


def sharp_dist(rng, n, split, jump, s, w, nrep=NREP):
    return [B.sharpness(B.profile(plant_width(rng, n, split, jump, s, w), MIN_SIDE))
            for _ in range(nrep)]


def amp_for_t(rng, n, split, s, w, target_t, tol=0.03, iters=36):
    """Arm B: retune amplitude at this w so the median fitted t matches the observed."""
    lo, hi, mid = 0.0, 40.0 * s, 0.0
    for _ in range(iters):
        mid = (lo + hi) / 2
        ts = [P.fit(plant_width(rng, n, split, mid, s, w))['t'] for _ in range(40)]
        m = sorted(ts)[len(ts) // 2]
        if abs(m - target_t) < tol:
            break
        if m < target_t:
            lo = mid
        else:
            hi = mid
    return mid


def admissible(rng, n, split, jump, s, x, t_obs, arm):
    """Every w whose central 80% sharpness interval contains x."""
    keep, iv = [], {}
    for w in WGRID:
        a = jump if arm == 'A' else math.copysign(amp_for_t(rng, n, split, s, w, t_obs), jump)
        d = sharp_dist(rng, n, split, a, s, w)
        c = P.central(d)
        iv[w] = {'lo': c[0], 'hi': c[1], 'amplitude': a}
        if c[0] <= x <= c[1]:
            keep.append(w)
    return keep, iv


def fmt(ws):
    return '{' + ','.join(str(w) for w in ws) + '}' if ws else '{}'


def main():
    rng = random.Random(SEED)
    out = {'seed': SEED, 'nrep': NREP, 'w_grid': list(WGRID), 'plant_w': PLANT_W}

    data = C.load()
    obs = {}
    for (m, s), prof in sorted(data.items()):
        if m != 'qwen2.5-1.5b':
            continue
        for stat in C.STATS:
            y = [row[stat] for row in prof]
            obs[f'{m}|{s}|{stat}'] = {**P.fit(y),
                                      'sharpness': B.sharpness(B.profile(y, MIN_SIDE))}
    out['observed'] = obs

    # ---------- CONTROL 1: recover a PLANTED w ----------
    print(f'  CONTROL 1  plant w={PLANT_W} in each cell, the inversion must admit it')
    c1 = {}
    for k, v in obs.items():
        yp = plant_width(rng, v['n'], v['split'], v['jump'], v['resid_sd'], PLANT_W)
        xp = B.sharpness(B.profile(yp, MIN_SIDE))
        keep, _ = admissible(rng, v['n'], v['split'], v['jump'], v['resid_sd'], xp, v['t'], 'A')
        c1[k] = {'planted_x': xp, 'admissible': keep, 'ok': PLANT_W in keep}
        print(f"    {k:<40} x {xp:5.2f}  admits {fmt(keep):<22} {'PASS' if PLANT_W in keep else 'FAIL'}")
    n1 = sum(1 for v in c1.values() if v['ok'])
    out['control_recovery'] = {'per_cell': c1, 'n_pass': n1, 'pass': n1 >= 8}
    print(f'    -> {n1} of {len(c1)}  (need >= 8)')

    # ---------- CONTROL 2: the endpoints must not admit each other ----------
    print(f'\n  CONTROL 2  w=1 data must not admit w=28, and the reverse')
    c2 = {}
    for k, v in obs.items():
        r = {}
        for w in (1, 28):
            yp = plant_width(rng, v['n'], v['split'], v['jump'], v['resid_sd'], w)
            xp = B.sharpness(B.profile(yp, MIN_SIDE))
            keep, _ = admissible(rng, v['n'], v['split'], v['jump'], v['resid_sd'], xp, v['t'], 'A')
            r[w] = {'x': xp, 'admissible': keep, 'self': w in keep,
                    'other': (28 if w == 1 else 1) in keep}
        ok = r[1]['self'] and r[28]['self'] and not (r[1]['other'] and r[28]['other'])
        c2[k] = {**{str(w): r[w] for w in r}, 'ok': ok}
        print(f"    {k:<40} w1 admits {fmt(r[1]['admissible']):<20} "
              f"w28 admits {fmt(r[28]['admissible']):<20} {'PASS' if ok else 'FAIL'}")
    n2 = sum(1 for v in c2.values() if v['ok'])
    out['control_endpoints'] = {'per_cell': c2, 'n_pass': n2, 'pass': n2 >= 8}
    print(f'    -> {n2} of {len(c2)}  (need >= 8)')

    if not (out['control_recovery']['pass'] and out['control_endpoints']['pass']):
        out['verdict'] = 'UNVERIFIED_CONTROL_FAILED'
        print('\n  -> UNVERIFIED: a control failed. No interval is read. Not an acquittal.')
        json.dump(out, open(HERE / 'results' / 'r24_width.json', 'w'), indent=1)
        return 3

    # ---------- the real data, both arms ----------
    print('\n  ADMISSIBLE w, real data')
    print(f'    {"cell":<40}{"x":<7}{"arm A (amp fixed)":<26}{"arm B (t matched)":<26}agree')
    per, agree_n, span_n, loc_n, broad_n = {}, 0, 0, 0, 0
    for k, v in obs.items():
        x = v['sharpness']
        ka, iva = admissible(rng, v['n'], v['split'], v['jump'], v['resid_sd'], x, v['t'], 'A')
        kb, ivb = admissible(rng, v['n'], v['split'], v['jump'], v['resid_sd'], x, v['t'], 'B')
        ag = (set(ka) == set(kb))
        spans = len(ka) == len(WGRID) or len(kb) == len(WGRID)
        per[k] = {'x': x, 'arm_A': ka, 'arm_B': kb, 'agree': ag, 'spans_grid': spans,
                  'intervals_A': {str(w): iva[w] for w in iva},
                  'intervals_B': {str(w): ivb[w] for w in ivb}}
        agree_n += ag
        span_n += spans
        if ag and ka and not any(w >= 8 for w in ka):
            loc_n += 1
        if ag and ka and not any(w <= 2 for w in ka):
            broad_n += 1
        print(f'    {k:<40}{x:<7.2f}{fmt(ka):<26}{fmt(kb):<26}{ag}')
    out['per_cell'] = per

    verdict = ('UNINFORMATIVE' if span_n >= 5 else
               'UNVERIFIED' if agree_n < len(obs) else
               'LOCALISED' if loc_n >= 8 else
               'BROAD' if broad_n >= 8 else 'UNVERIFIED')
    out.update({'n_agree': agree_n, 'n_spanning_grid': span_n, 'n_localised': loc_n,
                'n_broad': broad_n, 'verdict': verdict})
    uni = sorted(set().union(*[set(v['arm_A']) for v in per.values()])) if per else []
    inter = sorted(set.intersection(*[set(v['arm_A']) for v in per.values()])) if per else []
    out['union_admissible'] = uni
    out['intersection_admissible'] = inter
    print(f'\n  arms agree {agree_n}/{len(obs)}   spanning the grid {span_n}   '
          f'localised {loc_n}   broad {broad_n}')
    print(f'  admissible w across all ten cells: union {fmt(uni)}  intersection {fmt(inter)}')
    print(f'  REGISTERED VERDICT: {verdict}')
    (HERE / 'results').mkdir(exist_ok=True)
    op = HERE / 'results' / 'r24_width.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
