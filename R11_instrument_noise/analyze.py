#!/usr/bin/env python3
"""R11 — the three readings of PREREGISTRATION.md, implemented BEFORE the results exist.

Committed while both runs were still queued. That is the whole point: a reading written after
seeing numbers is a narrative, and this repository has already produced three of those (R4's free
estimator, R5's free floor definition, the front page's withdrawn variance decomposition).

    python3 R11_instrument_noise/analyze.py

Stdlib only, like the rest of the gate. It reads the two result files and refuses if either is
missing rather than reporting a partial verdict.

THE DIVISION HAZARD, HANDLED BEFORE IT BITES. `|drop| / (2*SEM)` is undefined for a head that does
nothing: drop == 0 on every item gives SEM == 0. A head with a tiny but non-zero SEM produces an
enormous ratio that means nothing. Both are reported as UNDEFINED rather than as large numbers --
the failure mode this project keeps finding is a formula that returns a plausible value where it
has no denominator.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A_PATH = HERE / 'results' / 'r11_itemsA_qwen2.5-1.5b.json'
B_PATH = HERE / 'results' / 'r11_itemsB_qwen2.5-1.5b.json'
BAND = (14, 27)
SEM_FLOOR = 1e-9          # below this a SEM is not a measurement, it is a zero
KILL_FLOOR_DIVERGENCE = 20.0   # per cent -- PRE-REGISTERED, do not touch


def sd(xs):
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def load(p: Path):
    d = json.load(open(p))
    L = {int(k): v for k, v in d['layers'].items()}
    if not all('per_head_sem' in v for v in L.values()):
        raise SystemExit(f"REFUSED: {p.name} carries no per_head_sem -- it was produced by the "
                         f"runner BEFORE the SEM was stored, so it cannot answer this round.")
    drop = {(k, int(h)): x for k, v in L.items() for h, x in v['per_head'].items()}
    sem = {(k, int(h)): x for k, v in L.items() for h, x in v['per_head_sem'].items()}
    return d, L, drop, sem


def main() -> int:
    if not (A_PATH.exists() and B_PATH.exists()):
        missing = [p.name for p in (A_PATH, B_PATH) if not p.exists()]
        print(f"  UNRUNNABLE: {', '.join(missing)} not present. Both runs are required; a verdict "
              f"from one item set is the thing this round exists to avoid.")
        return 1

    dA, LA, dropA, semA = load(A_PATH)
    dB, LB, dropB, semB = load(B_PATH)
    lo, hi = BAND
    band = [(k, h) for k in range(lo, hi + 1) for h in sorted(LA[k]['per_head'], key=int)
            for h in [int(h)]]
    band = sorted(set(band))

    print(f"  A: {dA['n_items']} items, seeds from {dA.get('draw_seed', 'n/a')}   "
          f"B: {dB['n_items']} items, DISJOINT by construction (seed window shifted by 400)")

    # ---- reading 1 -- measurability of the eight published effects, on the PUBLISHED item set
    pe = json.load(open(ROOT / 'R1_noise_floor' / 'results' / 'prior_effects' /
                        'e132b_eight_single_head_effects.json'))
    import re
    print(f"\n  1 | MEASURABILITY on the published item set: |drop| / (2*SEM), >1 = resolvable at 2s")
    print(f"      {'head':<9}{'drop':>9}{'2*SEM':>10}{'ratio':>9}")
    n_meas = n_def = 0
    for h, e in sorted(pe['effects'].items(), key=lambda kv: -kv[1]['abs']):
        m = re.match(r'L(\d+)H(\d+)', h)
        key = (int(m.group(1)), int(m.group(2)))
        s = semA.get(key)
        if s is None:
            print(f"      {h:<9}{e['drop']:>+9.4f}{'--':>10}{'NOT IN BAND':>9}")
            continue
        if s < SEM_FLOOR:
            print(f"      {h:<9}{e['drop']:>+9.4f}{2*s:>10.2e}{'UNDEFINED':>9}")
            continue
        n_def += 1
        r = e['abs'] / (2 * s)
        n_meas += r > 1
        print(f"      {h:<9}{e['drop']:>+9.4f}{2*s:>10.4f}{r:>9.2f}")
    print(f"      -> {n_meas} of {n_def} defined effects are RESOLVABLE at 2s by this instrument")

    # ---- reading 2 -- does the SEM explain run-to-run disagreement?
    print(f"\n  2 | IS THE SEM THE WHOLE STORY? |dropA - dropB| vs 2*sqrt(semA^2 + semB^2)")
    inside = tot = 0
    worst = None
    for key in band:
        if key not in dropB or key not in semB:
            continue
        d = abs(dropA[key] - dropB[key])
        band_w = 2 * math.sqrt(semA[key] ** 2 + semB[key] ** 2)
        if band_w < SEM_FLOOR:
            continue
        tot += 1
        inside += d <= band_w
        z = d / band_w
        if worst is None or z > worst[0]:
            worst = (z, key, d, band_w)
    pct = 100 * inside / tot if tot else float('nan')
    print(f"      {inside} of {tot} band heads agree within the SEM-predicted band ({pct:.1f}%)")
    if worst:
        z, key, d, w = worst
        print(f"      worst: L{key[0]}H{key[1]}  |dA-dB| {d:.4f} vs predicted {w:.4f}  = {z:.1f}x")
    print(f"      -> expected ~95% if item sampling is the only source of run-to-run variation.")
    print(f"         Materially below that means the SEM UNDERSTATES the instrument's noise and "
          f"every per-head number here carries an unmodelled term.")

    # ---- reading 3 -- KILL: is the floor itself item-set-dependent?
    poolA = [dropA[k] for k in band]
    poolB = [dropB[k] for k in band if k in dropB]
    fA, fB = 2 * sd(poolA), 2 * sd(poolB)
    div = 100 * abs(fA - fB) / fA
    print(f"\n  3 | KILL BRANCH -- exhaustive band floor, two disjoint item sets")
    print(f"      A {fA:.4f}   B {fB:.4f}   divergence {div:.1f}%   "
          f"(pre-registered threshold {KILL_FLOOR_DIVERGENCE:.0f}%)")
    killed = div > KILL_FLOOR_DIVERGENCE
    print(f"      -> {'FLOOR-IS-ITEM-SET-DEPENDENT' if killed else 'FLOOR-SURVIVES'}")
    if killed:
        print(f"         Every 'inside the floor' claim in this repository needs an item-set scope "
              f"it does not carry, including the headline.")
    else:
        print(f"         NOT evidence of item-set independence: n=2, and R4's lesson is that two "
              f"points do not establish a law. It is one comparison that did not fire.")

    out = HERE / 'results' / 'r11_analysis.json'
    json.dump({'n_measurable': n_meas, 'n_defined': n_def,
               'agree_within_sem': inside, 'n_band_pairs': tot, 'agree_pct': pct,
               'floor_A': fA, 'floor_B': fB, 'floor_divergence_pct': div,
               'kill_threshold_pct': KILL_FLOOR_DIVERGENCE,
               'verdict': 'FLOOR-IS-ITEM-SET-DEPENDENT' if killed else 'FLOOR-SURVIVES'},
              open(out, 'w'), indent=2)
    print(f"\n  -> {out}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
