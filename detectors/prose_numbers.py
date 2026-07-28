#!/usr/bin/env python3
"""DETECTOR 6 — a number in prose that no generator emits.

BORN FROM. Two claims in this repository reached a README from a commit message and could not be
regenerated afterwards: R4's leave-one-model-out fold errors (2.2 / 5.0 / 10.5 / 18.7 / 155.9x) and
R5's floor-widening range (2.4-5.2x). Both looked exactly like measurements. Both survived several
readings. Neither had a script behind it, and the only reason either was caught is that someone sat
down to write the generator that should have existed first.

WHAT IT CHECKS, AND IN WHICH DIRECTION IT IS SOUND.

    PROPERTY   every number a reader can check is produced by code in this repository
    PROXY      every number in the prose appears in some generator's output, within tolerance
    IMPLICATION   absent from all generator output  =>  NOT PRODUCED BY THEM        (sound)
                  present in some generator output  =>  the claim is correct        (NOT sound)
    WITNESS    R5's "0.90-1.94x" -- 1.94 IS emitted by headline.py (it is the true max of the
               effect-change ratio) while 0.90 is not (the true min is 0.69). Half of a wrong
               range matches. The detector reports the 0.90 and says nothing about the 1.94,
               which is exactly as much as this proxy can support.
    SAFE SIDE  it reports UNBACKED for numbers no generator emits, and says NOTHING about the
               ones it finds. It is a detector of absence and must never be read as a check
               that a matched number is right.

FALSE POSITIVES ARE THE COST OF THAT SOUNDNESS: years, model sizes, layer counts, set sizes and
commit hashes are all numbers no generator emits. They are exempted by an explicit inline marker in
the prose rather than by a pattern, because a pattern that guesses which numbers are "structural"
would silently exempt a real claim the day someone words it differently.

    <!-- unbacked-ok: 2026 1.5 3.5 --> on the line before, or anywhere in the file for a
    file-wide exemption. The marker is the author saying "this number is not a measurement",
    and it is greppable, reviewable and diffable -- which prose is not.

    python3 detectors/prose_numbers.py --selftest
    python3 detectors/prose_numbers.py README.md R5_factorial/README.md
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

# Numbers written in prose.
#
# THE FIRST VERSION OF THIS REGEX WAS BLIND TO EVERY RATIO IN THE REPOSITORY. Its trailing guard was
# `(?![\w.])`, and 'x' is a word character -- so "5.2x" matched nothing at all. Every quantity this
# project reports is written with an 'x' suffix, which means the detector's own selftest case 1
# passed on the half of the sentence that happens to be followed by a hyphen and silently skipped
# the other half. A pattern that cannot see the notation the subject is written in is not a weak
# detector; it is a detector of something else.
NUM = re.compile(r'(?<![\w.])(\d+(?:\.\d+)?)(?=[x%×]?(?![\w]))')
# ...AND THE SAME BUG CLASS BIT A SECOND TIME IN THE SAME HOUR. The first fix guarded with
# `(?![\w.])`, which still rejected "5.2x." -- 'x' is consumed by the optional suffix and the
# SENTENCE-ENDING PERIOD then fails the guard. Two selftest cases went quietly BACKED on files whose
# only number was unbacked. The guard is now `(?![\w])`: a period after a number ends a sentence,
# it does not continue the number, because the number pattern itself has already eaten any decimal
# point it was entitled to. Recorded rather than silently corrected because the lesson is that a
# tokenizer bug hides in the ONE character nobody puts in a test fixture.

# ONLY DECIMALS AND PERCENTAGES ARE CHECKED, AND THIS IS A DECLARED BLIND SPOT, not an oversight.
# Bare integers in this repository are overwhelmingly structural -- layer indices, set sizes, model
# counts, "2 sd", "3 of 4" -- and flagging them buries the real signal. Every measurement that has
# ever gone wrong here was a decimal. The cost: an unbacked INTEGER claim is invisible to this
# detector, and selftest case 7 asserts that it is, so that a clean report is never read as
# covering them.
def _checkable(tok: str, line: str, at: int) -> bool:
    return '.' in tok or line[at + len(tok):at + len(tok) + 1] in ('%', '×')
MARKER = re.compile(r'<!--\s*unbacked-ok:([^>]*)-->')


@dataclass
class Report:
    verdict: str
    unbacked: list = field(default_factory=list)
    n_prose: int = 0
    n_generated: int = 0
    exempt: set = field(default_factory=set)

    def ok(self) -> bool:
        return self.verdict == 'BACKED'


def generator_numbers(cmds=None) -> set:
    """Every number this repository's generators emit, as strings normalised to 4 decimals.

    Runs the generators rather than reading a cached list: a cached list is a description of the
    generators, and this file exists because descriptions drift from objects.
    """
    # headline.py --json embeds R4's whole result file, so R4's numbers are covered without
    # re-running its analysis. That matters for more than speed: headline.py imports nothing
    # outside the standard library, while R4's run.py needs numpy. Keeping the reference set
    # dependency-free is what lets `make verify` run for a stranger with a stock python -- and a
    # verification step that needs a scientific stack to check a claim about verification is a
    # joke at this repository's own expense.
    cmds = cmds or [[sys.executable, str(ROOT / 'headline.py'), '--json'],
                    [sys.executable, str(ROOT / 'validate_defects.py'), '--json']]
    out = []
    for c in cmds:
        try:
            r = subprocess.run(c, capture_output=True, text=True, timeout=300, cwd=str(ROOT))
        except Exception as e:                       # noqa: BLE001
            raise SystemExit(f"REFUSED: generator {c[-1]} could not run ({e}). A detector whose "
                             f"reference set is empty would report every number as unbacked, "
                             f"which is a false alarm dressed as vigilance.")
        if r.returncode != 0:
            raise SystemExit(f"REFUSED: generator {' '.join(c[-2:])} exited {r.returncode}. "
                             f"Fix the generator before asking what the prose is missing.\n"
                             f"{r.stderr[-800:]}")
        out.append(r.stdout)
    vals = set()
    for blob in out:
        for tok in NUM.findall(blob):
            vals.add(float(tok))
    return vals


def backs(prose_token: str, gen: set) -> bool:
    """Does some generated value round, AT THE PROSE'S OWN PRECISION, to the prose number?

    THIS REPLACED A LENIENCY BUG THAT LET A WRONG NUMBER THROUGH, and the bug was found by
    measuring the detector's false-pass rate rather than by reading a green report.

    The first version registered round(v, 0..3) for every emitted v, then accepted a prose number
    p if p OR round(p,1) OR round(p,2) was in that set. Two failures, one loud and one quiet:

      * it inflated the reference set 4x -- 200 emitted values became 803 -- so a random x.xx in
        [0,10), which is the shape of nearly every ratio in this repository, matched BY
        COINCIDENCE 57.9% of the time;
      * rounding the PROSE is the wrong direction. It let "2.31%" pass against a set containing
        2.3, because round(2.31, 1) == 2.3. Prose may be a rounding of a generated value; a
        generated value may not be a rounding of the prose.

    The rule here is the one that was meant all along: p is backed iff some v satisfies
    round(v, decimals(p)) == p. "12.3" backs 12.2718; "2.31" does not back 2.3.

    THE SIGN IS COMPARED BY MAGNITUDE, and that is a deliberate asymmetry. NUM never captures a
    leading sign, so prose "-0.0080" arrives here as 0.008 while the generator emits -0.00795.
    Matching |v| is what the docstring always said and what the first rewrite silently dropped --
    two real numbers in R2's table went unbacked for that reason alone. The cost is that this
    detector cannot see a SIGN error in prose; that is recorded as a second blind spot beside the
    integer one, not papered over.
    """
    dec = len(prose_token.split('.')[1]) if '.' in prose_token else 0
    p = float(prose_token)
    return any(round(abs(v), dec) == p for v in gen)


def check_file(path: Path, gen: set) -> Report:
    text = path.read_text()
    exempt = set()
    for mk in MARKER.findall(text):
        for tok in NUM.findall(mk):
            exempt.add(float(tok))
    # AN UNCLOSED FENCE SILENTLY DISABLES THIS CHECK FOR THE REST OF THE FILE. Attacked
    # 2026-07-28: a file whose first line is ``` returns BACKED having examined zero numbers,
    # because everything after it is treated as quoted generator output. One character turns
    # Detector 6 off for that file. Refuse loudly instead of reporting clean.
    if sum(1 for ln in text.splitlines() if ln.lstrip().startswith('```')) % 2:
        return Report('UNRUNNABLE', unbacked=[{'line': 0, 'value': -1.0,
                      'text': 'odd number of code fences: everything after the last unmatched ``` '
                              'would be skipped as quoted output, and this file would report '
                              'BACKED having checked nothing'}])
    lines, unbacked, n = text.splitlines(), [], 0
    in_code = False
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith('```'):
            in_code = not in_code
            continue
        # THE FENCE EXEMPTION IS GONE, AND IT WAS MEASURED BEFORE IT WAS REMOVED. 184 of 476
        # numbers across the READMEs lived inside fences and were invisible here -- 54% of the
        # front page, 69% of R7, 66% of R8, the files carrying the most important tables. The
        # exemption's premise was that a fenced block quotes generator output. Checked: 131 of 136
        # fenced numbers ARE emitted by a generator, so the premise mostly held -- and the five
        # that were not are real, are mine, and were hiding exactly where the exemption put them.
        # Removing it cost five flags and closed a hole that would have grown with every table.
        if False:
            continue
        if ln.lstrip().startswith('>'):
            # Blockquotes hold the annotated corrections -- they deliberately restate numbers that
            # are WRONG. Flagging those would demand deleting the record of the mistake, which is
            # the opposite of what this repository does with its mistakes.
            continue
        for mo in NUM.finditer(ln):
            tok = mo.group(1)
            if not _checkable(tok, ln, mo.start(1)):
                continue
            v = float(tok)
            n += 1
            if v in exempt or backs(tok, gen):
                continue
            unbacked.append({'line': i, 'value': v, 'text': ln.strip()[:110]})
    return Report('BACKED' if not unbacked else 'UNBACKED', unbacked, n, len(gen), exempt)


def selftest() -> int:
    """The detector must FIRE on the real incident before it is allowed to clear anything."""
    import tempfile
    ok = True
    gen = {2.74, 12.27, 6.0, 1.15, 1.31, 3.34, 1.39, 5.46, 0.69, 1.94}

    with tempfile.TemporaryDirectory() as td:
        # 1. THE REAL R5 SENTENCE, as it shipped. 2.4 and 5.2 and 0.90 are not emitted by any
        #    generator; 1.94 is. A detector that flags all four is guessing; one that flags none
        #    is the README that shipped.
        p = Path(td) / 'r5.md'
        p.write_text("The floor widens 2.4-5.2x while the effect changes by 0.90-1.94x.\n")
        r = check_file(p, gen)
        got = sorted(u['value'] for u in r.unbacked)
        want = [0.9, 2.4, 5.2]
        print(f"  [1] the shipped R5 sentence -> {r.verdict}, unbacked {got}")
        if r.ok() or got != want:
            print(f"      FAIL: expected UNBACKED {want}"); ok = False

        # 2. THE CORRECTED SENTENCE must come back clean, or the detector is unusable: a check
        #    that fires on the fixed version too carries no information about the fix.
        p.write_text("The floor widens 1.31-3.34x (2 sd) or 1.39-5.46x (p10-p90); "
                     "the effect changes 0.69-1.94x.\n")   # '2 sd' and 'p10' are integers: exempt
        r = check_file(p, gen)
        print(f"  [2] the corrected sentence  -> {r.verdict}")
        if not r.ok():
            print(f"      FAIL: {r.unbacked}"); ok = False

        # 3. HALF A WRONG RANGE MATCHES, and the witness in the docstring says so. This asserts the
        #    proxy's UNSOUND direction explicitly, so nobody later reads a clean line as a pass.
        p.write_text("The effect changes by 0.90-1.94x.\n")
        r = check_file(p, gen)
        got = sorted(u['value'] for u in r.unbacked)
        print(f"  [3] half-wrong range        -> {r.verdict}, unbacked {got} (1.94 NOT flagged)")
        if got != [0.9]:
            print(f"      FAIL: expected only [0.9]"); ok = False

        # 4. The exemption marker must work, and must be scoped to the numbers it names.
        p.write_text("<!-- unbacked-ok: 2.4 -->\nThe floor widens 2.4-5.2x.\n")
        r = check_file(p, gen)
        got = sorted(u['value'] for u in r.unbacked)
        print(f"  [4] marker exempts 2.4 only -> {r.verdict}, unbacked {got}")
        if got != [5.2]:
            print(f"      FAIL: expected [5.2]"); ok = False

        # 5. FENCED NUMBERS ARE CHECKED NOW, and this case changed with the contract rather than
        #    the contract changing to keep the case. It used to assert fences are ignored, on the
        #    premise that they quote generator output. Measured across the repository: 184 of 476
        #    README numbers lived in fences -- 54% of the front page -- and five of them were
        #    unbacked, hiding precisely where the exemption put them. A number in a fence that no
        #    generator emits is still a number nobody can check.
        p.write_text("Text.\n```\nfold errors 155.9x\n```\n")
        r = check_file(p, gen)
        got = sorted(u['value'] for u in r.unbacked)
        print(f"  [5] fenced UNBACKED number  -> {r.verdict}, unbacked {got}")
        if r.ok() or got != [155.9]:
            print("      FAIL: a fence must not hide an unbacked number"); ok = False

        # 5b. ...and a fenced number that IS emitted must still pass, or the check would flag every
        #     pasted stdout block and be turned off within a day.
        p.write_text("Text.\n```\nratio 2.74x\n```\n")
        r = check_file(p, gen)
        print(f"  [5b] fenced BACKED number   -> {r.verdict}")
        if not r.ok():
            print(f"      FAIL: {r.unbacked}"); ok = False

        # 8. THE LENIENCY THE OLD RULE HAD. Prose more precise than anything generated must FLAG.
        #    Under the previous rule "2.31" passed against a set containing 2.3.
        p.write_text("The overshoot was 2.31% of writes.\n")
        r = check_file(p, {2.3, 2.35})
        print(f"  [8] prose finer than the source -> {r.verdict}  "
              f"(2.31 must NOT be backed by 2.3)")
        if r.ok():
            print("      FAIL: rounding the PROSE is the wrong direction"); ok = False

        # 9. ...and the direction that IS legitimate must still pass: prose rounds a generated
        #    value. Without this, the fix would simply flag everything and look rigorous.
        p.write_text("The ratio is 12.3x.\n")
        r = check_file(p, {12.2718})
        print(f"  [9] prose rounds the source     -> {r.verdict}  (12.3 IS backed by 12.2718)")
        if not r.ok():
            print(f"      FAIL: {r.unbacked}"); ok = False

        # 10. A SIGNED generated value backs an UNSIGNED prose number, because NUM never captures
        #     the sign. Two real numbers in R2's table were unbacked for exactly this.
        p.write_text("The null median is -0.0080 on that model.\n")
        r = check_file(p, {-0.00795})
        print(f"  [10] signed source, unsigned prose -> {r.verdict}  (magnitude match)")
        if not r.ok():
            print(f"      FAIL: {r.unbacked}"); ok = False

        # 7. THE DECLARED BLIND SPOT, asserted so it cannot be forgotten. An unbacked integer is
        #    invisible here. This case exists to make a future reader who trusts a clean report
        #    read the line that says what the report does not cover.
        p.write_text("Exactly 47 of the effects cleared.\n")
        r = check_file(p, gen)
        print(f"  [7] unbacked INTEGER        -> {r.verdict}  <- declared blind spot, not a pass")
        if not r.ok():
            print("      FAIL: integers are documented as out of scope"); ok = False

        # 6. AND THE DETECTOR MUST REFUSE RATHER THAN CLEAR when its reference set is empty. An
        #    empty generator set would make every number 'backed' only if the logic were inverted,
        #    and would make every number 'unbacked' as written -- so the failure mode here is a
        #    storm of false alarms, which is loud. The refusal in generator_numbers() covers the
        #    quiet direction: a generator that exits non-zero must stop the check, not shrink it.
        p.write_text("The ratio is 2.74x.\n")
        r = check_file(p, set())
        print(f"  [6] empty reference set     -> {r.verdict} (loud, not silent)")
        if r.ok():
            print("      FAIL: an empty reference set must not clear anything"); ok = False

    print(f"\n  SELFTEST {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='*')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--power', action='store_true',
                    help='measure the coincidence rate: how often a RANDOM number is "backed"')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.power:
        # A DETECTOR OF ABSENCE IS ONLY AS GOOD AS THE CHANCE OF A COINCIDENTAL PRESENCE, and that
        # chance grows every time a generator learns to emit another number. Measured rather than
        # assumed: an earlier matching rule registered four rounded forms of every emitted value,
        # inflating the set to 803 and giving a random x.xx in [0,10) -- the shape of nearly every
        # ratio here -- a 57.9% chance of passing. That is not a detector, and no green report
        # would have said so.
        import random as _r
        gen = generator_numbers()
        print(f"  reference set: {len(gen)} values emitted by this repo's generators\n")
        for lo, hi, nd, label in ((0, 10, 2, 'x.xx  in [0,10)'),
                                  (0, 100, 1, 'xx.x  in [0,100)'),
                                  (0, 1000, 0, 'integer in [0,1000)')):
            rng = _r.Random(7)
            trials = 20000
            hits = sum(1 for _ in range(trials)
                       if backs(f"%.{nd}f" % rng.uniform(lo, hi), gen))
            print(f"  a random {label:<20} is 'backed' by coincidence "
                  f"{100*hits/trials:5.2f}% of the time")
        print("\n  Read this as the detector's FALSE-PASS rate. It bounds nothing about the\n"
              "  sound direction -- a number absent from the set was still not generated -- but a\n"
              "  clean report on the x.xx row is worth roughly (1 - that rate) per number.")
        return 0

    files = [Path(f) for f in args.files] or sorted(ROOT.glob('**/README.md'))
    files = [f for f in files if '.git' not in f.parts]
    gen = generator_numbers()
    print(f"  reference set: {len(gen)} distinct values emitted by this repo's generators\n")
    bad, reports = 0, {}
    for f in files:
        r = check_file(f, gen)
        reports[str(f.relative_to(ROOT))] = r.__dict__ | {'exempt': sorted(r.exempt)}
        mark = 'ok  ' if r.ok() else 'FLAG'
        print(f"  {mark} {str(f.relative_to(ROOT)):<40} {r.n_prose:>4} numbers, "
              f"{len(r.unbacked)} unbacked")
        for u in r.unbacked:
            print(f"         line {u['line']:>3}: {u['value']}  |  {u['text']}")
        bad += not r.ok()
    if args.json:
        print(json.dumps(reports, indent=2, default=str))
    print(f"\n  {len(files) - bad} of {len(files)} files fully backed")
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
