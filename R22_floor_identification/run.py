#!/usr/bin/env python3
"""R22 -- is `7 of 8 inside the floor` identified, or one cell of a surface nobody computed?

Registered in R22_floor_identification/PREREGISTRATION.md, committed before this file existed.

No GPU. Everything here is arithmetic on frozen artifacts.

TWO THINGS THE REGISTRATION DID NOT KNOW AND THIS FILE FOUND BY OPENING THE ARTIFACT:

1. THE 30 REFERENCE DRAWS ARE NOT CHECKED IN. `r1v1_atlas_qwen2.5-1.5b.json` stores only
   `n_draws / mean / sd / min / max` for `band_k1`. So MAD, IQR, a trimmed sd and the empirical
   percentiles -- four of the registered grid's rows -- CANNOT be computed at the registered
   reference. They are reported UNCOMPUTABLE, not skipped: a harness that cannot tell `unmeasured`
   from `unfindable` is on this repository's own overshoot list.

2. THE HEAD THAT DECIDES THE COUNT IS INSIDE ITS OWN REFERENCE DISTRIBUTION. The stored `min` of the
   30 draws is `-0.4668109973271688`; `L16H3`'s published drop is `-0.4668108383814494`. They agree
   to `1.6e-07` -- the same head, measured in two runs. So the floor `L16H3` is judged against was
   computed partly FROM `L16H3`. `resolution_limit()` already states the rule -- *"leave-one-out so
   no head is judged against a null containing itself"* -- and it was never applied to the central
   floor. The leave-one-out floor is computable exactly from the stored aggregates.
"""
import collections
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))
import headline as H                                                     # noqa: E402

PUBLISHED_FLOOR = 0.4417733517951077
PUBLISHED_N_INSIDE = 7


def sd(v, ddof=1):
    mu = sum(v) / len(v)
    return math.sqrt(sum((x - mu) ** 2 for x in v) / (len(v) - ddof))


