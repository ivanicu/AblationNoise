#!/usr/bin/env python3
"""A18 -- the family of decision rules, split by DIRECTION before it is corrected.

Registered in MULTIPLICITY_PREREGISTRATION.md, committed before this file existed.

A correction lowers alpha. That makes a PRESENCE rule (`fires when p <= alpha`) harder and an
ABSENCE rule (`fires when p >= alpha`) EASIER. This repository's headline verdicts are mostly
absences -- R19's H-position is literally `p_pos >= ALPHA` -- so a blanket Bonferroni would
strengthen its central claims with no new observation. The two halves are therefore never mixed.

The primary statistic is family-size-free, because the family size is bookkeeping:

    m_break = floor(alpha / p)      the largest family in which Bonferroni still rejects
    ceiling = alpha * (N + 1)       what m_break CANNOT exceed for a permutation test over N draws

The inventory is DERIVED by walking `headline.py --json`, not hand-listed. Direction is assigned by
an explicit table below; anything the table does not cover is UNCLASSIFIED and is COUNTED, never
dropped -- the population a check iterates over IS the check.
"""
import json
import math
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
ALPHA = 0.05

# Family definitions evaluated side by side, because m is a CHOICE. 12 = the headline verdicts
# ADVERSARY.md A18 counts; 33 = the registered decision rules after D145 added two to A18's 31.
CANDIDATE_FAMILIES = {'headline_verdicts_12': 12, 'registered_rules_33': 33}

# Direction table. A path is matched by the first prefix that fits. PRESENCE fires on p <= alpha;
# ABSENCE fires on p >= alpha or states "no effect"; CONTROL is an instrument check, not a claim.
DIRECTION = [
    # --- controls: these exist to prove the instrument can fire at all
    ('.set_enrichment.positive_control_p', 'CONTROL', 'matched-layer null positive control'),
    ('.window_arm_control.p', 'CONTROL', 'window/arm control, R13'),
    ('.taxonomy_power.chi_square_p', 'CONTROL', 'defect-ledger taxonomy, about the ledger'),
    # --- resolution: statements about what p an instrument can ATTAIN, not verdicts. Assigned
    # AFTER the first run, which had them as UNCLASSIFIED; recorded as post hoc. It cannot move the
    # verdict, which depends only on the PRESENCE family, and `resolution_limit()` already reports
    # that its 8 uncorrected rows yield ZERO BH discoveries -- they are explicitly not claimed.
    ('.ov_permutation_null.p_floor', 'RESOLUTION', 'the floor of a 2000-draw null'),
    ('.resolution_limit.', 'RESOLUTION', 'per-head attainable p; 0 BH discoveries, not a claim'),
    # --- absence: the verdict is "not enriched" / "no position effect" / "not the published set"
    ('.set_enrichment.arms.I_final.p_distinct_per_layer', 'ABSENCE', 'the eight are not enriched'),
    ('.set_enrichment.arms.I_all.p_distinct_per_layer', 'ABSENCE', 'the eight are not enriched'),
    ('.set_enrichment.arms.I_final.p_hurt', 'ABSENCE', 'signed variant, not enriched'),
    ('.set_enrichment.arms.I_final.p_help', 'ABSENCE', 'signed variant, not enriched'),
    ('.set_enrichment.arms.I_all.p_hurt', 'ABSENCE', 'signed variant, not enriched'),
    ('.set_enrichment.arms.I_all.p_help', 'ABSENCE', 'signed variant, not enriched'),
    ('.set_enrichment.arms.I_final.p', 'ABSENCE', 'the eight are not enriched, pooled null'),
    ('.set_enrichment.arms.I_all.p', 'ABSENCE', 'the eight are not enriched, pooled null'),
    ('.additivity.sign_test_p', 'ABSENCE', 'no consistent super/sub-additivity'),
    ('.r17.p_one_sided', 'ABSENCE', 'no excess over the sham band'),
    ('_position', 'ABSENCE', 'R19 H-position: registered as p >= ALPHA, a PASS on non-rejection'),
    ('_published_final', 'ABSENCE', 'R19 H-published: the eight are not special'),
    ('_published_all', 'ABSENCE', 'R19 H-published: the eight are not special'),
    ('.r19_confirmatory.ov_prediction.p_kl', 'ABSENCE', 'OV forward prediction, not confirmed'),
    ('.r19_confirmatory.ov_prediction.p_margin', 'ABSENCE', 'OV forward prediction, not confirmed'),
    # --- presence: the verdict is "this is real"
    ('.set_enrichment.L17H0_one_head_p', 'PRESENCE', 'L17H0 single-head enrichment'),
    ('.selection_overlap.L22H7_one_head_p', 'PRESENCE', 'L22H7 selection/effect overlap'),
    ('.selection_overlap.aggregations.', 'PRESENCE', 'selection-vs-effect overlap, per aggregation'),
    ('.ov_permutation_null.results.', 'PRESENCE', 'OV copying beats a permuted null'),
    ('.condition_shape_rank.', 'PRESENCE', 'the conditional shape is rank-1-dominated'),
    ('.mechanism.alignment.p', 'PRESENCE', 'readout-reach partial correlation'),
]

