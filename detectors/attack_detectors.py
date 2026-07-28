#!/usr/bin/env python3
"""DETECTOR 8 — the detectors themselves, attacked with inputs derived from their own assumptions.

THE README CLAIMED THIS AND IT WAS FALSE. Every detector here is described as one that "refuses
rather than degrading". Their `--selftest`s prove they FIRE on the incident that produced them.
Nothing proved they REFUSE on input they cannot read — and on 2026-07-28, attacked with five
inputs, **three of five returned a clean verdict on garbage**:

    circularity      all-None predictions      -> NON-CIRCULAR
    control_fitness  empty readings list       -> CONTROL-FIT
    control_fitness  scale = 0                 -> CONTROL-FIT
    control_fitness  a NaN reading             -> CONTROL-FIT
    prose_numbers    one unclosed ``` fence    -> BACKED, having examined zero numbers

The `scale` argument of `control_fitness` was made REQUIRED specifically to close a tolerance that
scaled with the span, and **zero reopened exactly that hole**. NaN is worse: every comparison
against it is False, so every internal check passes silently. And one stray fence character turns
prose_numbers off for a whole file while it reports clean.

THE ATTACKS ARE DERIVED, NOT INVENTED. For each detector: read what it assumes about its input,
then violate exactly that. Inventing malformed inputs would test what I already thought of, which
is the failure mode an adversary exists to cover.

    python3 detectors/attack_detectors.py            run every attack
    python3 detectors/attack_detectors.py --selftest same thing; this file IS its own selftest
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

REFUSALS = ('UNRUNNABLE', 'UNDECIDABLE', 'REFUSED', 'CONTROL-UNFIT', 'CONTRAST-UNFIT',
            'CONTRAST-UNDECLARED', 'READOUT-INVALID', 'CIRCULAR', 'SUSPECT')


def attacks():
    from circularity import check_circularity
    from control_fitness import check_control
    from arm_contrast import check_contrast
    from prose_numbers import check_file

    out = []

    def add(name, assumption, fn):
        try:
            v = fn()
        except SystemExit as e:
            v = f'REFUSED ({e})'[:40]
        except Exception as e:                                    # noqa: BLE001
            v = f'RAISED {type(e).__name__}'
        out.append((name, assumption, v))

    add('circularity / all-None labels', 'labels are present',
        lambda: check_circularity([None] * 5, ['A'] * 5).verdict)
    add('control_fitness / empty readings', 'there is at least one reading',
        lambda: check_control(readings=[], reported_reading=0.0, scale=1.0).verdict)
    add('control_fitness / scale = 0', 'the scale is a positive reference quantity',
        lambda: check_control(readings=[1.0, 2.0], reported_reading=1.0, scale=0.0).verdict)
    add('control_fitness / NaN reading', 'readings are finite numbers',
        lambda: check_control(readings=[float('nan')], reported_reading=1.0, scale=1.0).verdict)
    add('arm_contrast / undeclared property', 'both arms declare the same property set',
        lambda: check_contrast({'a': 1, 'b': 2}, {'a': 2}, isolates='a').verdict)

    td = tempfile.mkdtemp()
    p = pathlib.Path(td) / 'x.md'
    p.write_text("```\nunclosed fence 9.99\n")
    add('prose_numbers / odd code fences', 'fences come in pairs',
        lambda: check_file(p, {1.0}).verdict)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.parse_args()
    rows = attacks()
    bad = []
    for name, assumption, verdict in rows:
        ok = any(verdict.startswith(r) for r in REFUSALS) or verdict.startswith('RAISED')
        print(f"  {'ok  ' if ok else 'PASS'} {name:<38}{verdict:<22}assumes: {assumption}")
        if not ok:
            bad.append((name, verdict))
    if bad:
        print(f"\n  {len(bad)} of {len(rows)} DEGRADED SILENTLY -- a clean verdict on input the "
              f"detector cannot read:")
        for n, v in bad:
            print(f"    {n} -> {v}")
        return 1
    print(f"\n  ATTACK PASS: {len(rows)} of {len(rows)} refuse rather than degrade")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
