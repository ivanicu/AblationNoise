#!/usr/bin/env python3
"""THE REDO LIST. Every round scored against the publication-grade standard, from the ARTIFACTS.

Ivan, 2026-07-30, standing law for this project and everything after it:

    every experiment from now on must be publication-grade, full-scale, large-sample, multi-seed,
    seed-robust, multi-run, independently replicated, effect-size-powered, uncertainty-quantified,
    distribution-complete, hierarchically modeled, multiplicity-controlled, preregisterable,
    confirmatory, causally identified, interventionally validated, counterfactually grounded,
    mechanistically diagnostic, necessity-and-sufficiency-tested, dose-response-characterized,
    temporally resolved, control-saturated, sham-controlled, placebo-controlled where applicable,
    nuisance-matched, norm-matched, compute-matched, positive-control-calibrated,
    negative-control-calibrated, random-baseline-calibrated, measurement-calibrated,
    instrument-validated, construct-validated, criterion-validated, measurement-error-aware,
    noise-floor-calibrated, judge-audited, leakage-audited, contamination-audited,
    shortcut-resistant, artifact-resistant, counterbalanced, position-randomized,
    label-randomized, benchmark-degeneracy-audited, specification-robust, implementation-robust,
    estimator-robust, metric-robust, prompt-robust, perturbation-robust, cross-model, cross-scale,
    cross-architecture, cross-dataset, cross-task, cross-domain, out-of-distribution-tested,
    adversarially stress-tested, falsification-oriented, hostile-peer-review-ready.

    过去所有不合格的要重新做.

THIS FILE IS THAT LIST, AND IT IS MEASURED, NOT REMEMBERED. Every score comes from reading the
round's own result JSONs and generators. Nothing is scored from what I recall having done.

═══ THE HONESTY RULE THAT GOVERNS THIS LEDGER ═══
Most of the ~60 axes above are NOT mechanically detectable from a JSON. Scoring them from a
keyword would be exactly the failure this repo has been fighting all day -- a proxy standing in for
a property, read in the unsound direction. So every axis is one of:

    PASS        the artifact carries positive evidence, with the value that proves it
    FAIL        the artifact carries positive evidence that it is ABSENT (e.g. n_models == 1)
    UNMEASURED  this instrument cannot see it. NOT a pass. NOT a fail.

An UNMEASURED axis is a debt, not an acquittal (P6). The redo list is ranked by FAIL count, and the
UNMEASURED count is printed beside it so the ranking is never mistaken for coverage.

MECHANICALLY CHECKABLE AXES (the only ones scored):
  cross_model        distinct model tags appearing in the round's results               >=2
  cross_scale        distinct parameter scales among those tags                         >=2
  cross_arch         distinct model FAMILIES                                            >=2
  multi_seed         distinct seed offsets / seeds                                      >=2
  multi_support      distinct intervention supports                                     >=2
  multi_draw         the largest n_draws/n_perm/n_null/n_splits/n_boot found            >=30
  uncertainty        an sd, sem, CI, bootstrap or quantile accompanies a headline
  null_present       a null, floor, surrogate, permutation or derangement is recorded
  positive_control   a positive control / calibration arm is recorded
  preregistered      a registered_rule / threshold block, or a PREREGISTRATION.md
  data_derived_null  the null permutes/deranges OBSERVED data rather than generating one
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

FAMILY = {'qwen2.5': 'qwen2.5', 'qwen3': 'qwen3', 'phi': 'phi', 'llama': 'llama',
          'gemma': 'gemma', 'mistral': 'mistral'}
SCALE = re.compile(r'(\d+\.?\d*)\s*b\b', re.I)

PAT = {
    'uncertainty': re.compile(r'\b(sd|stdev|std|sem|ci\d*|ci95|boot|bootstrap|percentile|'
                              r'quantile|p95|p99|iqr|band)\b', re.I),
    'null_present': re.compile(r'\b(null|floor|surrogate|perm|permutation|derange|derangement|'
                               r'sham|baseline|chance)\b', re.I),
    'positive_control': re.compile(r'(positive_control|poscontrol|control_pass|gate|'
                                   r'calibrat|c1_|c2_|injected|recover)', re.I),
    'preregistered': re.compile(r'(registered_rule|registered|prereg|threshold|rule)', re.I),
    'data_derived_null': re.compile(r'(derange|permut|within[_-]layer[_-]perm|label[_-]perm|'
                                    r'item[_-]perm|shuffl)', re.I),
    'multi_draw': re.compile(r'"(n_draws|n_perm|n_null|n_splits|n_boot|n_perm_draws|nperm|'
                             r'n_control_draws|n_null_draws|floor_n)"\s*:\s*(\d+)'),
    'seed': re.compile(r'(off|seed[_-]?offset["\s:]*)(\d{1,5})', re.I),
    'support': re.compile(r'I_(final|all)', re.I),
    # ⚠ the first version of this pattern required a FAMILY PREFIX and therefore scored
    # R35_support at 0 models, when R35 measures BOTH 1.5b and 3b -- its JSON keys are the bare
    # scale tags. A blind instrument returning UNMEASURED everywhere produced a false
    # "zero FAIL" list. Bare scale tags are now matched, and POSITIVE_CONTROL below fails the
    # whole run if the instrument is blind again.
    'model_tag': re.compile(r'\b(qwen2\.5-[\d.]+b|qwen3\.?5?-[\d.]+b|phi-[\d.]+[a-z-]*|'
                            r'llama-?[\d.]+b|gemma-?[\d.]+[be]|mistral-?[\d.]+b|'
                            r'(?<![\w.])\d+\.?\d*b)(?![\w])', re.I),
}

# P5★: a measured 0 is inadmissible until the instrument has returned non-zero on a KNOWN case.
# R35_support demonstrably measures two models at two scales; R29_cancellation demonstrably
# carries two supports and two seed offsets. If the instrument cannot see those, every zero it
# prints is silence, not a clean bill.
POSITIVE_CONTROL = {'R35_support': {'n_models_min': 2, 'n_scales_min': 2},
                    'R29_cancellation': {'n_supports_min': 2, 'n_seeds_min': 2}}


# ⚠⚠ CORRECTION 2026-07-30, SECOND DEFECT, FOUND BY THE NAVIGATOR AND WORSE THAN THE FIRST.
# The five axes below were scored by SUBSTRING over the concatenation of every JSON in a round's
# directory. Measured consequences: `uncertainty` PASS fired on the bare word "band" in 12 of its
# 22 PASSes; `positive_control` fired on "gate" in 6; `preregistered` on "rule"/"threshold" in 6.
# A substring anywhere in any file certified a property of a DIFFERENT experiment's headline.
# And because score() emitted only PASS or UNMEASURED for these five, they had NO FAILING WORLD --
# 99 of the 223 PASSes came from checks that could not fail.
# FIX: these five now PASS only on a STRUCTURED KEY in a parsed JSON object, never on prose.
# A NEGATIVE CONTROL is wired in below: a synthetic blob carrying every trigger WORD in its text
# values but no structured key must score UNMEASURED on all five, or the detector is still reading
# prose and the whole ledger self-labels UNVERIFIED.
KEYPAT = {
    'uncertainty': re.compile(r'(^|_)(sd|sem|se|ci|ci95|iqr|boot|bootstrap|p95|p99|p999|'
                              r'quantile|percentile|band|err|error)($|_|\d)', re.I),
    'null_present': re.compile(r'(^|_)(null|floor|surrogate|perm|derange|sham|chance|baseline)', re.I),
    'positive_control': re.compile(r'(^|_)(positive_control|poscontrol|control_pass|gate_pass|'
                                   r'gate_passed|c1|c2|calibrat|injected|control)($|_)', re.I),
    'preregistered': re.compile(r'^(registered_rule|rule|registered|prereg\w*)$', re.I),
    'data_derived_null': re.compile(r'(^|_)(derange\w*|perm\w*|shuffl\w*|label_perm|item_perm)', re.I),
}


def walk_keys(o, acc):
    """Every KEY in the parsed JSON, at any depth. Values are never inspected."""
    if isinstance(o, dict):
        for k, v in o.items():
            acc.add(k)
            walk_keys(v, acc)
    elif isinstance(o, list):
        for v in o[:200]:
            walk_keys(v, acc)
    return acc


def scan_round(d):
    """Read every result JSON and generator in the round. Return raw evidence, not verdicts."""
    txt, files = [], []
    keys = set()
    for p in sorted(d.rglob('*.json')):
        if 'archive' in p.parts:
            continue
        try:
            raw = p.read_text(errors='ignore')
            txt.append(raw)
            files.append(p.name)
            walk_keys(json.loads(raw), keys)
        except (OSError, ValueError):
            pass
    gens = [p for p in sorted(d.rglob('*.py')) if 'archive' not in p.parts]
    src = '\n'.join(p.read_text(errors='ignore') for p in gens) if gens else ''
    blob = '\n'.join(txt)
    tags = {m.group(1).lower() for m in PAT['model_tag'].finditer(blob + ' ' + src)}
    fams = {next((v for k, v in FAMILY.items() if t.startswith(k)), t.split('-')[0]) for t in tags}
    scales = set()
    for t in tags:
        m = SCALE.search(t)
        if m:
            scales.add(float(m.group(1)))
    seeds = {int(m.group(2)) for m in PAT['seed'].finditer(blob)}
    sups = {m.group(1).lower() for m in PAT['support'].finditer(blob + ' ' + src)}
    draws = [int(m.group(2)) for m in PAT['multi_draw'].finditer(blob)]
    prereg_md = any((d / n).exists() for n in
                    ('PREREGISTRATION.md', 'AMENDMENT_1.md')) or \
        any(p.name.startswith(('PREREG', 'AMEND')) for p in d.glob('*.md'))
    return {'n_json': len(files), 'n_gen': len(gens), 'keys': keys, 'tags': sorted(tags),
            'families': sorted(fams), 'scales': sorted(scales), 'seeds': sorted(seeds),
            'supports': sorted(sups), 'max_draws': max(draws) if draws else 0,
            'blob': blob, 'src': src, 'prereg_md': prereg_md}


def score(ev):
    s = {}
    s['cross_model'] = 'PASS' if len(ev['tags']) >= 2 else ('FAIL' if ev['tags'] else 'UNMEASURED')
    s['cross_scale'] = 'PASS' if len(ev['scales']) >= 2 else ('FAIL' if ev['scales'] else 'UNMEASURED')
    s['cross_arch'] = 'PASS' if len(ev['families']) >= 2 else ('FAIL' if ev['families'] else 'UNMEASURED')
    s['multi_seed'] = 'PASS' if len(ev['seeds']) >= 2 else ('FAIL' if ev['seeds'] else 'UNMEASURED')
    s['multi_support'] = 'PASS' if len(ev['supports']) >= 2 else ('FAIL' if ev['supports'] else 'UNMEASURED')
    s['multi_draw'] = ('PASS' if ev['max_draws'] >= 30
                       else ('FAIL' if ev['max_draws'] > 0 else 'UNMEASURED'))
    for k in ('uncertainty', 'null_present', 'positive_control', 'data_derived_null'):
        s[k] = 'PASS' if any(KEYPAT[k].search(x) for x in ev['keys']) else 'UNMEASURED'
    s['preregistered'] = ('PASS' if (ev['prereg_md']
                                     or any(KEYPAT['preregistered'].search(x) for x in ev['keys']))
                          else 'UNMEASURED')
    return s


def main():
    rounds = sorted([p for p in REPO.glob('R*') if p.is_dir() and re.match(r'R\d+', p.name)],
                    key=lambda p: int(re.match(r'R(\d+)', p.name).group(1)))
    axes = ['cross_model', 'cross_scale', 'cross_arch', 'multi_seed', 'multi_support',
            'multi_draw', 'uncertainty', 'null_present', 'positive_control',
            'data_derived_null', 'preregistered']
    out = {'standard': 'Ivan 2026-07-30: publication-grade, full-scale, multi-seed, cross-model, '
                       'control-saturated, hostile-peer-review-ready. 过去所有不合格的要重新做.',
           'honesty_rule': 'PASS / FAIL / UNMEASURED. UNMEASURED is a DEBT, never an acquittal. '
                           'Only mechanically checkable axes are scored; the other ~50 axes of the '
                           'standard are not detectable from an artifact and are NOT claimed.',
           'axes_scored': axes, 'axes_in_standard_not_scored': 49}
    rows = {}
    print(f"  {'round':<26}{'FAIL':<6}{'UNM':<6}{'models':<8}{'seeds':<8}{'sup':<5}"
          f"{'draws':<8}axes failing")
    for d in rounds:
        ev = scan_round(d)
        if ev['n_json'] == 0 and ev['n_gen'] == 0:
            continue
        s = score(ev)
        nf = sum(1 for v in s.values() if v == 'FAIL')
        nu = sum(1 for v in s.values() if v == 'UNMEASURED')
        fails = [k for k, v in s.items() if v == 'FAIL']
        rows[d.name] = {'scores': s, 'n_fail': nf, 'n_unmeasured': nu,
                        'n_models': len(ev['tags']), 'models': ev['tags'],
                        'n_seeds': len(ev['seeds']), 'seeds': ev['seeds'],
                        'n_supports': len(ev['supports']), 'max_draws': ev['max_draws'],
                        'n_result_json': ev['n_json'], 'n_generators': ev['n_gen'],
                        'failing_axes': fails}
        print(f"  {d.name:<26}{nf:<6}{nu:<6}{len(ev['tags']):<8}{len(ev['seeds']):<8}"
              f"{len(ev['supports']):<5}{ev['max_draws']:<8}{','.join(fails)}")
    out['rounds'] = rows

    # ── P5★ POSITIVE CONTROL: the instrument must see what is known to be there ──
    print('\n  POSITIVE CONTROL — the instrument must return non-zero on known cases')
    pc, pc_ok = {}, True
    for rnd, req in POSITIVE_CONTROL.items():
        r = rows.get(rnd)
        if r is None:
            pc[rnd] = 'ROUND MISSING'
            pc_ok = False
            continue
        got = {'n_models_min': r['n_models'], 'n_scales_min': len(set(
            float(m.group(1)) for t in r['models'] for m in [SCALE.search(t)] if m)),
            'n_supports_min': r['n_supports'], 'n_seeds_min': r['n_seeds']}
        ok = all(got.get(k, 0) >= v for k, v in req.items())
        pc[rnd] = {'required': req, 'observed': {k: got.get(k, 0) for k in req}, 'passes': ok}
        pc_ok &= ok
        print(f"    {rnd:<24} required {req}   observed "
              f"{ {k: got.get(k, 0) for k in req} }   -> {ok}")
    out['positive_control'] = pc
    out['positive_control_passed'] = bool(pc_ok)
    print(f"    -> {'INSTRUMENT SEES; the zeros below are measurements' if pc_ok else 'INSTRUMENT BLIND; every zero below is SILENCE, not a clean bill'}")
    if not pc_ok:
        out['ledger_status'] = 'UNVERIFIED_INSTRUMENT_BLIND'

    # ── NEGATIVE CONTROL: every trigger WORD in text, no structured key. Must score UNMEASURED. ──
    fake = {'note': 'this band gate rule threshold null floor permutation derangement surrogate '
                    'positive_control sham chance baseline registered bootstrap sd sem ci95'}
    fk = walk_keys(fake, set())
    neg = {a: ('UNMEASURED' if not any(KEYPAT[a].search(x) for x in fk) else 'PASS')
           for a in ('uncertainty', 'null_present', 'positive_control', 'preregistered',
                     'data_derived_null')}
    neg_ok = all(v == 'UNMEASURED' for v in neg.values())
    out['negative_control'] = {'arm': 'all trigger words in a text VALUE, zero structured keys',
                               'scores': neg, 'passes': bool(neg_ok)}
    print('\n  NEGATIVE CONTROL — trigger words present as prose, no structured key:')
    print(f"    {neg}   -> {'detector reads KEYS, not prose' if neg_ok else 'STILL READING PROSE'}")
    if not neg_ok:
        out['ledger_status'] = 'UNVERIFIED_DETECTOR_READS_PROSE'

    # ── the denominator that stops '223 PASS' being quoted as compliance ──
    n_pass = sum(1 for k in rows for a in axes if rows[k]['scores'][a] == 'PASS')
    falsifiable = ('cross_model', 'cross_scale', 'cross_arch', 'multi_seed', 'multi_support',
                   'multi_draw')
    n_fals_pass = sum(1 for k in rows for a in falsifiable if rows[k]['scores'][a] == 'PASS')
    full = len(rows) * 60
    out['headline'] = {
        'rounds': len(rows), 'axes_scored': len(axes), 'axes_in_full_standard': 60,
        'cells_scored': len(rows) * len(axes), 'cells_in_full_standard': full,
        'demonstrated_PASS': n_pass,
        'pct_of_full_standard_demonstrated': round(100 * n_pass / full, 2),
        'demonstrated_by_a_FALSIFIABLE_check': n_fals_pass,
        'pct_of_full_standard_falsifiably_demonstrated': round(100 * n_fals_pass / full, 2),
        'warning': 'the five non-counting axes have no failing world; only the six counting axes '
                   'can return FAIL. Never quote demonstrated_PASS without this block.'}
    print(f"\n  HEADLINE, WITH THE REAL DENOMINATOR")
    print(f"    {len(rows)} rounds x 60 axes in the standard = {full} cells")
    print(f"    demonstrated PASS {n_pass} = {100 * n_pass / full:.1f}% of the standard")
    print(f"    demonstrated by a check that COULD have failed: {n_fals_pass} = "
          f"{100 * n_fals_pass / full:.1f}%")

    # ── unqualified = FAIL + UNMEASURED; that is the redo key, not n_fail ──
    for k in rows:
        rows[k]['n_unqualified'] = rows[k]['n_fail'] + rows[k]['n_unmeasured']
    redo = sorted(rows, key=lambda k: (-rows[k]['n_unqualified'], -rows[k]['n_fail']))
    out['redo_order'] = redo
    tot_f = sum(rows[k]['n_fail'] for k in rows)
    tot_u = sum(rows[k]['n_unmeasured'] for k in rows)
    print(f"\n  {len(rows)} rounds scored on {len(axes)} mechanically checkable axes")
    print(f"  total FAIL {tot_f}   total UNMEASURED {tot_u}   "
          f"({len(rows) * len(axes)} cells)")
    print(f"  rounds with zero FAIL: "
          f"{sorted(k for k in rows if rows[k]['n_fail'] == 0)}")
    print(f"\n  REDO ORDER (unqualified = FAIL + UNMEASURED, since an axis a round cannot\n"
          f"  demonstrate is not an axis it has met):")
    for k in redo[:12]:
        print(f"    {k:<28} unqualified {rows[k]['n_unqualified']:2d}/11  "
              f"(FAIL {rows[k]['n_fail']}, UNMEASURED {rows[k]['n_unmeasured']})")
    print(f"\n  ⚠ 49 of the standard's ~60 axes are NOT mechanically checkable and are NOT scored "
          f"here.\n    This ledger is a FLOOR on how much is unqualified, never a ceiling.")

    (HERE / 'results').mkdir(parents=True, exist_ok=True)
    op = HERE / 'results' / 'r36_compliance_ledger.json'
    json.dump(out, open(op, 'w'), indent=1)
    print(f'\n  wrote {op}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