# Number of draws behind each null, for the instrument ceiling. Read from the emitter where it is
# published; a rule absent here reports ceiling `None` rather than a guessed one.
N_DRAWS = [
    ('.ov_permutation_null.', '.ov_permutation_null.n_permutations'),
    ('.set_enrichment.', '.set_enrichment.n_replicates'),
    ('.selection_overlap.', '.selection_overlap.n_replicates'),
]


def walk(o, path, out):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, f'{path}.{k}', out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, f'{path}[{i}]', out)
    else:
        out[path] = o


def is_p_key(path):
    leaf = path.split('.')[-1].split('[')[0]
    return leaf == 'p' or leaf.startswith('p_') or leaf.endswith('_p')


def classify(path):
    for pat, d, why in DIRECTION:
        if pat in path:
            return d, why
    return 'UNCLASSIFIED', ''


def m_break(p):
    """The largest family in which Bonferroni at ALPHA still rejects. 0 means it never does."""
    return int(math.floor(ALPHA / p)) if p > 0 else None


def selftest():
    """Registered positive controls 1 and 3. An instrument that has never been shown to fire is
    silence, not evidence -- and one that cannot return 0 has no failing branch at all."""
    assert m_break(1e-9) == 50000000, m_break(1e-9)
    assert m_break(0.049) == 1, m_break(0.049)
    assert m_break(0.06) == 0, m_break(0.06)
    assert m_break(0.0) is None
    return True


