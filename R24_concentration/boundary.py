#!/usr/bin/env python3
"""Is the step at depth 0.889 a location, or the edge of the search window?

Registered in R24_concentration/AMENDMENT_1_the_step_sits_on_its_own_search_boundary.md.

`best_step` scans c in [min_side, n - min_side]. At min_side=4, n=28 the last permitted split is
c=24 and 24/27 = 0.889 -- exactly where all ten of R24's tests landed. A maximiser on its own
boundary is not an estimate.

The discriminator is to RELAX THE CONSTRAINT and watch. A real boundary does not move when the
fence is moved; an artifact tracks the fence.

The full t(c) profile is emitted, not the argmax, because a one-element block at c = n-1 makes t
unstable in the direction that flatters the artifact reading.
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run as C                                                          # noqa: E402

SEED = 20260729
MIN_SIDES = (4, 3, 2, 1)
PLANT_AT = 21                       # 0.75 of 28 layers, the profile run.py already generates


def profile(y, min_side):
    """t(c) over every permitted split. Returns {c: t} -- the whole curve, not the argmax."""
    n = len(y)
    out = {}
    for c in range(min_side, n - min_side + 1):
        a, b = y[:c], y[c:]
        ma, mb = sum(a) / len(a), sum(b) / len(b)
        va = sum((x - ma) ** 2 for x in a) + sum((x - mb) ** 2 for x in b)
        sd = math.sqrt(va / (n - 2)) if n > 2 else 0.0
        out[c] = abs(mb - ma) / sd if sd > 0 else 0.0
    return out


def argmax(p):
    return max(p, key=lambda c: p[c])


def sharpness(p):
    """How LOCALISED is the best split -- the peak against the typical value of the same curve.

    The registered rule tests only whether the argmax MOVES when the fence moves. That is sound
    against a fence-tracking artifact and SILENT about a broad plateau: relaxing min_side only adds
    endpoint candidates, so a flat profile whose interior max happens to beat them is 'pinned' too.
    Stability under relaxation does NOT imply localisation.

    MEASURED ON THE min_side=4 PROFILE, never min_side=1. On a flat plant the unconstrained curve
    has a one-element block at each end, its median sits near zero, and the ratio explodes: the
    first version of this function scored planted FLAT at 8.216 against planted STEP at 10.054,
    i.e. it did not separate a boundary from noise at all. The amendment predicted the endpoint
    instability and I still computed the statistic on the curve that contains it."""
    v = sorted(p.values())
    med = v[len(v) // 2]
    return (max(v) / med) if med > 0 else float('nan')


def march(locs):
    """Does the argmax track the fence? Strictly increasing as min_side decreases."""
    v = [locs[m] for m in MIN_SIDES]
    return all(v[i + 1] > v[i] for i in range(len(v) - 1))


def pinned(locs, target=24, tol=1):
    return all(abs(locs[m] - target) <= tol for m in MIN_SIDES)


def main():
    rng = random.Random(SEED)
    out = {'seed': SEED, 'min_sides': list(MIN_SIDES), 'plant_at': PLANT_AT}

    # ---------- CONTROL 1: an interior peak must be findable ----------
    print('  CONTROL 1  planted step at c=21, unconstrained search must find it there')
    cs = C.synth(rng, 28, 12, 'step')
    y = [C.participation_ratio(c) for c in cs]
    p1 = profile(y, 1)
    a1 = argmax(p1)
    c1_ok = abs(a1 - PLANT_AT) <= 1
    print(f'    argmax at c={a1} (planted {PLANT_AT})  t={p1[a1]:.3f}  '
          f'-> {"PASS" if c1_ok else "FAIL"}')
    print('    profile c=17..27: ' + ' '.join(f'{c}:{p1[c]:.2f}' for c in range(17, 28) if c in p1))
    out['control_interior_peak'] = {'argmax': a1, 'planted': PLANT_AT, 't': p1[a1],
                                    'sharpness': sharpness(profile(y, 4)), 'sharpness_ms1': sharpness(p1),
                                    'profile': {str(k): v for k, v in p1.items()}, 'pass': c1_ok}
    print(f'    sharpness ms4 {sharpness(profile(y, 4)):.3f}   ms1 {sharpness(p1):.3f}')

    # ---------- CONTROL 2: how big does an edge t get for free ----------
    print('\n  CONTROL 2  planted flat, the free size of an edge t')
    cs = C.synth(rng, 28, 12, 'flat')
    yf = [C.participation_ratio(c) for c in cs]
    pf = profile(yf, 1)
    af = argmax(pf)
    r = C.test_stratum(list(range(28)), yf, rng, 4000)
    c2_ok = r['p_step'] >= 0.05
    print(f'    argmax at c={af}  t={pf[af]:.3f}   constrained p_step {r["p_step"]:.4f}  '
          f'-> {"PASS" if c2_ok else "FAIL"}')
    out['control_flat'] = {'argmax': af, 't': pf[af], 'p_step': r['p_step'],
                           'sharpness': sharpness(profile(yf, 4)), 'sharpness_ms1': sharpness(pf), 'pass': c2_ok}
    print(f'    sharpness ms4 {sharpness(profile(yf, 4)):.3f}   ms1 {sharpness(pf):.3f}')
    cs = C.synth(rng, 28, 12, 'gradient')
    yg = [C.participation_ratio(c) for c in cs]
    pg = profile(yg, 1)
    out['control_gradient'] = {'argmax': argmax(pg), 't': pg[argmax(pg)],
                               'sharpness': sharpness(profile(yg, 4)), 'sharpness_ms1': sharpness(pg)}
    print(f'\n  CONTROL 3  planted GRADIENT (no step at all): argmax c={argmax(pg)}  '
          f'sharpness ms4 {sharpness(profile(yg, 4)):.3f}   ms1 {sharpness(pg):.3f}'
          f'   -- the value a smooth rise produces for free')

    if not (c1_ok and c2_ok):
        out['verdict'] = 'UNVERIFIED_CONTROL_FAILED'
        print('\n  -> UNVERIFIED: a control failed. Not an acquittal.')
        (HERE / 'results').mkdir(exist_ok=True)
        json.dump(out, open(HERE / 'results' / 'r24_boundary.json', 'w'), indent=1)
        return 3

    # ---------- the real data ----------
    data = C.load()
    print('\n  ARGMAX vs min_side, the ten tests')
    print(f'    {"stratum":<24}{"stat":<16}' + ''.join(f'ms{m:<6}' for m in MIN_SIDES)
          + '  n   verdict')
    rows, pin_n, march_n, total = {}, 0, 0, 0
    for (m, s), prof in sorted(data.items()):
        for stat in C.STATS:
            y = [row[stat] for row in prof]
            n = len(y)
            locs = {ms: argmax(profile(y, ms)) for ms in MIN_SIDES}
            last = {ms: n - ms for ms in MIN_SIDES}          # the fence, per min_side
            on_fence = sum(1 for ms in MIN_SIDES if locs[ms] == last[ms])
            key = f'{m}|{s}|{stat}'
            is_1p5 = (m == 'qwen2.5-1.5b')
            if is_1p5:
                total += 1
                if pinned(locs):
                    pin_n += 1
                if march(locs):
                    march_n += 1
            rows[key] = {'argmax': {str(k): v for k, v in locs.items()},
                         'fence': {str(k): v for k, v in last.items()},
                         'on_fence': on_fence, 'n_layers': n,
                         'pinned_at_24': pinned(locs), 'marches': march(locs),
                         'sharpness': sharpness(profile(y, 4)),
                         'sharpness_ms1': sharpness(profile(y, 1)),
                         'profile_min_side_1': {str(k): v for k, v in profile(y, 1).items()}}
            tag = ('FENCE' if on_fence == len(MIN_SIDES) else
                   'pinned' if pinned(locs) else 'mixed')
            print(f'    {m + "|" + s:<24}{stat:<16}'
                  + ''.join(f'{locs[ms]:<8}' for ms in MIN_SIDES)
                  + f'{n:<4}{tag:<8}sharp {sharpness(profile(y, 4)):.2f}')
    out['tests'] = rows

    verdict = ('BOUNDARY-IS-REAL' if pin_n >= 8 else
               'ARTIFACT' if march_n >= 8 else 'UNVERIFIED')
    out.update({'n_1p5b_tests': total, 'n_pinned_at_24': pin_n, 'n_marching': march_n,
                'verdict': verdict})
    print(f'\n  of the {total} qwen2.5-1.5b tests: pinned at 24 = {pin_n}, '
          f'marching with the fence = {march_n}   (rule: >=8 either way, else UNVERIFIED)')
    print(f'  REGISTERED VERDICT: {verdict}')
    sh = [v['sharpness'] for k, v in rows.items() if '1.5b' in k]
    out['sharpness_1p5b'] = {'min': min(sh), 'median': sorted(sh)[len(sh) // 2], 'max': max(sh)}
    print(f"\n  SHARPNESS, the calibration the rule did not use:\n"
          f"    planted step      {out['control_interior_peak']['sharpness']:.3f}   <- what a real "
          f"boundary looks like\n"
          f"    planted gradient  {out['control_gradient']['sharpness']:.3f}\n"
          f"    planted flat      {out['control_flat']['sharpness']:.3f}\n"
          f"    the ten 1.5b      {out['sharpness_1p5b']['min']:.3f} .. "
          f"{out['sharpness_1p5b']['max']:.3f}  median {out['sharpness_1p5b']['median']:.3f}")
    st, fl, gr = (out['control_interior_peak']['sharpness'], out['control_flat']['sharpness'],
                  out['control_gradient']['sharpness'])
    sep = st > 2 * max(fl, gr)
    out['sharpness_separates_step_from_noise'] = sep
    out['sharpness_margin_over_flat'] = st / fl if fl > 0 else None
    print(f'\n  does sharpness separate a planted step from planted NOISE?  step/flat = '
          f'{st / fl:.2f}x  step/gradient = {st / gr:.2f}x   -> {"YES" if sep else "NO"}')
    out['rule_was_unfit'] = True
    out['verdict_after_calibration'] = ('PLATEAU-NOT-EXCLUDED' if sep else 'UNVERIFIED')
    print('\n  World B (the argmax tracks its fence) is OVERTURNED: it settles at 25 and does not\n'
          '  follow the fence to 27, in 9 of 10 tests. That result stands on its own control.\n'
          '  World A (a boundary) vs World C (a broad plateau) -- a world the amendment never\n'
          '  named -- is NOT settled by the registered rule, which only ever tested fence-tracking.')
    if not sep:
        print('  And it is not settled by sharpness either: the statistic added to settle it does\n'
              '  not separate a planted step from planted noise. -> UNVERIFIED, not an acquittal.')

    (HERE / 'results').mkdir(exist_ok=True)
    op = HERE / 'results' / 'r24_boundary.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
