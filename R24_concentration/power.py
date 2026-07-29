#!/usr/bin/env python3
"""At the effect size actually present, can a step be told from a ramp at all?

Registered in R24_concentration/AMENDMENT_2_calibrate_at_the_observed_effect_size.md.

Sharpness separates a plant that jumps concentration 0.15 -> 0.65 from noise by 5.62x. The data's
fitted t is about 2.0. So the giant plant proves the STATISTIC works and says nothing about whether
it works HERE.

UNDERPOWERED is checked first and wins outright. If the two plant distributions overlap, where the
observed value falls is not evidence about anything.
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

SEED = 20260729
NREP = 400
MIN_SIDE = 4
CENTRAL = 0.80
OVERLAP_KILL = 0.50
GIANT = 0.50                        # the original plant's amplitude, for the positive control


def pct(v, p):
    v = sorted(v)
    i = p * (len(v) - 1)
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return v[lo] + (v[hi] - v[lo]) * (i - lo) if hi > lo else v[lo]


def central(v, frac=CENTRAL):
    tail = (1 - frac) / 2
    return pct(v, tail), pct(v, 1 - tail)


def overlap_frac(a, b):
    """Overlap of two intervals as a fraction of the width of their union."""
    lo = max(a[0], b[0])
    hi = min(a[1], b[1])
    inter = max(0.0, hi - lo)
    union = max(a[1], b[1]) - min(a[0], b[0])
    return inter / union if union > 0 else 1.0


def fit(y, min_side=MIN_SIDE):
    """The observed two-block fit: split, jump, residual scatter -- what the plants must match."""
    _, c = C.best_step(y, min_side)
    a, b = y[:c], y[c:]
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    res = [x - ma for x in a] + [x - mb for x in b]
    n = len(y)
    s = math.sqrt(sum(r * r for r in res) / (n - 2))
    return {'split': c, 'jump': mb - ma, 'resid_sd': s, 'n': n,
            't': abs(mb - ma) / s if s > 0 else 0.0}


def plant_step(rng, n, split, jump, s):
    return [(0.0 if i < split else jump) + rng.gauss(0, s) for i in range(n)]


def plant_ramp(rng, n, jump, s):
    """Same start, same end, same n -- only the PATH differs."""
    return [jump * i / (n - 1) + rng.gauss(0, s) for i in range(n)]


def ramp_matched_on_t(rng, n, split, target_t, s, tol=0.02, iters=40):
    """The confound arm: match the ramp on FITTED t rather than on amplitude.

    A ramp and a step with the same endpoints differ in total variance, which moves t through a
    route that has nothing to do with localisation. Bisect the ramp amplitude until its expected
    fitted t matches the step's."""
    lo, hi = 0.0, 20.0 * s
    for _ in range(iters):
        mid = (lo + hi) / 2
        ts = [fit(plant_ramp(rng, n, mid, s))['t'] for _ in range(40)]
        m = sorted(ts)[len(ts) // 2]
        if abs(m - target_t) < tol:
            break
        if m < target_t:
            lo = mid
        else:
            hi = mid
    return mid


def dist(rng, kind, nrep, **kw):
    out = []
    for _ in range(nrep):
        y = plant_step(rng, **kw) if kind == 'step' else plant_ramp(
            rng, kw['n'], kw['jump'], kw['s'])
        out.append(B.sharpness(B.profile(y, MIN_SIDE)))
    return out


def main():
    rng = random.Random(SEED)
    out = {'seed': SEED, 'nrep': NREP, 'central': CENTRAL, 'overlap_kill': OVERLAP_KILL,
           'central_pct': int(CENTRAL * 100), 'overlap_kill_pct': int(OVERLAP_KILL * 100),
           'ramp_pct': 90, 'step_pct': 10}

    data = C.load()
    obs = {}
    for (m, s), prof in sorted(data.items()):
        if m != 'qwen2.5-1.5b':
            continue
        for stat in C.STATS:
            y = [row[stat] for row in prof]
            obs[f'{m}|{s}|{stat}'] = {**fit(y), 'sharpness': B.sharpness(B.profile(y, MIN_SIDE))}
    out['observed'] = obs
    ts = sorted(v['t'] for v in obs.values())
    js = sorted(abs(v['jump']) for v in obs.values())
    ss = sorted(v['sharpness'] for v in obs.values())
    print(f'  OBSERVED, ten qwen2.5-1.5b tests')
    print(f'    fitted t      {ts[0]:.3f} .. {ts[-1]:.3f}   median {ts[len(ts) // 2]:.3f}')
    print(f'    jump          {js[0]:.5f} .. {js[-1]:.5f}   median {js[len(js) // 2]:.5f}')
    print(f'    sharpness     {ss[0]:.3f} .. {ss[-1]:.3f}   median {ss[len(ss) // 2]:.3f}')
    x = ss[len(ss) // 2]
    out['observed_median_sharpness'] = x

    # ---------- POSITIVE CONTROL: at the giant amplitude the worlds MUST separate ----------
    n = 28
    gs = dist(rng, 'step', NREP, n=n, split=21, jump=GIANT, s=GIANT * 0.08)
    gr = dist(rng, 'ramp', NREP, n=n, jump=GIANT, s=GIANT * 0.08)
    cs_, cr_ = central(gs), central(gr)
    ov_giant = overlap_frac(cs_, cr_)
    ctrl_ok = ov_giant <= OVERLAP_KILL
    print(f'\n  POSITIVE CONTROL  amplitude {GIANT}')
    print(f'    step  central80 [{cs_[0]:.3f}, {cs_[1]:.3f}]   ramp  [{cr_[0]:.3f}, {cr_[1]:.3f}]')
    print(f'    overlap {ov_giant:.4f} of the union   -> {"PASS" if ctrl_ok else "FAIL"} '
          f'(must be <= {OVERLAP_KILL})')
    out['positive_control'] = {'amplitude': GIANT, 'step_central80': cs_, 'ramp_central80': cr_,
                               'overlap': ov_giant, 'pass': ctrl_ok}
    if not ctrl_ok:
        out['verdict'] = 'VOID_POSITIVE_CONTROL_FAILED'
        print('\n  -> VOID: the comparison cannot separate the worlds even at the giant amplitude.')
        json.dump(out, open(HERE / 'results' / 'r24_power.json', 'w'), indent=1)
        return 3

    # ---------- at the OBSERVED effect size ----------
    print(f'\n  AT THE OBSERVED EFFECT SIZE, per test')
    print(f'    {"test":<40}{"t":<7}{"step c80":<20}{"ramp c80":<20}{"ovl":<8}{"x":<7}verdict')
    per, kills = {}, 0
    for k, v in obs.items():
        st = dist(rng, 'step', NREP, n=v['n'], split=v['split'], jump=v['jump'], s=v['resid_sd'])
        rp = dist(rng, 'ramp', NREP, n=v['n'], jump=v['jump'], s=v['resid_sd'])
        a, b = central(st), central(rp)
        ov = overlap_frac(a, b)
        xi = v['sharpness']
        if ov > OVERLAP_KILL:
            vd = 'UNDERPOWERED'
            kills += 1
        elif xi > pct(rp, .90) and a[0] <= xi <= a[1]:
            vd = 'STEP-LIKE'
        elif xi < pct(st, .10) and b[0] <= xi <= b[1]:
            vd = 'RAMP-LIKE'
        else:
            vd = 'UNVERIFIED'
        per[k] = {'t': v['t'], 'step_central80': a, 'ramp_central80': b, 'overlap': ov,
                  'observed': xi, 'ramp_p90': pct(rp, .90), 'step_p10': pct(st, .10),
                  'verdict': vd}
        print(f'    {k:<40}{v["t"]:<7.2f}[{a[0]:5.2f},{a[1]:6.2f}]     '
              f'[{b[0]:5.2f},{b[1]:6.2f}]     {ov:<8.3f}{xi:<7.2f}{vd}')
    out['per_test'] = per

    # ---------- the confound arm: match the ramp on FITTED t, not amplitude ----------
    print(f'\n  CONFOUND ARM  ramp matched on fitted t instead of amplitude')
    conf = {}
    for k, v in obs.items():
        amp = ramp_matched_on_t(rng, v['n'], v['split'], v['t'], v['resid_sd'])
        st = dist(rng, 'step', NREP, n=v['n'], split=v['split'], jump=v['jump'], s=v['resid_sd'])
        rp = dist(rng, 'ramp', NREP, n=v['n'], jump=amp, s=v['resid_sd'])
        a, b = central(st), central(rp)
        ov = overlap_frac(a, b)
        conf[k] = {'ramp_amplitude': amp, 'overlap': ov,
                   'underpowered': ov > OVERLAP_KILL}
        print(f'    {k:<40}ramp amp {amp:.5f}  overlap {ov:.3f}  '
              f'{"UNDERPOWERED" if ov > OVERLAP_KILL else "separable"}')
    out['confound_t_matched'] = conf

    agree = all((conf[k]['underpowered']) == (per[k]['verdict'] == 'UNDERPOWERED') for k in obs)
    out['matchings_agree'] = agree
    verdict = ('UNDERPOWERED' if kills >= 6 else
               'UNVERIFIED' if not agree else
               'STEP-LIKE' if sum(1 for v in per.values() if v['verdict'] == 'STEP-LIKE') >= 6 else
               'RAMP-LIKE' if sum(1 for v in per.values() if v['verdict'] == 'RAMP-LIKE') >= 6 else
               'UNVERIFIED')
    if not agree:
        verdict = 'UNVERIFIED'
    out['verdict'] = verdict
    print(f'\n  underpowered in {kills} of {len(obs)} tests   '
          f'amplitude- and t-matched agree: {agree}')
    print(f'  REGISTERED VERDICT: {verdict}')
    (HERE / 'results').mkdir(exist_ok=True)
    op = HERE / 'results' / 'r24_power.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
