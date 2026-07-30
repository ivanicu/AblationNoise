#!/usr/bin/env python3
"""Lambda is an algebraic identity on SNR, and the null that carries no head information reads W1.

Found by an independent code reviewer. Every number below is reproduced here rather than quoted.

    rms^2 = mean^2 + (n-1)/n * sd_i^2      and    snr = |mean| * sqrt(n) / sd_i
    =>  Lambda = log(rms) - log|mean| = 0.5 * log(1 + (n-1)/snr^2)

So Lambda carries EXACTLY the information in |per_head| / per_head_sem and nothing else. Both columns
were already published in R11. The registration called Lambda "a POINTWISE reparameterisation of the
published number", which is true and was not the point: it is a reparameterisation of SNR SPECIFICALLY,
which means it cannot separate a head property from a resolution limit -- and separating those was the
entire question.

FOUR CONSEQUENCES, all measured here:
  1. the identity, to machine precision
  2. Lambda recomputed from R11's two published columns with ZERO forwards, against the 2976-forward scan
  3. W3's threshold was arithmetically unreachable: a MEDIAN cannot exceed the MAX, and the max of
     max|Delta|/rms over every cell is below the 6.5 bar. So W3 was dead on arrival, like W0.
  4. the jackknife SE used as "the instrument's own floor" against a direct replicate precision from the
     two independent item sets -- the registration quotes the replicate figure itself, in its own W0
     refutation, and then gates on the other one

NO NEW VERDICT IS EMITTED. This file retracts one.
"""
import json
import math
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
SEED = 20260729
N_NULL = 200


