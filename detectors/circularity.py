#!/usr/bin/env python3
"""DETECTOR 2 — CIRCULARITY.

    Is your predictor already the answer?

WHERE IT CAME FROM. On 2026-07-22 this project derived a prospective "routing-margin law": a
logistic fit of retrieval success on one attention head's routing margin, fit at k=4,8, predicting
held-out accuracy at k=16,24 within 0.021. It came with a mechanistic account of lost-in-the-middle,
a mechanism-derived repair, and a self-declared RE_COMPLETE.

Fifteen minutes later E151 asked one question and all of it died (`1b283bd`):

    P(model's answer == the head's argmax-attention room) = 0.86 - 0.96 across k

The head is a copy head. Its attention IS approximately the answer, so a statistic built from that
attention is a noisier restatement of the answer, not a predictor of it. Confirmed from the other
side: the model's OWN logit margin, fit the same prospective way, predicted held-out accuracy
within 0.004-0.007 -- three to five times BETTER than the attention margin's 0.015-0.021. The
"law" added nothing over the model being calibrated.

WHY THIS NEEDS A DETECTOR RATHER THAN VIGILANCE. Every diagnostic that fired was green. The fit was
genuinely out-of-sample. The AUROC was genuinely 0.89. The repair genuinely worked. Nothing in the
result looked wrong; what was wrong was upstream of the result, in what the predictor was made of.
An out-of-sample score cannot detect circularity, because a tautology generalises perfectly.

WHAT IT CHECKS

  1. TAUTOLOGY, ABOVE CHANCE.  Raw P(answer == predictor's top choice) is NOT the quantity: with
                      imbalanced labels two unrelated sequences agree a lot for free. The detector's
                      own selftest exposed this -- a deliberately unrelated predictor scored 0.619
                      agreement and was flagged. What is gated is the excess over the agreement the
                      marginals alone produce,
                          kappa = (observed - chance) / (1 - chance),
                          chance = sum_c P(answer=c) * P(predictor=c)
                      Both are reported. Thresholds are judgements and are stated, not hidden:
                      kappa >= 0.70 CIRCULAR, 0.40-0.70 SUSPECT, below that clear on this axis.
  2. TRIVIAL BASELINE Does a predictor the model already exposes -- its own output margin -- do the
                      same job as well or better? If yes, the fancy predictor adds nothing whether
                      or not it is circular. Optional; SKIPPED is reported, never counted as pass.
  3. DEGENERACY       Does the predictor vary at all across items? A constant predictor scores
                      perfectly against a constant outcome and explains nothing.

The three are independent. A predictor can be non-circular and still add nothing (2 fires alone),
or vary healthily and still be the answer restated (1 fires alone).

Usage:
    from detectors.circularity import check_circularity
    r = check_circularity(answers=[...], predictor_choices=[...],
                          predictor_err=0.021, baseline_err=0.006)

Self-test: `python3 detectors/circularity.py --selftest` -- it must FIRE on this project's real
E151 numbers and PASS on a predictor built from something the answer cannot contain.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict


@dataclass
class Report:
    n: int = 0
    tautology_rate: float | None = None
    chance_rate: float | None = None
    kappa: float | None = None
    predictor_err: float | None = None
    baseline_err: float | None = None
    beats_baseline: bool | None = None
    predictor_unique_values: int | None = None
    baseline_checked: bool = False
    verdict: str = "UNRUN"
    why: list[str] = field(default_factory=list)

    def ok(self) -> bool:
        return self.verdict == "NON-CIRCULAR"


CIRCULAR_AT = 0.70          # on kappa, not on raw agreement
SUSPECT_AT = 0.40


def check_circularity(answers, predictor_choices,
                      predictor_err: float | None = None,
                      baseline_err: float | None = None,
                      predictor_values=None) -> Report:
    """answers / predictor_choices: per-item labels. predictor_err / baseline_err: held-out error."""
    # A PREDICTION THAT IS NONE IS NOT A PREDICTION. Attacked 2026-07-28 with an all-None
    # predictor and this function returned NON-CIRCULAR -- certifying an extractor that produced
    # nothing. Same shape as the defaulting-.get failure already in this repository's ledger:
    # absent data made to look like agreement.
    for _nm, _seq in (('answers', answers), ('predictor_choices', predictor_choices)):
        if _seq is not None and any(x is None for x in _seq):
            _k = sum(x is None for x in _seq)
            # KEYWORD, NOT POSITIONAL. The first attempt at this guard passed the verdict
            # positionally and `verdict` is not this dataclass's first field, so it landed in `n`
            # and the report came back with the DEFAULT verdict "UNRUN" -- a silent wrong-field
            # write, inside the fix for silent wrong answers.
            return Report(verdict='UNRUNNABLE', n=len(_seq),
                          why=[f"{_k} of {len(_seq)} {_nm} are None. Absent labels are UNKNOWN, "
                               f"not agreement and not non-circularity."])
    r = Report()
    if len(answers) != len(predictor_choices):
        r.verdict = "UNRUNNABLE"
        r.why.append(f"length mismatch: {len(answers)} answers, {len(predictor_choices)} choices")
        return r
    r.n = len(answers)
    if r.n == 0:
        r.verdict = "UNRUNNABLE"
        r.why.append("no items — a rate over zero items is not a measurement")
        return r

    # 1. tautology, corrected for the agreement the marginals give away for free
    r.tautology_rate = sum(1 for a, c in zip(answers, predictor_choices) if a == c) / r.n
    from collections import Counter
    ca, cp = Counter(answers), Counter(predictor_choices)
    r.chance_rate = sum((ca[c] / r.n) * (cp.get(c, 0) / r.n) for c in ca)
    r.kappa = ((r.tautology_rate - r.chance_rate) / (1 - r.chance_rate)
               if r.chance_rate < 1 else 1.0)

    # 3. degeneracy
    if predictor_values is not None:
        r.predictor_unique_values = len(set(predictor_values))

    # 2. trivial baseline
    if predictor_err is not None and baseline_err is not None:
        r.baseline_checked = True
        r.predictor_err, r.baseline_err = predictor_err, baseline_err
        r.beats_baseline = predictor_err < baseline_err

    fired = []
    if r.kappa >= CIRCULAR_AT:
        fired.append(f"agreement {r.tautology_rate:.3f} vs chance {r.chance_rate:.3f} -> kappa "
                     f"{r.kappa:.3f} >= {CIRCULAR_AT}: the predictor's top choice IS the answer far "
                     f"beyond what the marginals give, so a statistic built from it restates the "
                     f"answer rather than predicting it")
    elif r.kappa >= SUSPECT_AT:
        fired.append(f"kappa {r.kappa:.3f} in [{SUSPECT_AT}, {CIRCULAR_AT}): suspect, not decided "
                     f"by this axis alone")
    if r.predictor_unique_values is not None and r.predictor_unique_values < 3:
        fired.append(f"predictor takes only {r.predictor_unique_values} distinct values — a nearly "
                     f"constant predictor explains nothing however well it scores")
    if r.beats_baseline is False:
        fired.append(f"the model's OWN output margin predicts at least as well "
                     f"({r.baseline_err:.4f} vs {r.predictor_err:.4f}), so the predictor adds "
                     f"nothing over the model being calibrated")

    if not r.baseline_checked:
        r.why.append("TRIVIAL-BASELINE check SKIPPED — not run is not passed; supply "
                     "predictor_err and baseline_err to close it")

    if (r.kappa is not None and r.kappa >= CIRCULAR_AT) or r.beats_baseline is False:
        r.verdict = "CIRCULAR"
    elif fired:
        r.verdict = "SUSPECT"
    else:
        r.verdict = "NON-CIRCULAR"
    r.why = fired + r.why
    return r


def selftest() -> int:
    rows = []

    # (a) the real thing: E151's measured tautology rates and the two prospective errors
    E151 = {"4": 0.956, "8": 0.900, "16": 0.860, "24": 0.876}
    ATTN_ERR = {"16": 0.015080528526261516, "24": 0.020718009693092232}
    LOGIT_ERR = {"16": 0.0065900439279622525, "24": 0.004023191807804971}
    ROOMS4 = ["stone", "iron", "glass", "water"]
    for k, taut in E151.items():
        # answers roughly uniform over four rooms, as in the real task; the predictor agrees at the
        # measured rate and otherwise picks a DIFFERENT room. An all-one-answer fixture would give
        # chance == the agreement rate and kappa 0, i.e. it would exonerate the real case.
        n = 500
        hits = round(taut * n)
        ans = [ROOMS4[i % 4] for i in range(n)]
        pred = [ans[i] if i < hits else ROOMS4[(i + 1) % 4] for i in range(n)]
        r = check_circularity(ans, pred,
                              predictor_err=ATTN_ERR.get(k), baseline_err=LOGIT_ERR.get(k))
        rows.append((f"E151 k={k} (tautology {taut}) is caught", r.verdict == "CIRCULAR"))

    # (b) a predictor that is NOT the answer and DOES beat the trivial baseline
    n = 500
    ans = ["A" if i % 3 else "B" for i in range(n)]
    pred = ["A" if i % 7 else "B" for i in range(n)]        # agrees only by chance
    r = check_circularity(ans, pred, predictor_err=0.01, baseline_err=0.05,
                          predictor_values=list(range(n)))
    rows.append(("a non-circular predictor that beats the baseline passes", r.ok()))

    # (c) non-circular but adds nothing over the model's own margin
    r = check_circularity(ans, pred, predictor_err=0.05, baseline_err=0.01)
    rows.append(("a predictor beaten by the trivial baseline is CIRCULAR-flagged",
                 r.verdict == "CIRCULAR"))

    # (d) a constant predictor is caught even at a low tautology rate
    r = check_circularity(ans, pred, predictor_values=[1.0] * n)
    rows.append(("a constant predictor is flagged", r.verdict != "NON-CIRCULAR"))

    # (e) the skipped baseline must be reported, never silently passed
    r = check_circularity(ans, pred)
    rows.append(("a skipped baseline check is reported as skipped",
                 any("SKIPPED" in w for w in r.why)))

    # (f) zero items must be unrunnable, not a pass
    r = check_circularity([], [])
    rows.append(("zero items is UNRUNNABLE, not a pass", r.verdict == "UNRUNNABLE"))

    bad = 0
    for label, ok in rows:
        print(f"  {'ok  ' if ok else 'FAIL'}  {label}")
        bad += 0 if ok else 1
    print("=" * 70)
    print("detector fires on the real case and passes the clean one"
          if not bad else f"{bad} SELFTEST FAILURE(S) — do not trust this detector")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--json-in', help='file with {"answers":[], "predictor_choices":[], ...}')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.json_in:
        ap.error("--json-in is required unless --selftest")
    d = json.load(open(a.json_in))
    r = check_circularity(d["answers"], d["predictor_choices"],
                          d.get("predictor_err"), d.get("baseline_err"),
                          d.get("predictor_values"))
    print(json.dumps(asdict(r), indent=1))
    return 0 if r.ok() else 2


if __name__ == '__main__':
    sys.exit(main())
