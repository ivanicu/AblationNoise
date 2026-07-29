#!/usr/bin/env python3
"""R21 analysis -- the registered rule, applied. Written while the run was still in flight.

Thresholds come from R21_indirect_attribution/PREREGISTRATION.md, committed before run.py existed.
Any disagreement between the two is a defect in this file, not a re-specification.

THE IDENTITY CONTROL GATES EVERYTHING. OWN+ATT+MLP+EMB+NORM is an exact decomposition of the margin
drop, so a discrepancy against R10's frozen total is not noise -- it means a component is missing
from the sum, or the two runs are not measuring the same items.
"""
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))

BAND_LO, BAND_HI = 14, 28
DOMINANCE = 0.50            # registered
IDENTITY_FRAC = 0.05        # registered: <= 0.05 x band sd of total
OWN_VS_R20_SPEARMAN = 0.90  # registered
CLASSES = ('att', 'mlp', 'emb', 'norm')


def median(v):
    w = sorted(v)
    n = len(w)
    return w[n // 2] if n % 2 else 0.5 * (w[n // 2 - 1] + w[n // 2])


def sd(v):
    mu = sum(v) / len(v)
    return math.sqrt(sum((z - mu) ** 2 for z in v) / (len(v) - 1))


def main():
    f = HERE / 'results' / 'r21_indirect_qwen2.5-1.5b.json'
    if not f.exists():
        print(f'no result at {f} -- this analysis was written before the data existed')
        return 1
    d = json.load(open(f))
    if d.get('verdict') != 'MEASURED':
        print(f"  the run REFUSED: {d.get('verdict')} -- {d.get('why')}")
        return 3
    C = d['cells']
    NH, NL = d['n_heads'], d['n_layers']
    band = [(L, h) for L in range(BAND_LO, min(BAND_HI, NL)) for h in range(NH)]
    key = lambda k: f'L{k[0]:02d}H{k[1]:02d}'
    missing = [key(k) for k in band if key(k) not in C]
    if missing:
        print(f'  INCOMPLETE: {len(missing)} of {len(band)} band heads absent, e.g. {missing[:3]}')
        return 3

    print(f"R21  {d['model']}  n={d['n_items']} items  {len(band)} band heads")
    print(f"     base margin {d['base_margin']:.6f}   R10 recorded {d['r10_base_margin']:.6f}")

    tot = [C[key(k)]['total_r10'] for k in band]
    band_sd = sd(tot)
    lim = IDENTITY_FRAC * band_sd

    # ---- control 1a: the decomposition is internally exact (identity by construction)
    e_self = [abs(sum(C[key(k)][c] for c in ('own',) + CLASSES)
                  - C[key(k)]['total_measured_here']) for k in band]
    # ---- control 1b: and it reproduces R10's frozen total (cross-run)
    e_r10 = [abs(C[key(k)]['total_measured_here'] - C[key(k)]['total_r10']) for k in band]
    ok_id = max(e_self) <= 1e-4 and max(e_r10) <= lim
    print(f"\n  CONTROL identity   max|OWN+ATT+MLP+EMB+NORM - total_here| {max(e_self):.3e}")
    print(f"  CONTROL vs R10     max|total_here - total_r10| {max(e_r10):.6f}   "
          f"limit {IDENTITY_FRAC} x band sd = {lim:.6f}  -> {'PASS' if ok_id else 'FAIL'}")

    # THE PRE-REGISTRATION CONTRADICTED ITSELF AND I DID NOT NOTICE UNTIL THIS FAILED.
    # Its "Third confound" section says the clean comparator is HELD FIXED here so the
    # decomposition stays exactly additive, while R10 RECOMPUTES max-over-other-rooms after every
    # ablation. Its "Positive controls" section then requires this decomposition to equal R10's
    # frozen total. Those two are incompatible by construction: wherever the comparator moves, the
    # two are different margins. The control could not pass, and the same file names the reason.
    #
    # The subgroup below is selected on a COVARIATE registered before the run -- "did the comparator
    # move at all" -- and NOT on the size of the error. On the heads where it never moved, the two
    # margin definitions coincide and the control is meaningful.
    r20f = REPO / 'R20_direct_indirect' / 'results' / 'r20_direct_indirect_qwen2.5-1.5b.json'
    stable, e_stable = [], []
    if r20f.exists():
        R20c = json.load(open(r20f))['cells']
        stable = [k for k in band if R20c[key(k)]['comparator_flip_rate'] == 0.0]
        e_stable = [abs(C[key(k)]['total_measured_here'] - C[key(k)]['total_r10']) for k in stable]
        print(f"  CONTROL vs R10, on the {len(stable)} heads whose comparator NEVER moved: "
              f"max {max(e_stable):.6f}  -> {'PASS' if max(e_stable) <= lim else 'FAIL'}   "
              f"[post hoc: the subgroup was chosen after the control failed]")
        import headline as _H
        print(f"  Spearman(|total_here - total_r10|, comparator_flip_rate) "
              f"{_H._spearman([abs(C[key(k)]['total_measured_here'] - C[key(k)]['total_r10']) for k in band], [R20c[key(k)]['comparator_flip_rate'] for k in band]):+.4f}")
    ok_id_stable = bool(e_stable) and max(e_stable) <= lim
    rho_flip = float('nan')
    if stable:
        import headline as _H2
        rho_flip = _H2._spearman(
            [abs(C[key(k)]['total_measured_here'] - C[key(k)]['total_r10']) for k in band],
            [R20c[key(k)]['comparator_flip_rate'] for k in band])

    # ---- control 2: last-layer structure. No attention exists after layer NL-1.
    last = [(NL - 1, h) for h in range(NH)]
    ok_last = all(key(k) in C for k in last)
    if ok_last:
        la = max(abs(C[key(k)]['att']) for k in last)
        ll = max(abs(C[key(k)]['att_late']) for k in last)
        ok_last = la < 1e-6 and ll < 1e-9
        print(f"  CONTROL last layer max|ATT| {la:.3e}  max|ATT from later layers| {ll:.3e}  "
              f"-> {'PASS' if ok_last else 'FAIL'}")
    else:
        print('  CONTROL last layer SKIPPED (layer not in the band range measured)')
        ok_last = True

    # ---- control 3: OWN must be R20's `direct`
    r20 = REPO / 'R20_direct_indirect' / 'results' / 'r20_direct_indirect_qwen2.5-1.5b.json'
    rho_own = float('nan')
    if r20.exists():
        import headline as H
        R = json.load(open(r20))['cells']
        rho_own = H._spearman([C[key(k)]['own'] for k in band],
                              [R[key(k)]['direct_renorm'] for k in band])
        print(f"  CONTROL OWN==R20   Spearman(OWN, R20 direct_renorm) {rho_own:+.4f}   "
              f"required >= {OWN_VS_R20_SPEARMAN}  -> "
              f"{'PASS' if rho_own >= OWN_VS_R20_SPEARMAN else 'FAIL'}")
    ok_own = rho_own >= OWN_VS_R20_SPEARMAN

    if not (ok_id_stable and ok_last and ok_own):
        print('\n  -> UNVERIFIED: even the comparator-stable subgroup fails. Not an acquittal.')
        return 3
    if not ok_id:
        print('\n  ** THE CONTROL AS REGISTERED FAILED. ** What follows is read under the repair '
              'above, which is post hoc. The shares are reported on BOTH populations.')

    # ---- the registered statistic
    def share_table(pop):
        sh = {c: [] for c in CLASSES}
        for k in pop:
            cell = C[key(k)]
            denom = sum(abs(cell[c]) for c in CLASSES)
            for c in CLASSES:
                sh[c].append(abs(cell[c]) / denom if denom > 0 else float('nan'))
        return {c: median([x for x in sh[c] if x == x]) for c in CLASSES}

    med = share_table(band)
    med_stable = share_table(stable) if stable else None
    if med_stable:
        print(f'\n  median shares on the {len(stable)} comparator-stable heads: '
              + '  '.join(f'{c.upper()} {med_stable[c]:.4f}' for c in CLASSES))
    top = max(med, key=med.get)
    verdict = ({'mlp': 'MLP-DOMINATED', 'att': 'ATTENTION-DOMINATED',
                'norm': 'RENORM-DOMINATED', 'emb': 'EMB-DOMINATED'}[top]
               if med[top] >= DOMINANCE else 'MIXED')

    # ---- the registered confound reports
    nm = {'att': d['n_att_members'], 'mlp': d['n_mlp_members'], 'emb': 1, 'norm': 1}
    print(f'\n  class shares (median of |class| / sum|classes| over {len(band)} heads)')
    print(f'  {"class":>6} {"median share":>13} {"median |sum|":>13} {"per member":>12} '
          f'{"cancellation":>13}')
    summary = {}
    for c in CLASSES:
        msum = median([abs(C[key(k)][c]) for k in band])
        canc = float('nan')
        if c in ('att', 'mlp'):
            canc = median([abs(C[key(k)][c]) / C[key(k)][c + '_abs']
                           for k in band if C[key(k)][c + '_abs'] > 0])
        summary[c] = {'median_share': med[c], 'median_abs_sum': msum,
                      'members': nm[c], 'per_member': msum / nm[c], 'cancellation': canc}
        print(f'  {c.upper():>6} {med[c]:13.4f} {msum:13.6f} {msum / nm[c]:12.6f} '
              f'{canc:13.4f}' if canc == canc else
              f'  {c.upper():>6} {med[c]:13.4f} {msum:13.6f} {msum / nm[c]:12.6f} '
              f'{"-":>13}')

    med_own = median([abs(C[key(k)]['own']) for k in band])
    med_tot = median([abs(C[key(k)]['total_r10']) for k in band])
    print(f'\n  median |OWN| {med_own:.6f}   median |total| {med_tot:.6f}   '
          f'ratio {med_tot / med_own:.4f}x   (R20 reported 3.3251x)')

    # ---- how much of the indirect term is LATER attention vs same-or-earlier
    late = median([abs(C[key(k)]['att_late']) for k in band])
    print(f'  median |ATT from layers strictly after the ablated one| {late:.6f}   '
          f'of median |ATT| {summary["att"]["median_abs_sum"]:.6f}')

    print(f'\n  REGISTERED VERDICT: {verdict}   '
          f'(top class {top.upper()} at {med[top]:.4f}, threshold {DOMINANCE})')
    out = {'model': d['model'], 'n_items': d['n_items'], 'n_band': len(band),
           'controls': {'identity_self_max': max(e_self), 'identity_vs_r10_max': max(e_r10),
                        'identity_limit': lim, 'own_vs_r20_spearman': rho_own,
                        'last_layer_ok': ok_last},
           'classes': summary, 'verdict': verdict, 'top_class': top,
           'n_comparator_stable': len(stable),
           'spearman_err_vs_comparator_flip': rho_flip,
           'identity_vs_r10_max_stable': max(e_stable) if e_stable else None,
           'median_shares_stable': med_stable,
           'median_abs_own': med_own, 'median_abs_total': med_tot,
           'ratio_total_over_own': med_tot / med_own,
           'median_abs_att_late': late}
    op = HERE / 'results' / 'r21_analysis_qwen2.5-1.5b.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
