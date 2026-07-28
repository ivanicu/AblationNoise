#!/usr/bin/env python3
"""R4 — CAN THE FLOOR BE PREDICTED INSTEAD OF MEASURED?

Pre-registration: PREREGISTRATION.md. Amendment: AMENDMENT_1_feature_set_unspecified.md.

ZERO NEW COMPUTE. Every number here is a re-analysis of the R1 result files checked into this
repository, so a reader reproduces R4 in two seconds with no GPU, no model and no network:

    python3 R4_predictability/run.py

THIS SCRIPT EXISTS BECAUSE THE ORIGINAL ANALYSIS DID NOT. R4 was first run inline and its
across-model fold errors were quoted from a commit message. They cannot be regenerated -- see the
amendment. That is precisely the failure this project was built to catch, caught in its own work,
so the fix is not a caveat in prose but a script that recomputes what it prints.

THE TARGET IS THE RAW sd, NOT THE FLOOR. floor = sd / |baseline|, so regressing floor on baseline
would be circular by construction. sd does not contain the baseline, so the baseline is admissible
as a PREDICTOR while the floor is not admissible as a TARGET for it.
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
R1 = HERE.parent / 'R1_noise_floor' / 'results'

# A dtype replicate of a model already in the set is not a fifth model. Including it would count one
# architecture twice in a leave-one-MODEL-out split, which is the leak the split exists to prevent.
EXCLUDE = {'qwen2.5-1.5b-bf16'}

# The licensed predictor family. Every member satisfies the pre-registration's only stated
# constraint -- not a component of sd -- which is exactly the point the amendment makes.
FEATURES = {
    'logk':     lambda k, m: np.log10(k),
    'lognl':    lambda k, m: np.log10(m['n_layers']),
    'lognh':    lambda k, m: np.log10(m['n_heads']),
    'logbase':  lambda k, m: np.log10(m['base']),
    'k':        lambda k, m: float(k),
    'nl':       lambda k, m: float(m['n_layers']),
    'nh':       lambda k, m: float(m['n_heads']),
    'base':     lambda k, m: m['base'],
}


def load():
    models = {}
    for f in sorted(glob.glob(str(R1 / '*.json'))):
        d = json.load(open(f))
        if d['model'] in EXCLUDE:
            continue
        ks = sorted(int(c.split('k')[-1]) for c in d['cells'] if c.startswith('band_k'))
        models[d['model']] = {
            'n_layers': d['n_layers'], 'n_heads': d['n_heads'],
            'base': abs(d['base_margin']),
            'cells': [(k, d['cells'][f'band_k{k}']['sd']) for k in ks],
        }
    if not models:
        raise SystemExit(f"REFUSED: no R1 result files under {R1}")
    return models


def powerlaw(models):
    """Within a model: is sd a power law in set size? Needs >= 3 set sizes to be a fit at all."""
    out = {}
    for name, m in models.items():
        if len(m['cells']) < 3:
            continue
        x = np.log10([k for k, _ in m['cells']])
        y = np.log10([s for _, s in m['cells']])
        a, b = np.polyfit(x, y, 1)
        r2 = 1 - ((y - (a * x + b)) ** 2).sum() / ((y - y.mean()) ** 2).sum()
        out[name] = {'exponent': float(a), 'log10_scale': float(b), 'r2': float(r2),
                     'set_sizes': [k for k, _ in m['cells']],
                     'sd': [float(s) for _, s in m['cells']]}
    return out


def two_point(models, fit_at=(1, 10)):
    """THE DELIVERABLE. Fit the power law on two measured set sizes, predict every other one.

    Needs no feature selection, no other model, and no architecture information -- which is why it
    survives the amendment that took the across-model verdict down.
    """
    errs, per = [], {}
    for name, m in models.items():
        d = dict(m['cells'])
        if not all(k in d for k in fit_at) or len(d) < 3:
            continue
        a, b = np.polyfit(np.log10(fit_at), np.log10([d[k] for k in fit_at]), 1)
        e = []
        for k, sd in m['cells']:
            if k in fit_at:
                continue
            p = 10 ** (a * np.log10(k) + b)
            e.append(float(max(p / sd, sd / p)))
        per[name] = {'exponent': float(a), 'factor_errors': e}
        errs += e
    errs = np.array(errs)
    return {'fit_at': list(fit_at), 'n_heldout': int(errs.size),
            'median_factor_error': float(np.median(errs)),
            'worst_factor_error': float(errs.max()),
            'n_within_2x': int((errs < 2).sum()), 'per_model': per}


def loo(models, names, log_target):
    """Leave-one-MODEL-out. A cell split would leak: cells within a model share architecture."""
    out = {}
    for held in models:
        tr = [(k, m) for nm, m in models.items() if nm != held for k, _ in m['cells']]
        y = np.array([sd for nm, m in models.items() if nm != held for _, sd in m['cells']])
        X = np.array([[FEATURES[f](k, m) for f in names] + [1.0] for k, m in tr])
        w = np.linalg.lstsq(X, np.log10(y) if log_target else y, rcond=None)[0]
        m = models[held]
        Xh = np.array([[FEATURES[f](k, m) for f in names] + [1.0] for k, _ in m['cells']])
        p = Xh @ w
        # A linear-target fit can predict a negative sd; clipping keeps the factor error finite
        # rather than letting an inadmissible prediction score as infinitely bad and dominate.
        pred = np.maximum(10 ** np.clip(p, -30, 30) if log_target else p, 1e-9)
        true = np.array([sd for _, sd in m['cells']])
        out[held] = float(np.median(np.maximum(pred / true, true / pred)))
    return out


def sweep(models, max_features=4):
    """THE AMENDMENT'S MEASUREMENT: how much of the verdict was the unspecified feature set?"""
    rows = []
    for log_target in (True, False):
        for r in range(1, max_features + 1):
            for names in itertools.combinations(FEATURES, r):
                folds = loo(models, names, log_target)
                rows.append({'features': list(names), 'log_target': log_target,
                             'folds': folds,
                             'n_within_2x': int(sum(v < 2 for v in folds.values()))})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(HERE / 'results' / 'r4_predictability.json'))
    ap.add_argument('--check', action='store_true',
                    help='exit non-zero if a README number no longer reproduces')
    args = ap.parse_args()

    models = load()
    n_cells = sum(len(m['cells']) for m in models.values())
    print(f"R4 re-analysis of {len(models)} models / {n_cells} band cells (no new compute)\n")

    pl = powerlaw(models)
    print("WITHIN A MODEL the floor is a power law in set size")
    print(f"  {'model':<16} {'exponent':>9} {'R2':>7}   sd at k = " +
          ' '.join(f'{k}' for k, _ in models['qwen2.5-1.5b']['cells']))
    for name, f in sorted(pl.items(), key=lambda kv: kv[1]['exponent']):
        print(f"  {name:<16} {f['exponent']:9.3f} {f['r2']:7.3f}   " +
              ' '.join(f'{s:.3f}' for s in f['sd']))
    exps = [f['exponent'] for f in pl.values()]
    # The MEASURED sd at k=1, not the fitted intercept. The two differ (8.9x vs 9.5x here) and the
    # measured ratio is the one a reader can check against the R1 files by eye, so it is the one
    # reported. Naming which quantity a spread refers to is not pedantry: the same phrase over two
    # definitions is how a number drifts without anyone editing it.
    k1 = [f['sd'][f['set_sizes'].index(1)] for f in pl.values()]
    k1_span = max(k1) / min(k1)
    print(f"  exponent spans {min(exps):.2f}-{max(exps):.2f}; the measured k=1 sd spans "
          f"{k1_span:.1f}x on an identical task -> the CURVE does not transfer\n")

    tp = two_point(models)
    print(f"TWO-POINT RULE: fit k={tp['fit_at'][0]} and k={tp['fit_at'][1]}, predict the rest")
    print(f"  held-out cells {tp['n_heldout']}   median factor error "
          f"{tp['median_factor_error']:.2f}x   worst {tp['worst_factor_error']:.2f}x   "
          f"within 2x: {tp['n_within_2x']} of {tp['n_heldout']}\n")

    sw = sweep(models)
    met = sum(r['n_within_2x'] >= 3 for r in sw)
    best = max(sw, key=lambda r: r['n_within_2x'])
    print(f"ACROSS MODELS the pre-registered gate depends on a free choice (AMENDMENT 1)")
    print(f"  {len(sw)} admissible feature sets swept; the gate (>=3 of 5 folds within 2x) is "
          f"MET by {met} ({100*met/len(sw):.0f}%)")
    print(f"  best set {best['features']} log_target={best['log_target']} -> "
          f"{best['n_within_2x']} of 5 folds within 2x "
          f"({', '.join(f'{v:.1f}x' for v in best['folds'].values())})")
    print(f"  VERDICT: UNVERIFIED -- one admissible estimator returns each answer, and 5 models "
          f"cannot decide between them")

    res = {'n_models': len(models), 'n_cells': n_cells, 'within_model_powerlaw': pl,
           'k1_sd_span': float(k1_span), 'exponent_range': [float(min(exps)), float(max(exps))],
           'two_point': tp, 'feature_sweep_n': len(sw), 'gate_met_by': met,
           'best_feature_set': best,
           'verdict_across_models': 'UNVERIFIED',
           'verdict_within_model': 'FLOOR-IS-A-POWER-LAW-IN-SET-SIZE',
           'verdict_two_point': 'TWO-MEASURED-POINTS-FIX-THE-CURVE'}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(args.out, 'w'), indent=2, default=float)
    print(f"\n  -> {args.out}")

    if args.check:
        # The README's numbers, asserted against what was just recomputed. A README that drifts
        # from its own data fails the build rather than being discovered by a reader.
        claims = [
            ('two-point median', tp['median_factor_error'], 1.15, 0.01),
            ('two-point worst', tp['worst_factor_error'], 1.68, 0.01),
            ('two-point within 2x', tp['n_within_2x'], 12, 0),
            ('held-out cells', tp['n_heldout'], 12, 0),
            ('min R2', min(f['r2'] for f in pl.values()), 0.935, 0.001),
            ('max R2', max(f['r2'] for f in pl.values()), 0.985, 0.001),
            ('gate met by', met, 60, 0),
            ('k=1 sd span', k1_span, 8.77, 0.02),
            ('min exponent', min(exps), 0.295, 0.001),
            ('max exponent', max(exps), 0.733, 0.001),
        ]
        bad = [(n, g, w) for n, g, w, t in claims if abs(g - w) > t]
        for n, g, w in bad:
            print(f"  STALE: {n} is {g}, README says {w}")
        if bad:
            return 1
        print(f"  README check: {len(claims)} numbers reproduce")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
