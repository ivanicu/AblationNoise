#!/usr/bin/env python3
"""The D0 residue of WC: is the shared item field ITEM ORDER? Zero forwards.

wc_field_is_the_instrument.py killed WC in its baseline-margin form (ratio 0.9859 / 1.0101 /
0.8331 against a registered 0.80, positive control 0.0000-0.0082). Its own commit body recorded
what was NOT cleared:

    "item position and answer-token prior are not columns in the npz, so that residue of WC is
     D0 -- unmeasured, not cleared."

Item POSITION is in fact free: it is the column index of the delta matrix, i.e. the order in which
the 120 items sit in the evaluation set. Answer-token prior is not, and stays D0.

This file asks whether the shared item direction v1 is a smooth function of item ORDER -- which it
would be if the eval set is sorted, blocked by category, or drifting in difficulty, any of which
makes "shared field" a fact about the FILE rather than about the network.

THE BASIS IS DELIBERATELY LARGE, 10 dimensions against v1's 1, because a generous basis that still
fails to absorb v1 is the strong version of the negative:
    {1, i, i^2, i^3} polynomial drift
    {sin, cos}(2*pi*k*i/n) for k = 1,2,3   low-frequency blocking
so any monotone trend, any curvature, and any block structure with period >= n/3 is inside it.

═══ REGISTERED BEFORE THE RUN, same rule and same thresholds as the baseline-margin file ═══
    ratio = R2_perp / R2_field, mean over 30 head splits
    ratio <  0.50 in >=2 of 3 cells  ->  POSITION SURVIVES as an explanation of the field
    ratio >= 0.80 in ALL 3 cells     ->  POSITION DEAD
    otherwise                         ->  UNVERIFIED, partial
    POSITIVE CONTROL must return ratio < 0.50 or everything below is UNVERIFIED.

The control here is built to the SAME shape as the hypothesis under test -- delta = outer(u_h, s_i)
where s_i is a smooth function of item index -- rather than the baseline-margin control reused. A
control that does not span the failure mode is not a control.

⚠⚠ ANNOTATED IMMEDIATELY AFTER THE RUN. The navigator overturned the control, and the same
objection applies here that it raised against the baseline-margin file:

    THE POSITIVE CONTROL IS AN IDENTITY, NOT A DETECTION. S = outer(u, s) with s inside Q's span
    forces v1 = s up to sign, and Q contains s by construction, so ratio -> 0 is ALGEBRA. The
    returned 0.0000 / 0.0022 / 0.0085 are round-off, not calibration. The registered thresholds sit
    at 0.50 and 0.80 and THE INSTRUMENT HAS NEVER BEEN RUN NEAR EITHER.

So POSITION_DEAD as printed below is UNVERIFIED AT THE THRESHOLD. What the control establishes is
only that the instrument returns ~0 when the field IS the basis; it does not establish that the
instrument returns 0.9 when 10% of the field is the basis. The calibration required is a mixture
family v = cos(theta)*basis_dir + sin(theta)*mech_dir with the true observable share swept, checking
that the returned ratio tracks 1 - share. That control is built in private_selectivity_replicate.py.

WHAT SURVIVES WITHOUT THE RATIO'S CALIBRATION, because it is a direct comparison and not a ratio:
    R2_obs (10 dims, generous)   0.0774 / 0.0641 / 0.0618
    R2_field (1 dim)             0.5120 / 0.5621 / 0.4782
A ten-dimensional order basis predicts held-out heads 6.6-7.7x worse than one shared direction, and
cos(v1, position span) is 0.2769 / 0.2457 / 0.2325, i.e. 5.4-7.7% of v1's SQUARED length. Those two
lines do not depend on the threshold being calibrated.

NO WORLD IS DECLARED BY THIS FILE.
"""
import json
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260730
RULE = {'survives_if_ratio_below': 0.50, 'dead_if_ratio_atleast': 0.80,
        'cells_required_survive': 2, 'cells_required_dead': 3,
        'control_must_return_ratio_below': 0.50}


def pos_basis(n):
    t = np.linspace(-1, 1, n)
    cols = [np.ones(n), t, t ** 2, t ** 3]
    for k in (1, 2, 3):
        cols += [np.sin(np.pi * k * (t + 1)), np.cos(np.pi * k * (t + 1))]
    Q, _ = np.linalg.qr(np.stack(cols, 1))
    return Q


