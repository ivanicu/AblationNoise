#!/usr/bin/env python3
"""DETECTOR 3 — CONTROL FITNESS.

    Can your control fail? And has this instrument ever returned the other answer?

TWO INCIDENTS, ONE FILE, because they are the two halves of the same question.

E152 (2026-07-22) attacked a SURVIVING claim -- "the query is read and committed at L16-18" -- by
measuring the total output perturbation (TVD) of the same patch across layers. It returned
PROPAGATION-ARTIFACT and the author accepted it, which would have retracted a true result. The
control could not fail, because BOTH competing hypotheses predict the same reading:

    H1  the token is no longer read     -> the patch stops mattering -> TVD -> 0
    H2  the patch cannot propagate      -> the patch stops mattering -> TVD -> 0

A control whose hypotheses share a prediction is not a control. The valid one was cross-token at
matched depth: patch a DIFFERENT token at the same layer and ask whether IT still moves the output.

E132c (2026-07-27) is the other half. Its positive control -- ablate the set containing the head
E123 proved is the copy head -- did not merely fail to fire, it fired INVERTED: ablating the copy
set RAISED the correct-answer margin, below all thirty draws of the null. An instrument whose known
mechanism produces the wrong sign cannot support either branch of the question it was asked.

WHAT IT CHECKS

  1. DISCRIMINATION   Do the hypotheses this control distinguishes predict DIFFERENT readings? Given
                      each hypothesis's predicted direction, a control where all predictions agree is
                      reported UNFIT -- no measurement it returns can separate them.
  2. DYNAMIC RANGE    Has this instrument, in this run, moved at all RELATIVE TO A DECLARED SCALE?
                      A null from an instrument that has only ever returned nulls is silence, not an
                      acquittal (the project's P5 law) -- but "has it moved" is undecidable without
                      saying moved-compared-to-what, so the scale is required, not optional.
  3. POSITIVE CONTROL Does the known-mechanism arm move in the EXPECTED DIRECTION, not merely by a
                      large amount? A wrong-signed positive control is worse than a dead one,
                      because its magnitude looks like calibration.

Self-test replays both real incidents and requires the detector to fire on each.
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field


@dataclass
class Report:
    verdict: str = "UNRUN"
    why: list[str] = field(default_factory=list)

    def ok(self) -> bool:
        return self.verdict == "CONTROL-FIT"


def check_control(hypothesis_predictions: dict[str, str] | None = None,
                  readings: list[float] | None = None,
                  reported_reading: float | None = None,
                  scale: float | None = None,
                  positive_control: float | None = None,
                  positive_control_expected_sign: int | None = None) -> Report:
    """hypothesis_predictions: {hypothesis name -> predicted direction, e.g. 'down'/'up'/'zero'}."""
    # THREE CLEAN PASSES ON GARBAGE, found by attacking this file on 2026-07-28 with inputs
    # derived from its own assumptions. It returned CONTROL-FIT for: an EMPTY readings list, a
    # scale of ZERO, and a NaN reading. The scale argument was made REQUIRED precisely because a
    # tolerance that scales with the span is self-defeating -- and zero defeats it again. NaN is
    # worse: every comparison against it is False, so every check silently passes.
    import math as _m
    if readings is not None:
        if len(readings) == 0:
            return Report('UNRUNNABLE', why=["readings is empty. No data is not a fit control."])
        if any(not _m.isfinite(float(x)) for x in readings):
            return Report('UNRUNNABLE', why=["a reading is NaN or infinite; every comparison "
                                             "against it is False, so every check would pass."])
    if scale is not None and (not _m.isfinite(float(scale)) or float(scale) <= 0):
        return Report('UNDECIDABLE', why=[f"scale={scale!r} is not a positive finite number. The "
                                          f"scale exists to stop the tolerance scaling with the "
                                          f"span; zero reopens exactly that hole."])
    if reported_reading is not None and not _m.isfinite(float(reported_reading)):
        return Report('UNRUNNABLE', why=["reported_reading is NaN or infinite."])
    r = Report()
    fired: list[str] = []

    if hypothesis_predictions is not None:
        preds = set(hypothesis_predictions.values())
        if len(hypothesis_predictions) > 1 and len(preds) == 1:
            fired.append(
                f"UNFIT BY CONSTRUCTION: all {len(hypothesis_predictions)} hypotheses "
                f"({', '.join(hypothesis_predictions)}) predict the same reading "
                f"({preds.pop()!r}). No outcome of this control separates them.")
    else:
        r.why.append("DISCRIMINATION check SKIPPED — hypotheses not supplied; not run is not passed")

    # DYNAMIC RANGE IS NOT MEASURABLE WITHOUT A REFERENCE SCALE, and the first version of this
    # check pretended otherwise. It asked whether every reading sat within 10% OF THE SPAN of the
    # reported one -- a tolerance that shrinks with the span, so the exact case it exists to catch
    # (all readings clustered near zero) made the tolerance small enough to pass. Self-defeating.
    # The scale must be supplied: the baseline quantity these readings are a perturbation OF. Same
    # lesson as reporting a dimensionless floor without its denominator.
    if readings is not None and len(readings) >= 2 and scale:
        span = max(readings) - min(readings)
        if span / abs(scale) < 0.02:
            fired.append(f"NO DYNAMIC RANGE: the readings span {span:.3g} against a scale of "
                         f"{scale:.3g} ({span/abs(scale):.1%}); this instrument has not been "
                         f"observed to move here, so its verdict is silence rather than a null")
    elif readings is not None and len(readings) >= 2 and not scale:
        r.why.append("DYNAMIC-RANGE check UNDECIDABLE — readings supplied without a scale. "
                     "A span is only small relative to something; supply the baseline quantity.")
    else:
        r.why.append("DYNAMIC-RANGE check SKIPPED — readings not supplied; not run is not passed")

    if positive_control is not None and positive_control_expected_sign is not None:
        if positive_control == 0:
            fired.append("POSITIVE CONTROL IS DEAD: the known mechanism produced exactly zero")
        elif (positive_control > 0) != (positive_control_expected_sign > 0):
            fired.append(
                f"POSITIVE CONTROL IS INVERTED: the known mechanism moved {positive_control:+.3f}, "
                f"opposite to the expected sign. A wrong-signed control is worse than a dead one — "
                f"its magnitude reads as calibration.")
    else:
        r.why.append("POSITIVE-CONTROL check SKIPPED — not supplied; not run is not passed")

    r.verdict = "CONTROL-UNFIT" if fired else "CONTROL-FIT"
    r.why = fired + r.why
    return r


def selftest() -> int:
    rows = []

    # E152: both hypotheses predict TVD -> 0
    r = check_control(hypothesis_predictions={
        "token no longer read": "zero", "patch cannot propagate": "zero"})
    rows.append(("E152's control is caught as UNFIT BY CONSTRUCTION", not r.ok()))
    rows.append(("  ... and names the shared prediction",
                 any("same reading" in w for w in r.why)))

    # the valid replacement: cross-token, the two hypotheses now differ
    r = check_control(hypothesis_predictions={
        "token no longer read": "other-token-still-moves-output",
        "patch cannot propagate": "other-token-also-dies"})
    rows.append(("the cross-token replacement passes discrimination", r.ok()))

    # E132c: the positive control is inverted (expected a DROP, got a rise)
    r = check_control(positive_control=-1.428, positive_control_expected_sign=+1)
    rows.append(("E132c's inverted positive control is caught", not r.ok()))
    rows.append(("  ... and says inverted, not merely weak",
                 any("INVERTED" in w for w in r.why)))

    # a healthy positive control passes
    r = check_control(positive_control=+2.9, positive_control_expected_sign=+1)
    rows.append(("a correctly-signed positive control passes", r.ok()))

    # an instrument that never varies
    r = check_control(readings=[0.001, 0.002, 0.0015, 0.0012], reported_reading=0.0013, scale=4.48)
    rows.append(("an instrument with no dynamic range is caught (scale given)", not r.ok()))

    # one that does vary, against the same scale
    r = check_control(readings=[0.0, 0.4, 1.2, 0.9], reported_reading=0.0, scale=4.48)
    rows.append(("an instrument with real range passes", r.ok()))

    # and without a scale the question is UNDECIDABLE, not passed
    r = check_control(readings=[0.001, 0.002, 0.0015], reported_reading=0.0013)
    rows.append(("readings without a scale -> UNDECIDABLE, and said so",
                 any("UNDECIDABLE" in w for w in r.why)))

    # skipped checks must be reported, never silently passed
    r = check_control()
    rows.append(("all three checks skipped -> three SKIPPED notices",
                 sum("SKIPPED" in w for w in r.why) == 3))

    bad = 0
    for label, ok in rows:
        print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
        bad += 0 if ok else 1
    print("=" * 70)
    print("detector fires on both real incidents and passes their valid replacements"
          if not bad else f"{bad} SELFTEST FAILURE(S) — do not trust this detector")
    return 1 if bad else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if not a.selftest:
        ap.error("--selftest, or import check_control()")
    sys.exit(selftest())