def main():
    selftest()
    js = subprocess.check_output([sys.executable, str(REPO / 'headline.py'), '--json'],
                                 cwd=REPO, text=True)
    flat = {}
    walk(json.loads(js), '', flat)

    # registered positive control 2: the walk must find the p this repository already knows fails
    # Bonferroni at three tests. If it does not, the walk is not finding rules.
    ANCHOR = '.mechanism.alignment.p'
    if ANCHOR not in flat:
        print(f'REFUSED_WALK_MISSED_ANCHOR: {ANCHOR} not found -- the walk is not finding rules')
        return 3

    rows = []
    for path, v in sorted(flat.items()):
        if not (is_p_key(path) and isinstance(v, float) and 0.0 <= v <= 1.0):
            continue
        # A GENERATOR THAT CONSUMES ITS OWN OUTPUT IS NOT A MEASUREMENT. headline.multiplicity()
        # republishes this file's summary, so without this guard the walk finds its own previous
        # answer and the inventory grows by one row per run -- observed live: 48 p-values and 0
        # unclassified became 49 and 1 the moment the emitter was wired in. Renaming the offending
        # key fixed that instance; this line fixes the class.
        if path.startswith('.multiplicity.'):
            continue
        d, why = classify(path)
        ceil_n, n_src = None, None
        for pref, npath in N_DRAWS:
            if path.startswith(pref) and npath in flat:
                ceil_n, n_src = flat[npath], 'emitted'
                break
        if ceil_n is None and v > 0:
            # DERIVED, NOT GUESSED. An empirical p pinned at the first rank of an N-draw null is
            # exactly 1/(N+1) (or 1/N, depending on the +1 convention), so 1/p - 1 lands on an
            # integer. When it does, N is recovered from the number itself rather than from a
            # lookup table I would have had to hand-write -- and a hand-written table is how a
            # check becomes self-report.
            cand = 1.0 / v - 1.0
            if abs(cand - round(cand)) < 1e-6 and round(cand) >= 1:
                ceil_n, n_src = int(round(cand)), 'inferred_from_p_granularity'
        # WITHIN ONE DRAW OF THE FLOOR IS AT THE FLOOR. The repository's nulls disagree by one on
        # the +1 convention -- ov_permutation_null emits p_floor = 1/2001 while its results carry
        # 1/2000 -- so an exact comparison would report the tightest results as NOT at their floor,
        # which is the fail-toward-pass direction for this control.
        rank_implied = v * (ceil_n + 1) if ceil_n else None
        rows.append({
            'path': path, 'p': v, 'direction': d, 'claim': why,
            'm_break': m_break(v),
            'n_draws': ceil_n, 'n_draws_source': n_src,
            'rank_implied': rank_implied,
            'ceiling': (ALPHA * (ceil_n + 1)) if ceil_n else None,
            'at_floor': (rank_implied is not None and rank_implied <= 1.5),
            'fires_uncorrected': (v <= ALPHA) if d == 'PRESENCE' else
                                 (v >= ALPHA) if d == 'ABSENCE' else None})

    pres = [r for r in rows if r['direction'] == 'PRESENCE']
    reso = [r for r in rows if r['direction'] == 'RESOLUTION']
    absn = [r for r in rows if r['direction'] == 'ABSENCE']
    ctrl = [r for r in rows if r['direction'] == 'CONTROL']
    uncl = [r for r in rows if r['direction'] == 'UNCLASSIFIED']
    M_presence = len(pres)

    firing = [r for r in pres if r['fires_uncorrected']]
    dies = [r for r in firing if r['m_break'] < M_presence]
    dies6 = [r for r in firing if r['m_break'] < 6]
    # the finding that would be worse than any of the above
    manufactured = [r for r in absn if not r['fires_uncorrected']]

    verdict = 'MULTIPLICITY-BITES' if dies else 'MULTIPLICITY-IMMATERIAL'

    # THE SURVIVORS SURVIVE ON N, NOT ON EVIDENCE. A p pinned at its null's first rank says only
    # "nothing in N draws beat it"; m_break is then a statement about the number of draws bought,
    # and any two such results are indistinguishable however different their effects.
    surviving = [r for r in firing if r['m_break'] >= M_presence]
    surv_at_floor = [r for r in surviving if r['at_floor']]

    out = {'alpha': ALPHA, 'n_p_values_found': len(rows),
           'n_presence': len(pres), 'n_absence': len(absn), 'n_resolution': len(reso),
           'n_control': len(ctrl), 'n_unclassified': len(uncl),
           'n_surviving_presence': len(surviving),
           'n_surviving_presence_at_instrument_floor': len(surv_at_floor),
           'surviving_presence_at_floor': [r['path'] for r in surv_at_floor],
           'surviving_presence_with_graded_p': [r['path'] for r in surviving
                                                if not r['at_floor']],
           'unclassified_paths': [r['path'] for r in uncl],
           'M_presence': M_presence,
           'presence_firing_uncorrected': len(firing),
           'presence_dying_at_M_presence': [r['path'] for r in dies],
           'presence_dying_below_6': [r['path'] for r in dies6],
           'absence_currently_failing_would_be_manufactured': [r['path'] for r in manufactured],
           'verdict': verdict,
           'candidate_families': {}, 'rows': rows}
    for name, m in CANDIDATE_FAMILIES.items():
        out['candidate_families'][name] = {
            'm': m, 'n_presence_surviving': sum(1 for r in firing if r['m_break'] >= m),
            'n_presence_dying': sum(1 for r in firing if r['m_break'] < m),
            'bonferroni_alpha': ALPHA / m}
    out['candidate_families']['M_presence_derived'] = {
        'm': M_presence, 'n_presence_surviving': len(firing) - len(dies),
        'n_presence_dying': len(dies), 'bonferroni_alpha': ALPHA / M_presence if M_presence else None}

    op = REPO / 'results_multiplicity.json'
    json.dump(out, open(op, 'w'), indent=1)

    print(f'  p-values found by the walk: {len(rows)}   '
          f'PRESENCE {len(pres)}  ABSENCE {len(absn)}  RESOLUTION {len(reso)}  '
          f'CONTROL {len(ctrl)}  UNCLASSIFIED {len(uncl)}')
    if uncl:
        for r in uncl:
            print(f'      UNCLASSIFIED {r["path"]} = {r["p"]:.6g}')
    print()
    print('  PRESENCE family -- correction is CONSERVATIVE here')
    print(f'  {"p":>12} {"m_break":>8} {"ceiling":>8} {"floor?":>7}  path')
    for r in sorted(pres, key=lambda r: r['p']):
        c = f'{r["ceiling"]:.0f}' if r['ceiling'] else '-'
        src = {'emitted': 'N', 'inferred_from_p_granularity': 'n?'}.get(r['n_draws_source'], '')
        print(f'  {r["p"]:12.6g} {r["m_break"]:8d} {c:>8} {src:>3} '
              f'{"AT_FLOOR" if r["at_floor"] else "":>8}  {r["path"]}')
    print()
    print('  ABSENCE family -- correction is ANTI-CONSERVATIVE here: lowering alpha makes these EASIER')
    print(f'  {"p":>12} {"passes p>=a":>12}  path')
    for r in sorted(absn, key=lambda r: -r['p']):
        print(f'  {r["p"]:12.6g} {str(r["fires_uncorrected"]):>12}  {r["path"]}')
    print()
    for name, c in out['candidate_families'].items():
        print(f'  family {name:<24} m={c["m"]:>3}  alpha\'={c["bonferroni_alpha"]:.6f}  '
              f'presence surviving {c["n_presence_surviving"]}/{len(firing)}')
    print()
    print(f'  presence verdicts dying below a family of 6: {len(dies6)}')
    print(f'  presence verdicts SURVIVING at M_presence: {len(surviving)}   '
          f'of which pinned at their own null\'s floor: {len(surv_at_floor)}   '
          f'with a graded p: {len(surviving) - len(surv_at_floor)}')
    print(f'  absence verdicts that a correction would MANUFACTURE: {len(manufactured)}')
    print(f'  VERDICT: {verdict}')
    print(f'  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
