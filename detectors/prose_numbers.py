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
    cmds = cmds or [
        [sys.executable, str(ROOT / 'headline.py'), '--json'],
        [sys.executable, str(ROOT / 'R4_predictability' / 'run.py')],
    ]
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
            v = float(tok)
            vals.add(v)
            # Generators print 3 decimals and prose usually quotes 2 or 1. Register the rounded
            # forms so "12.27" in JSON backs "12.3" in prose without a tolerance search that would
            # let any nearby number pass.
            for nd in (0, 1, 2, 3):
                vals.add(round(v, nd))
    return vals


def check_file(path: Path, gen: set) -> Report:
    text = path.read_text()
    exempt = set()
    for mk in MARKER.findall(text):
        for tok in NUM.findall(mk):
            exempt.add(float(tok))
    lines, unbacked, n = text.splitlines(), [], 0
    in_code = False
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            # Fenced blocks in this repo hold pasted generator output and shell commands. Their
            # numbers are quotations, not claims, and checking them would flag every command line.
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
            if v in exempt or v in gen or round(v, 2) in gen or round(v, 1) in gen:
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

        # 5. A fenced block is a quotation, not a claim.
        p.write_text("Text.\n```\nfold errors 155.9x\n```\n")
        r = check_file(p, gen)
        print(f"  [5] fenced output ignored   -> {r.verdict}")
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
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    if args.selftest:
        return selftest()

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
