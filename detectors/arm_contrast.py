#!/usr/bin/env python3
"""DETECTOR 7 — does the control arm differ from the studied arm in the property it claims to isolate,
and in NOTHING ELSE?

BORN FROM A MEASURED GAP, NOT A HUNCH. This repository's defect ledger (`defects.json`, validated by
`make verify`) records 22 defects sorted into the joints of a claim. Cross-tabulating them against
who found each one:

    joint          found by an instrument      found by an outside reader
    PROVENANCE               5                           0
    STATISTIC                2                           1
    INTERVENTION             1                           0
    CONTROL                  0                           3
    SCOPE                    0                           2

**No instrument in this repository has ever caught a CONTROL or SCOPE defect.** Six detectors, and
those two joints were found only by another mind. This one is aimed there.

THE DEFECT IT IS AIMED AT, verbatim from the ledger (D19, found by an outside reader after EIGHT
rounds had inherited it):

    label      "the sham arm controls for THAT you ablated a head"
    operation   band is the upper half and sham is the early layers, so it controls for that AND
                for where in the stack

THE RULE. A contrast between two arms isolates property P only if the arms differ in P **and agree
on everything else**. Two arms differing in {P, Q} isolate neither: any difference in outcome is
attributable to both. This is checkable the moment each arm declares what it is, so it is a
DESIGN-TIME check -- it fires before a GPU is booked, not after a reviewer reads the paper.

    PROPERTY    a contrast isolates exactly the property its claim names
    PROXY       the symmetric difference of the two arms' declared property dicts
    IMPLICATION   symdiff != {claimed}  =>  the contrast does not isolate the claim   (sound)
                  symdiff == {claimed}  =>  the contrast is valid                     (NOT sound:
                  it is only as good as the declaration, and an undeclared difference is invisible)
    WITNESS     an arm that declares {site, layers} but silently also differs in dtype passes here
                and is still confounded. The declaration is the interface; this detector checks
                consistency, not completeness.
    SAFE SIDE   it reports UNFIT on a mismatch and says nothing about a match beyond "the declared
                properties are consistent". A clean report is never evidence the arms are matched.

    python3 detectors/arm_contrast.py --selftest
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field


@dataclass
class Report:
    verdict: str
    isolates: str = ''
    symdiff: list = field(default_factory=list)
    why: list = field(default_factory=list)

    def ok(self) -> bool:
        return self.verdict == 'CONTRAST-VALID'


def check_contrast(arm_a: dict, arm_b: dict, isolates: str,
                   ignore: tuple = ()) -> Report:
    """arm_a, arm_b: {property -> value}. `isolates`: the single property the contrast claims.

    `ignore` exists for properties that are bookkeeping rather than experimental conditions (a run
    label, a seed that is shared by construction). It is a hole, so it is named in the output --
    a silent exemption list is how this check would be defeated.
    """
    r = Report('CONTRAST-VALID', isolates=isolates)
    keys = set(arm_a) | set(arm_b)
    missing = [k for k in keys if k not in arm_a or k not in arm_b]
    if missing:
        # AN UNDECLARED PROPERTY IS NOT AN EQUAL ONE. Treating a missing key as "same" is the
        # defaulting-.get failure: absent data made to look like agreement.
        return Report('CONTRAST-UNDECLARED', isolates=isolates, symdiff=sorted(missing),
                      why=[f"{sorted(missing)} declared on only one arm; a property present on one "
                           f"side and absent on the other is UNKNOWN, not equal"])
    diff = sorted(k for k in keys if k not in ignore and arm_a[k] != arm_b[k])
    r.symdiff = diff
    if ignore:
        r.why.append(f"ignored by request: {sorted(ignore)} -- each is a hole in this check")
    if isolates not in keys:
        return Report('CONTRAST-UNFIT', isolates=isolates, symdiff=diff,
                      why=[f"the contrast claims to isolate {isolates!r}, which neither arm "
                           f"declares. It cannot isolate a property that is not a condition."])
    if diff == [isolates]:
        r.why.append(f"the arms differ in {isolates!r} and agree on "
                     f"{len(keys) - len(ignore) - 1} other declared properties")
        return r
    extra = [k for k in diff if k != isolates]
    if isolates not in diff:
        return Report('CONTRAST-UNFIT', isolates=isolates, symdiff=diff,
                      why=[f"the arms do NOT differ in {isolates!r}, the property the contrast "
                           f"claims to isolate. They differ in {extra}."])
    return Report('CONTRAST-CONFOUNDED', isolates=isolates, symdiff=diff,
                  why=[f"the arms differ in {isolates!r} AND in {extra}. Any difference in outcome "
                       f"is attributable to {len(diff)} properties, so the contrast isolates none "
                       f"of them."])


def selftest() -> int:
    """It must FIRE on the real incident -- eight rounds inherited it -- before it clears anything."""
    ok = True

    # 1. THE REAL DEFECT. R1's band vs sham: both zero ONE head at the FINAL position; they differ
    #    in the layer range. The claim is that the contrast isolates WHICH head was ablated.
    band = {'intervention': 'zero', 'site': 'final', 'set_size': 1, 'layer_band': 'upper_half',
            'readout': 'margin4'}
    sham = {'intervention': 'zero', 'site': 'final', 'set_size': 1, 'layer_band': 'early',
            'readout': 'margin4'}
    r = check_contrast(band, sham, isolates='which_head')
    print(f"  [1] R1 band vs sham, claims 'which_head' -> {r.verdict}")
    print(f"      {r.why[0][:105]}")
    if r.ok():
        print("      FAIL: this is the defect that survived eight rounds"); ok = False

    # 2. The same arms, honestly labelled. What they DO isolate is the layer band, and this must
    #    pass -- a detector that fires on everything carries no information.
    r = check_contrast(band, sham, isolates='layer_band')
    print(f"  [2] the same two arms, claiming 'layer_band' -> {r.verdict}")
    if not r.ok():
        print(f"      FAIL: {r.why}"); ok = False

    # 3. A GENUINELY CONFOUNDED PAIR: differs in the claimed property AND another.
    a = {'intervention': 'zero', 'site': 'final', 'set_size': 1}
    b = {'intervention': 'mean', 'site': 'all', 'set_size': 1}
    r = check_contrast(a, b, isolates='intervention')
    print(f"  [3] differs in intervention AND site -> {r.verdict}  symdiff {r.symdiff}")
    if r.verdict != 'CONTRAST-CONFOUNDED':
        print("      FAIL"); ok = False

    # 4. A property declared on one arm only must be UNKNOWN, not equal. This is the
    #    defaulting-.get failure the repository has already recorded once.
    r = check_contrast({'intervention': 'zero', 'site': 'final'},
                       {'intervention': 'mean'}, isolates='intervention')
    print(f"  [4] property declared on one arm only -> {r.verdict}  missing {r.symdiff}")
    if r.verdict != 'CONTRAST-UNDECLARED':
        print("      FAIL: an absent declaration must not read as agreement"); ok = False

    # 5. Claiming to isolate something neither arm declares.
    r = check_contrast(a, {'intervention': 'mean', 'site': 'final', 'set_size': 1},
                       isolates='depth')
    print(f"  [5] isolates a property nobody declares -> {r.verdict}")
    if r.verdict != 'CONTRAST-UNFIT':
        print("      FAIL"); ok = False

    # 6. THE DECLARED HOLE, asserted so a clean report is never read as "the arms are matched":
    #    an undeclared difference is invisible to this check, by construction.
    r = check_contrast({'intervention': 'zero', 'site': 'final'},
                       {'intervention': 'mean', 'site': 'final'}, isolates='intervention')
    print(f"  [6] valid on DECLARED properties -> {r.verdict}  <- says nothing about undeclared ones")
    if not r.ok():
        print("      FAIL"); ok = False

    print(f"\n  SELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--a', help='JSON dict of arm A properties')
    ap.add_argument('--b', help='JSON dict of arm B properties')
    ap.add_argument('--isolates')
    args = ap.parse_args()
    if args.selftest or not (args.a and args.b and args.isolates):
        return selftest()
    r = check_contrast(json.loads(args.a), json.loads(args.b), args.isolates)
    print(json.dumps(r.__dict__, indent=2))
    return 0 if r.ok() else 1


if __name__ == '__main__':
    raise SystemExit(main())
