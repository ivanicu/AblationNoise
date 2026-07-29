#!/usr/bin/env python3
"""The floor as a CENSUS rather than a 30-draw sample. Registered in CENSUS_PREREGISTRATION.md.

R1 and R10 share N_ITEMS, SEEDS, DRAW_SEED and byte-identical bindings()/prompt(), so R10's
exhaustive 168 is a census of the population R1 sampled 30 times with replacement. The published
floor is a sample estimate of a parameter measured in full next door.

A census removes sampling error over HEADS and nothing else. R11's instrument figure is carried
below rather than dropped, because the estimand's item-level and cross-model variation is untouched.
"""
import json, math, pathlib, random, sys
HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
import headline as H                                                     # noqa: E402

PUBLISHED_FLOOR = 0.4417733517951077
N_BOOT, BOOT_SEED = 20000, 20260729


def sd(v):
    mu = sum(v) / len(v)
    return math.sqrt(sum((x - mu) ** 2 for x in v) / (len(v) - 1))


def main():
    lk = json.load(open(HERE / 'results' / 'r22_leakage.json'))
    r10 = json.load(open(REPO / 'R10_exhaustive' / 'results'
                         / 'r10_exhaustive_qwen2.5-1.5b.json'))
    lay = {int(k): v for k, v in r10['layers'].items()}
    NH = r10['n_heads']
    band = [(L, h) for L in range(14, 28) for h in range(NH)]
    val = {t: lay[t[0]]['per_head'][str(t[1])] for t in band}
    tag = lambda t: 'L%02dH%02d' % t
    eff = H.r1_prior_effects()
    E = {k: v['drop'] for k, v in eff['effects'].items()}
    # MY OWN KEY-FORMAT BUG, CAUGHT BY READING THE PRINTED COUNT. `tag` zero-pads the head
    # (L16H03) while r1_prior_effects keys do not (L16H3), so `tag(t) in E` matched only the one
    # head with h >= 10 and the "leave the eight out" line removed ONE head, not eight -- which the
    # output announced as `167` where `160` was expected. Parse the keys the way leakage.py does.
    eight = [(int(k[1:k.index('H')]), int(k[k.index('H') + 1:])) for k in E]
    assert len(eight) == 8 and all(t in band for t in eight), eight

    # ---- gate: the recovered 30-draw list must reproduce the published floor exactly
    k1 = [tuple(int(x) for x in (s[1:3], s[4:6])) for s in lk['k1_draws']]
    f30 = 2 * sd([val[t] for t in k1])
    ok = abs(f30 - PUBLISHED_FLOOR) < 1e-12
    print(f'  GATE  recovered 30-draw floor {f30!r}  -> {"PASS" if ok else "FAIL"}')
    if not ok:
        print('  -> UNVERIFIED. Not an acquittal.')
        return 3

    census = 2 * sd([val[t] for t in band])
    census_out = 2 * sd([val[t] for t in band if t not in eight])
    n_c = sum(1 for x in E.values() if abs(x) <= census)
    n_co = sum(1 for x in E.values() if abs(x) <= census_out)

    rng = random.Random(BOOT_SEED)
    pop = [val[t] for t in band]
    boot = sorted(2 * sd([rng.choice(pop) for _ in range(30)]) for _ in range(N_BOOT))
    lo, hi = boot[int(0.025 * N_BOOT)], boot[int(0.975 * N_BOOT)]
    pctile = sum(1 for z in boot if z < PUBLISHED_FLOOR) / N_BOOT
    verdict = 'SAMPLE-IS-ORDINARY' if lo <= PUBLISHED_FLOOR <= hi else 'SAMPLE-IS-ATYPICAL'

    r11 = H.r11()
    out = {'published_floor_30draw': PUBLISHED_FLOOR, 'census_floor_168': census,
           'census_floor_leave_the_eight_out_160': census_out,
           'n_band': len(band), 'n_after_leave_out': len(band) - len(eight),
           'n_inside_published': eff['n_inside'], 'n_inside_census': n_c,
           'n_inside_census_leave_out': n_co,
           'census_over_published': census / PUBLISHED_FLOOR,
           'bootstrap_30_from_census': {'n': N_BOOT, 'seed': BOOT_SEED, 'ci95': [lo, hi],
                                        'median': boot[N_BOOT // 2],
                                        'percentile_of_published': pctile},
           'scope': 'between-head variation only; a census over HEADS removes no item-level or '
                    'cross-model component of the estimand',
           'instrument_component_carried_from_R11':
               (r11 or {}).get('instrument_frac_of_floor'),
           'verdict': verdict}
    print(f'  census floor (all {len(band)})            {census!r}')
    print(f'  census, the eight removed ({len(band) - len(eight)})    {census_out!r}')
    print(f'  n_inside   published {eff["n_inside"]}   census {n_c}   census-leave-out {n_co}')
    print(f'  census / published                    {census / PUBLISHED_FLOOR:.6f}x')
    print(f'  30-from-census bootstrap  95% [{lo:.6f}, {hi:.6f}]  median {boot[N_BOOT // 2]:.6f}')
    print(f'  the published floor sits at percentile {pctile:.4f}')
    print(f'\n  REGISTERED VERDICT: {verdict}')
    op = HERE / 'results' / 'r22_census.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