def run(D, Q, rng):
    n = D.shape[0]
    idx = rng.permutation(n)
    a, b = idx[:n // 2], idx[n // 2:]
    mu = D[a].mean()
    beta = D[a].mean(0) - mu
    A = D[a] - mu - beta[None, :]
    A = A - A.mean(1)[:, None]
    B = D[b] - mu - beta[None, :]
    B = B - B.mean(1)[:, None]
    _, _, Vt = np.linalg.svd(A, full_matrices=False)
    v1 = Vt[0][:, None]
    p = v1 - Q @ (Q.T @ v1)
    nr = np.linalg.norm(p)
    vp = p / nr if nr > 1e-12 else v1 * 0.0

    def sc(V):
        P = B @ V @ V.T
        ss = (B ** 2).sum()
        return float(1 - ((B - P) ** 2).sum() / ss) if ss > 0 else float('nan')

    f, o, pr = sc(v1), sc(Q), sc(vp)
    return {'R2_field': f, 'R2_obs': o, 'R2_perp': pr,
            'ratio': pr / f if f > 0 else float('nan'),
            'cos_v1_pos_span': float(np.linalg.norm(Q.T @ v1))}


def many(D, Q, seed, k=30):
    rg = np.random.default_rng(seed)
    r = [run(D, Q, rg) for _ in range(k)]
    return {'ratio': float(np.mean([x['ratio'] for x in r])),
            'ratio_sd': float(np.std([x['ratio'] for x in r], ddof=1)),
            'ratio_min': float(min(x['ratio'] for x in r)),
            'ratio_max': float(max(x['ratio'] for x in r)),
            'R2_field': float(np.mean([x['R2_field'] for x in r])),
            'R2_obs': float(np.mean([x['R2_obs'] for x in r])),
            'R2_perp': float(np.mean([x['R2_perp'] for x in r])),
            'cos_v1_pos_span': float(np.mean([x['cos_v1_pos_span'] for x in r]))}


def main():
    out = {'seed': SEED, 'registered_rule': RULE,
           'question': "WC residue: is the shared item field a smooth function of ITEM ORDER?"}
    n_items = 120
    Q = pos_basis(n_items)
    print(f'  position basis: {Q.shape[1]} dims (cubic drift + 3 low-frequency Fourier pairs)')

    print('\n  POSITIVE CONTROL  (synthetic: delta = outer(u_h, s_i) + noise, s smooth in ITEM ORDER)')
    rg = np.random.default_rng(SEED)
    t = np.linspace(-1, 1, n_items)
    s = np.sin(np.pi * (t + 1)) + 0.5 * t ** 2
    s = s - s.mean()
    ctrl = {}
    for sn in (0.0, 0.5, 1.0):
        u = rg.standard_normal(336)
        S = np.outer(u, s)
        S = S + sn * S.std() * rg.standard_normal(S.shape)
        r = many(S, Q, SEED, k=10)
        ctrl[f'noise_{sn}'] = r
        print(f"    noise {sn:<4} R2_field {r['R2_field']:+.4f}  R2_obs {r['R2_obs']:+.4f}  "
              f"R2_perp {r['R2_perp']:+.4f}  ratio {r['ratio']:.4f}  cos {r['cos_v1_pos_span']:.4f}")
    out['positive_control'] = ctrl
    cmax = max(v['ratio'] for v in ctrl.values())
    ok = cmax < RULE['control_must_return_ratio_below']
    out['control_passed'] = bool(ok)
    print(f"    control max ratio {cmax:.4f} -> "
          f"{'INSTRUMENT CAN DETECT ORDER' if ok else 'INSTRUMENT BLIND; ALL BELOW UNVERIFIED'}")

    print('\n  OBSERVED')
    res = {}
    for f in sorted((REPO / 'R29_cancellation' / 'results').glob('r29_vectors_*.npz')):
        stem = f.name[len('r29_vectors_'):-4]
        D = np.load(f)['delta'].astype(np.float64)
        r = many(D, Q, SEED)
        res[stem] = r
        print(f"    {stem:<30} ratio {r['ratio']:.4f} +-{r['ratio_sd']:.4f} "
              f"[{r['ratio_min']:.4f},{r['ratio_max']:.4f}]   R2_field {r['R2_field']:+.4f}  "
              f"R2_obs {r['R2_obs']:+.4f}   cos(v1,pos span) {r['cos_v1_pos_span']:.4f}")
    out['cells'] = res

    ratios = [v['ratio'] for v in res.values()]
    ns = sum(1 for x in ratios if x < RULE['survives_if_ratio_below'])
    nd = sum(1 for x in ratios if x >= RULE['dead_if_ratio_atleast'])
    verdict = ('UNVERIFIED_CONTROL_FAILED' if not ok else
               'POSITION_SURVIVES' if ns >= RULE['cells_required_survive'] else
               'POSITION_DEAD' if nd >= RULE['cells_required_dead'] else 'UNVERIFIED_PARTIAL')
    out['verdict'] = verdict
    print(f"\n  registered rule: {ns}/3 below 0.50, {nd}/3 at or above 0.80  ->  {verdict}")
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r30_wc_residue_position.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
