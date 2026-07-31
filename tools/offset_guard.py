#!/usr/bin/env python3
"""SUBMIT-TIME GUARD: a scan's reference must be drawn from the SAME item set as the scan.

Built after the THIRD occurrence of one defect, which is this project's threshold for building
infrastructure instead of patching again:

    |delta| 1.871e-01   (recorded, then walked back into)
    |delta| 1.082e-01   (task 483, qwen2.5-3b I_final off400 against an offset-0 reference)
    |delta| 1.874e-01   (task 484, qwen2.5-1.5b I_all off400 against an offset-0 reference)

Every one is the same thing: `--seed-offset N` draws a DIFFERENT ITEM SET, so a reference built at
offset 0 has a different base_margin, and scan.py's registered positive control fires by
construction. The halt worked all three times. The submission did not.

═══ THE FINGERPRINT ═══
The reference JSONs do NOT record their seed offset -- both offset-0 and offset-400 files carry the
same `draw_seed: 20260727`, so the offset is invisible in metadata. But `base_margin` IS a
deterministic function of the item set, and it differs:

    qwen2.5-1.5b  offset   0  ->  4.476821851730347   (R10_exhaustive)
    qwen2.5-1.5b  offset 400  ->  4.417667237917582   (R11 itemsB)

So the guard identifies an item set by its base_margin, not by a label that does not exist.

═══ THE RULE, AND IT REFUSES BY DEFAULT ═══
An UNKNOWN (tag, offset) pair is REFUSED, not passed. A guard that waves through what it has never
seen is the blind-instrument failure this project has already made twice. New pairs are admitted
only by measuring their base_margin and adding it here deliberately.

Usage:
    offset_guard.py --tag qwen2.5-1.5b --seed-offset 400 --ref path/to/ref.json
    exit 0 = the reference matches the item set; exit 1 = REFUSED, do not submit.
"""
import argparse
import json
import pathlib
import sys

TOL = 1e-6

# (tag, seed_offset) -> base_margin of THAT item set. Measured from the object, never assumed.
KNOWN = {
    ('qwen2.5-1.5b', 0): 4.476821851730347,
    ('qwen2.5-1.5b', 400): 4.417667237917582,
}


def check(tag, offset, ref):
    p = pathlib.Path(ref)
    if not p.exists():
        return 1, f'REFUSED: reference does not exist: {ref}'
    try:
        bm = json.load(open(p)).get('base_margin')
    except (OSError, ValueError) as e:
        return 1, f'REFUSED: reference unreadable: {e}'
    if bm is None:
        return 1, f'REFUSED: reference has no base_margin, so its item set cannot be identified'
    key = (tag, offset)
    if key not in KNOWN:
        return 1, (f'REFUSED: ({tag}, offset {offset}) is not in the registry. An unknown pair is '
                   f'refused, never passed — measure its base_margin and add it deliberately. '
                   f'The reference on disk has base_margin {bm:.15g}.')
    want = KNOWN[key]
    if abs(bm - want) > TOL:
        other = [f'{k[1]}' for k, v in KNOWN.items()
                 if k[0] == tag and abs(v - bm) <= TOL]
        hint = f' — that base_margin belongs to offset {other[0]}' if other else ''
        return 1, (f'REFUSED: reference base_margin {bm:.15g} does not match ({tag}, offset '
                   f'{offset}) which requires {want:.15g}{hint}. |delta| {abs(bm - want):.3e}. '
                   f'This is the defect that killed tasks 483 and 484.')
    return 0, f'OK: reference base_margin {bm:.15g} matches ({tag}, offset {offset})'


def selftest():
    """Positive AND negative control on the guard itself, run with --selftest."""
    root = pathlib.Path(__file__).resolve().parent.parent
    r10 = root / 'R10_exhaustive' / 'results' / 'r10_exhaustive_qwen2.5-1.5b.json'
    r11b = root / 'R11_instrument_noise' / 'results' / 'r11_itemsB_qwen2.5-1.5b.json'
    cases = [
        ('POSITIVE  offset 0 with the offset-0 reference', 'qwen2.5-1.5b', 0, r10, 0),
        ('POSITIVE  offset 400 with the offset-400 reference', 'qwen2.5-1.5b', 400, r11b, 0),
        ('NEGATIVE  offset 400 with the offset-0 reference  <- task 484', 'qwen2.5-1.5b', 400,
         r10, 1),
        ('NEGATIVE  offset 0 with the offset-400 reference', 'qwen2.5-1.5b', 0, r11b, 1),
        ('NEGATIVE  an unregistered pair must be REFUSED, not passed', 'qwen2.5-1.5b', 800, r10, 1),
        ('NEGATIVE  an unregistered MODEL must be REFUSED', 'qwen2.5-3b', 400, r10, 1),
    ]
    ok = True
    for name, tag, off, ref, want in cases:
        rc, msg = check(tag, off, ref)
        good = rc == want
        ok &= good
        print(f'  [{"pass" if good else "FAIL"}] {name}\n         rc={rc} (want {want})  {msg[:110]}')
    print(f'\n  guard selftest: {"BOTH CONTROLS PASS" if ok else "BROKEN"}')
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag')
    ap.add_argument('--seed-offset', type=int, default=0)
    ap.add_argument('--ref')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.tag and a.ref):
        print('REFUSED: --tag and --ref are required')
        return 1
    rc, msg = check(a.tag, a.seed_offset, a.ref)
    print(msg)
    return rc


if __name__ == '__main__':
    sys.exit(main())