def main():
    out = {'note': 'retraction; every figure reproduced here, none quoted'}
    f0 = HERE / 'results' / 'r29_scan_qwen2.5-1.5b_I_final_off0.json'
    f4 = HERE / 'results' / 'r29_scan_qwen2.5-1.5b_I_final_off400.json'
    f3 = HERE / 'results' / 'r29_scan_qwen2.5-3b_I_final_off0.json'
    d0 = json.load(open(f0))
    n = d0['n_items']
    per0 = d0['per_cell']

    # ---------- 1. the identity ----------
    dev = [abs(0.5 * math.log(1 + (n - 1) / v['snr'] ** 2) - v['Lambda']) for v in per0.values()]
    out['identity'] = {'formula': 'Lambda == 0.5*log(1 + (n-1)/snr^2)',
                       'max_abs_deviation_nats': max(dev), 'n_cells': len(dev), 'n_items': n}
    print(f'  1. Lambda == 0.5*log(1 + (n-1)/snr^2)   max|dev| {max(dev):.3e} nats over '
          f'{len(dev)} cells')

    # ---------- 1b. G IS AN IDENTITY TOO, and that is the deeper retraction ----------
    #   rms^2 = mean^2 + (n-1)/n * sd_i^2  and  sd_i = sem*sqrt(n)
    #   =>  G = log rms = 0.5*log(mean^2 + (n-1)*sem^2)
    # So (mean, sem) <-> (G, Lambda) is a BIJECTION: the round's entire "split" is a change of
    # coordinates on two columns R11 published. G's celebrated 0.9982 replication across disjoint item
    # sets is a property of those two columns, not of anything the scan measured.
    A0 = json.load(open(REPO / 'R11_instrument_noise' / 'results'
                        / 'r11_itemsA_qwen2.5-1.5b.json'))
    L0 = {int(k): v for k, v in A0['layers'].items()}
    gdev = []
    for lay in sorted(L0):
        ph, ps = L0[lay]['per_head'], L0[lay].get('per_head_sem')
        if not ps:
            continue
        for h in range(len(ph)):
            k = f'L{lay:02d}H{h:02d}'
            if k in per0:
                gdev.append(abs(0.5 * math.log(ph[str(h)] ** 2 + (n - 1) * ps[str(h)] ** 2)
                                - per0[k]['G']))
    out['identity_G'] = {'formula': 'G == 0.5*log(mean^2 + (n-1)*sem^2)',
                         'max_abs_deviation_nats': max(gdev), 'n_cells': len(gdev),
                         'note': 'residual is the float32 precision of the stored columns; the '
                                 'relation is exact in exact arithmetic'}
    print(f'  1b. G == 0.5*log(mean^2 + (n-1)*sem^2)   max|dev| {max(gdev):.3e} nats over '
          f'{len(gdev)} cells')
    print(f'      -> (mean, sem) <-> (G, Lambda) is a BIJECTION. BOTH coordinates are functions of '
          f'two published columns.')

    # ---------- 2. Lambda from two published columns, zero forwards ----------
    A = json.load(open(REPO / 'R11_instrument_noise' / 'results'
                       / 'r11_itemsA_qwen2.5-1.5b.json'))
    L = {int(k): v for k, v in A['layers'].items()}
    a, b = [], []
    for lay in sorted(L):
        ph, ps = L[lay]['per_head'], L[lay].get('per_head_sem')
        if not ps:
            continue
        for h in range(len(ph)):
            k = f'L{lay:02d}H{h:02d}'
            if k not in per0:
                continue
            s = abs(ph[str(h)]) / ps[str(h)]
            a.append(0.5 * math.log(1 + (n - 1) / (s * s)))
            b.append(per0[k]['Lambda'])

    def corr(x, y):
        m1, m2 = sum(x) / len(x), sum(y) / len(y)
        nu = sum((x[i] - m1) * (y[i] - m2) for i in range(len(x)))
        d1 = math.sqrt(sum((v - m1) ** 2 for v in x))
        d2 = math.sqrt(sum((v - m2) ** 2 for v in y))
        return nu / (d1 * d2) if d1 > 0 and d2 > 0 else float('nan')
    out['from_published_columns'] = {
        'corr_with_scan': corr(a, b), 'max_abs_diff_nats': max(abs(a[i] - b[i])
                                                               for i in range(len(a))),
        'n_cells': len(a), 'forwards_used': 0,
        'forwards_the_scan_used': 2976}
    print(f'  2. Lambda from R11\'s two published columns, ZERO forwards, vs the 2976-forward scan: '
          f'corr {corr(a, b):.8f}   max|diff| {out["from_published_columns"]["max_abs_diff_nats"]:.3e}'
          f' nats')

    # ---------- 3. W3's threshold was unreachable ----------
    w3 = {}
    for nm, ff in (('qwen2.5-1.5b', f0), ('qwen2.5-3b', f3)):
        if not ff.exists():
            continue
        p = json.load(open(ff))['per_cell']
        mx = max(v['max_over_rms'] for v in p.values())
        w3[nm] = {'max_over_all_cells': mx, 'w3_threshold': 6.5, 'reachable': mx >= 6.5,
                  'n_cells': len(p)}
        print(f'  3. {nm}: max of max|Delta|/rms over ALL {len(p)} cells = {mx:.4f}, '
              f'W3 needed a MEDIAN >= 6.5 -> unreachable: {mx < 6.5}')
    out['w3_unreachable'] = w3

    # ---------- 4. the precision estimator ----------
    if f4.exists():
        p4 = json.load(open(f4))['per_cell']
        ks = [k for k in per0 if k in p4]
        dif = [per0[k]['Lambda'] - p4[k]['Lambda'] for k in ks]
        sdd = math.sqrt(sum(x * x for x in dif) / (len(dif) - 1))
        rep = sdd / math.sqrt(2)
        jk = sorted(v['lambda_jackknife_se_nats'] for v in per0.values()
                    if v['lambda_jackknife_se_nats'] == v['lambda_jackknife_se_nats'])
        jkm = jk[len(jk) // 2]
        out['precision'] = {
            'jackknife_median_nats': jkm,
            'replicate_precision_nats': rep,
            'sd_of_difference_nats': sdd,
            'optimism_factor': rep / jkm,
            'gate_was': 0.15,
            'jackknife_passes_gate': jkm <= 0.15,
            'replicate_passes_gate': rep <= 0.15,
            'median_lambda_nats': sorted(v['Lambda'] for v in per0.values())[len(per0) // 2],
            'n_cells': len(ks)}
        pr = out['precision']
        print(f'  4. Lambda precision: jackknife median {jkm:.4f} nats   '
              f'DIRECT replicate (off0 vs off400) {rep:.4f} nats   '
              f'optimism {pr["optimism_factor"]:.2f}x')
        print(f'     the 0.15 gate: jackknife passes {pr["jackknife_passes_gate"]}, '
              f'replicate passes {pr["replicate_passes_gate"]}')
        print(f'     median Lambda {pr["median_lambda_nats"]:.4f} nats against a per-cell precision '
              f'of {rep:.4f} -> per-cell SNR about '
              f'{pr["median_lambda_nats"] / rep:.2f}')

    # ---------- 5. an SNR-preserving null, and what it reads ----------
    rng = random.Random(SEED)
    print(f'\n  5. SNR-PRESERVING NULL, {N_NULL} draws: each cell\'s items drawn iid Gaussian from '
          f'ITS OWN (mean, sd)')
    print('     -- Lambda then carries no head information beyond (mean, sd), which is W2\'s ontology')
    sg, mr = [], []
    for _ in range(N_NULL):
        k = rng.choice(list(per0))
        v = per0[k]
        mu, sd = v['mean'], v['sd_items']
        xs = [rng.gauss(mu, sd) for _ in range(n)]
        mm = sum(xs) / n
        rms = math.sqrt(sum(x * x for x in xs) / n)
        sg.append(sum(1 for x in xs if (x > 0) == (mm > 0)) / n)
        mr.append(max(abs(x) for x in xs) / rms)
    sg.sort(); mr.sort()
    obs_sign = sorted(v['sign_frac'] for v in per0.values())[len(per0) // 2]
    obs_mr = sorted(v['max_over_rms'] for v in per0.values())[len(per0) // 2]
    out['snr_preserving_null'] = {
        'n_draws': N_NULL,
        'sign_frac_null_median': sg[len(sg) // 2], 'sign_frac_observed_median': obs_sign,
        'max_over_rms_null_median': mr[len(mr) // 2], 'max_over_rms_observed_median': obs_mr,
        'w1_sign_threshold': 0.65,
        'w1_sign_threshold_below_null': 0.65 < sg[len(sg) // 2]}
    print(f'     sign frac: null median {sg[len(sg) // 2]:.4f}   observed median {obs_sign:.4f}   '
          f'W1 required >= 0.65')
    print(f'     -> W1\'s sign bar sits BELOW its own null: '
          f'{out["snr_preserving_null"]["w1_sign_threshold_below_null"]}')
    print(f'     max|Delta|/rms: null median {mr[len(mr) // 2]:.4f}   observed {obs_mr:.4f}')

    out['retracted'] = ['G, on the same ground as Lambda -- an identity on (per_head, per_head_sem)',
                        'W1_head_property as read by read_matrix.py',
                        'the claim that W3 was positively excluded -- its threshold was unreachable',
                        'the jackknife SE as the instrument floor for Lambda']
    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r29_retraction.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