def mad(v):
    m = sorted(v)[len(v) // 2]
    d = sorted(abs(x - m) for x in v)
    return 1.4826 * d[len(d) // 2]


def iqr_scale(v):
    w = sorted(v)
    q1, q3 = w[len(w) // 4], w[3 * len(w) // 4]
    return (q3 - q1) / 1.349


def trimmed_sd(v, frac=0.10):
    w = sorted(v)
    k = int(frac * len(w))
    return sd(w[k:len(w) - k]) if len(w) - 2 * k > 1 else float('nan')


def pct(v, p):
    w = sorted(abs(x) for x in v)
    i = min(len(w) - 1, int(p * (len(w) - 1)))
    return w[i]


def main():
    eff = H.r1_prior_effects()
    E = {k: v['drop'] for k, v in eff['effects'].items()}
    a1 = json.load(open(REPO / 'R1_noise_floor' / 'results' / 'original_vocabulary'
                        / 'r1v1_atlas_qwen2.5-1.5b.json'))
    c = a1['cells']['band_k1']
    n30, mu30, sd30, min30 = c['n_draws'], c['mean'], c['sd'], c['min']

    r10 = json.load(open(REPO / 'R10_exhaustive' / 'results'
                         / 'r10_exhaustive_qwen2.5-1.5b.json'))
    lay = {int(k): v for k, v in r10['layers'].items()}
    NH = len(lay[14]['per_head'])
    band168 = [lay[L]['per_head'][str(h)] for L in range(14, 28) for h in range(NH)]
    sham = [lay[L]['per_head'][str(h)] for L in range(0, 8) for h in range(NH)]

    out = {'published_floor': PUBLISHED_FLOOR, 'published_n_inside': PUBLISHED_N_INSIDE}

    # ---- POSITIVE CONTROL: land on the published cell exactly, or nothing else is readable
    f0 = 2 * sd30
    n0 = sum(1 for x in E.values() if abs(x) <= f0)
    ok = abs(f0 - PUBLISHED_FLOOR) < 1e-12 and n0 == PUBLISHED_N_INSIDE
    out['positive_control'] = {'floor': f0, 'n_inside': n0, 'reproduces_published': ok}
    print(f'  POSITIVE CONTROL  floor {f0!r}  n_inside {n0}  -> {"PASS" if ok else "FAIL"}')
    if not ok:
        print('  -> UNVERIFIED: the grid does not land on the published cell. Nothing below reads.')
        json.dump(out, open(HERE / 'results' / 'r22_floor_identification.json', 'w'), indent=1)
        return 3

    # ---- the leakage the registration did not anticipate
    L16 = E['L16H3']
    s = n30 * mu30
    ss = (n30 - 1) * sd30 ** 2 + n30 * mu30 ** 2
    s2, ss2, n2 = s - min30, ss - min30 ** 2, n30 - 1
    sd_loo = math.sqrt((ss2 - s2 * s2 / n2) / (n2 - 1))
    out['leakage'] = {
        'min_of_reference_draws': min30, 'L16H3_published_drop': L16,
        'abs_difference': abs(min30 - L16),
        'floor_with_tested_head_included': 2 * sd30,
        'floor_leave_one_out': 2 * sd_loo,
        'floor_shrinks_pct': 100 * (1 - sd_loo / sd30),
        'n_inside_leave_one_out': sum(1 for x in E.values() if abs(x) <= 2 * sd_loo),
        'L16H3_clears_published_pct': 100 * (abs(L16) / (2 * sd30) - 1),
        'L16H3_clears_leave_one_out_pct': 100 * (abs(L16) / (2 * sd_loo) - 1)}
    print(f'  LEAKAGE  the min of the 30 reference draws is L16H3 itself '
          f'(differ by {abs(min30 - L16):.3e})')
    print(f'           floor {2 * sd30:.6f} -> leave-one-out {2 * sd_loo:.6f}  '
          f'({out["leakage"]["floor_shrinks_pct"]:.4f}% smaller)   '
          f'L16H3 clears +{out["leakage"]["L16H3_clears_published_pct"]:.4f}% -> '
          f'+{out["leakage"]["L16H3_clears_leave_one_out_pct"]:.4f}%')

    # ---- bootstrap SE of the floor. The raw draws are absent, so this is the ANALYTIC SE of an sd
    # at n = 30 under normality -- stated as such, because a bootstrap needs the sample and there is
    # no sample checked in.
    se_frac = 1.0 / math.sqrt(2 * (n30 - 1))
    out['floor_se'] = {'method': 'analytic sd/sqrt(2(n-1)); the 30 draws are NOT checked in so a '
                                 'bootstrap is impossible',
                       'relative_se': se_frac, 'absolute_se': se_frac * 2 * sd30,
                       'margin_deciding_the_count_pct':
                           out['leakage']['L16H3_clears_published_pct'],
                       'se_over_margin': (100 * se_frac)
                                         / out['leakage']['L16H3_clears_published_pct']}
    print(f'  FLOOR SE  {100 * se_frac:.4f}% of the floor against a '
          f'{out["leakage"]["L16H3_clears_published_pct"]:.4f}% deciding margin  '
          f'-> {out["floor_se"]["se_over_margin"]:.4f}x')

    # ---- the grid
    refs = {'draws30_original_vocab': None,          # aggregates only -- most estimators impossible
            'exhaustive168_band': band168,
            'exhaustive_sham_L0_7': sham}
    ests = {'sd_ddof1': lambda v: sd(v, 1), 'sd_ddof0': lambda v: sd(v, 0),
            'mad_1.4826': mad, 'iqr_1.349': iqr_scale, 'trimmed_sd_10pct': trimmed_sd}
    mults = {'x2': 2.0, 'x1.96': 1.96}
    cells, uncomputable = [], []
    for rname, v in refs.items():
        for ename, f in ests.items():
            for mname, m in mults.items():
                for cname in ('raw', 'centred'):
                    tag = f'{rname}|{ename}|{mname}|{cname}'
                    if v is None:
                        if ename != 'sd_ddof1':
                            uncomputable.append(tag)
                            continue
                        scale, mu = sd30, mu30
                    else:
                        w = v if cname == 'raw' else [x - sum(v) / len(v) for x in v]
                        scale, mu = f(w), (0.0 if cname == 'raw' else sum(v) / len(v))
                    fl = m * scale
                    ni = sum(1 for x in E.values()
                             if abs(x - (mu if cname == 'centred' else 0.0)) <= fl)
                    cells.append({'cell': tag, 'floor': fl, 'n_inside': ni})
        # empirical percentiles need the sample
        if v is None:
            uncomputable += [f'{rname}|empirical_p95', f'{rname}|empirical_p97.5']
        else:
            for pn, pv in (('empirical_p95', 0.95), ('empirical_p97.5', 0.975)):
                fl = pct(v, pv)
                cells.append({'cell': f'{rname}|{pn}', 'floor': fl,
                              'n_inside': sum(1 for x in E.values() if abs(x) <= fl)})

    vals = [c['n_inside'] for c in cells]
    distinct = sorted(set(vals))
    modal = max(distinct, key=vals.count)
    modal_frac = vals.count(modal) / len(vals)
    verdict = ('IDENTIFIED' if len(distinct) == 1 else
               'NOT-IDENTIFIED' if (len(distinct) >= 3 or modal_frac < 0.50) else 'MIXED')
    # the CORE grid: only the three choices this repository has already flagged as contested
    core = [c for c in cells if ('mad' in c['cell'] or 'iqr' in c['cell']
                                 or 'empirical' in c['cell'] or 'x1.96' in c['cell']
                                 or 'sham' in c['cell'])]
    cvals = [c['n_inside'] for c in core]
    def sub(sel):
        v = [c['n_inside'] for c in sel]
        cc = collections.Counter(v)
        m = max(cc, key=lambda k: cc[k])
        return {'n_cells': len(sel), 'distinct': sorted(set(v)), 'modal': m,
                'modal_fraction': cc[m] / len(v),
                'floor_min': min(c['floor'] for c in sel),
                'floor_max': max(c['floor'] for c in sel),
                'floor_span': max(c['floor'] for c in sel) / min(c['floor'] for c in sel)}

    # THE SHAM REFERENCE IS A BUNDLE CHANGE AND THE REGISTRATION SAID SO BEFORE THE RUN. Judging
    # band heads against a sham-band scale changes the population being described, not just the
    # estimator, so it is reported as its own row rather than pooled into the headline spread.
    out['subgrids'] = {'band_references_only': sub([c for c in cells if 'sham' not in c['cell']]),
                       'exhaustive168_only': sub([c for c in cells
                                                  if c['cell'].startswith('exhaustive168')]),
                       'sham_only_bundle': sub([c for c in cells if 'sham' in c['cell']])}
    out.update({'n_cells': len(cells), 'n_uncomputable': len(uncomputable),
                'uncomputable_cells': uncomputable,
                'n_inside_values': vals, 'distinct_values': distinct,
                'modal_value': modal, 'modal_fraction': modal_frac,
                'floor_min': min(c['floor'] for c in cells),
                'floor_max': max(c['floor'] for c in cells),
                'core_n_cells': len(core), 'core_distinct': sorted(set(cvals)),
                'verdict': verdict, 'cells': cells})
    print(f'\n  grid: {len(cells)} computable cells, {len(uncomputable)} UNCOMPUTABLE '
          f'(the 30 draws are not checked in)')
    print(f'  n_inside distinct values {distinct}   modal {modal} at {modal_frac:.4f}')
    print(f'  floor ranges {min(c["floor"] for c in cells):.6f} to '
          f'{max(c["floor"] for c in cells):.6f}')
    print(f'  core grid ({len(core)} cells) distinct values {sorted(set(cvals))}')
    for c in sorted(cells, key=lambda c: c['floor']):
        print(f'    {c["n_inside"]}  {c["floor"]:.6f}   {c["cell"]}')
    print(f'\n  REGISTERED VERDICT: {verdict}')
    op = HERE / 'results' / 'r22_floor_identification.json'
    op.parent.mkdir(exist_ok=True)
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
