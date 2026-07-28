#!/usr/bin/env python3
"""Validate the defect ledger against the git history, then score the pre-registered taxonomy test.

WHY THIS IS A SCRIPT AND NOT A TABLE IN A README. The ledger's only value is that it is EXHIBITED
rather than asserted -- which is the criticism an outside reader made of this repository's own
"seven of eight" claim, stated in the README and shown nowhere. A hand-written ledger is a
self-report. One whose every row must resolve to a commit that is an ancestor of HEAD, or the build
fails, is not.

`git cat-file -t` is NOT the check. A SHA can resolve locally and be unreachable from HEAD -- that
exact false all-clear cost this project's sibling a day. The predicate is
`git merge-base --is-ancestor`.

AND THAT PREDICATE IS THREE-VALUED, which the first version got wrong in the file whose whole job
is to enforce that it is not. Run from a `git archive` tarball -- which is exactly what a GitHub
ZIP download is -- it printed "commit abe158b is not an ancestor of HEAD" for all 22 rows and
failed the build. The sentence is false: there was no repository to check against. A missing
instrument reported as a failed test, on the flagship command, for the most common way people
obtain code.

    python3 validate_defects.py            validate and score
    python3 validate_defects.py --json     machine-readable
"""
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BINS = ('INTERVENTION', 'CONTROL', 'STATISTIC', 'SCOPE', 'PROVENANCE', 'UNCLASSIFIED')

# The thresholds are copied from DEFECT_TAXONOMY_PREREGISTRATION.md, which was committed before any
# row of defects.json was written. They are asserted against that file below rather than trusted.
W_A = "TAXONOMY-EXISTS"
W_B = "THIRTEEN-ONE-OFFS"
W_C = "ONE-JOINT-DOMINATES"


def in_git_worktree() -> bool:
    r = subprocess.run(['git', 'rev-parse', '--is-inside-work-tree'],
                       cwd=str(HERE), capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() == 'true'


def ancestry(sha: str) -> str:
    '''CONFIRMED / OVERTURNED / UNVERIFIED -- three-valued, because two of these are not failures.

    THE FIRST VERSION FOLDED UNVERIFIED INTO OVERTURNED, in the file whose job is to enforce the
    rule against exactly that. Run from a `git archive` tarball -- which is what a GitHub ZIP
    download is -- it printed `commit abe158b is not an ancestor of HEAD` twenty-two times. That
    sentence is FALSE. The truth is "there is no repository here, so I could not check", and the
    difference between those is this repository's cardinal law.

    Worse than wrong: it fired on the FLAGSHIP command for the most common way people get code.
    '''
    if not in_git_worktree():
        return 'UNVERIFIED'
    r = subprocess.run(['git', 'cat-file', '-e', sha + '^{commit}'],
                       cwd=str(HERE), capture_output=True)
    if r.returncode != 0:
        # The object is absent -- a shallow clone, or history rewritten downstream. Still not a
        # statement about the row.
        return 'UNVERIFIED'
    ok = subprocess.run(['git', 'merge-base', '--is-ancestor', sha, 'HEAD'],
                        cwd=str(HERE), capture_output=True).returncode == 0
    return 'CONFIRMED' if ok else 'OVERTURNED'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    d = json.load(open(HERE / 'defects.json'))
    rows = d['defects']

    # --- the admission rule, enforced ------------------------------------------------------
    bad, unver = [], []
    have_git = in_git_worktree()
    for r in rows:
        if r['bin'] not in BINS:
            bad.append((r['id'], f"bin {r['bin']!r} is not one of the pre-registered bins"))
        v = ancestry(r['commit'])
        if v == 'OVERTURNED':
            bad.append((r['id'], f"commit {r['commit']} resolves here but is NOT an ancestor "
                                 f"of HEAD -- the row points at unreachable history"))
        elif v == 'UNVERIFIED':
            unver.append(r['id'])
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(ids):
        bad.append(('-', 'duplicate ids'))

    # --- the pre-registered thresholds must still be the ones in the pre-registration -------
    prereg = (HERE / 'DEFECT_TAXONOMY_PREREGISTRATION.md').read_text()
    for needle in ('≥3 bins hold ≥2 instances each', '`UNCLASSIFIED` ≤ 2',
                   '`UNCLASSIFIED` ≥ 5', 'a single bin holds ≥ 8'):
        if needle not in prereg:
            bad.append(('-', f"the pre-registration no longer contains {needle!r} -- "
                             f"thresholds were edited after the fact"))

    c = Counter(r['bin'] for r in rows)
    unc = c['UNCLASSIFIED']
    n_ge2 = sum(1 for b in BINS if b != 'UNCLASSIFIED' and c[b] >= 2)
    top = max((c[b] for b in BINS if b != 'UNCLASSIFIED'), default=0)

    if n_ge2 >= 3 and unc <= 2:
        verdict = W_A
    elif unc >= 5 or all(c[b] < 2 for b in BINS if b != 'UNCLASSIFIED'):
        verdict = W_B
    elif top >= 8:
        verdict = W_C
    else:
        verdict = 'AMBIGUOUS'

    found = Counter(r['found_by'] for r in rows)
    out = {'n_defects': len(rows), 'git_available': have_git,
           'n_ancestry_unverified': len(unver),
           'bins': dict(c), 'unclassified': unc,
           'n_bins_with_ge2': n_ge2, 'largest_bin': top, 'verdict': verdict,
           'found_by': dict(found), 'invalid_rows': bad}

    if args.json:
        print(json.dumps(out, indent=2))
        return 1 if bad else 0

    if not have_git:
        print(f"  {len(rows)} defects. ANCESTRY CHECK UNVERIFIED on all {len(unver)} rows: this is "
              f"not a git work tree\n  (a ZIP download or `git archive` tarball). That is a "
              f"statement about the ENVIRONMENT, not about the rows --\n  UNVERIFIED is not "
              f"OVERTURNED, and it does not fail the build. Clone the repository to check them.")
    elif bad:
        print(f"  {len(rows)} defects, {len(bad)} INVALID")
    else:
        print(f"  {len(rows)} defects, every one confirmed reachable from HEAD"
              + (f" ({len(unver)} UNVERIFIED)" if unver else ""))
    for i, why in bad:
        print(f"    INVALID {i}: {why}")
    print()
    for b in BINS:
        bar = '#' * c[b]
        print(f"    {b:<14}{c[b]:>3}  {bar}")
    print(f"\n  bins with >=2: {n_ge2}   largest bin: {top}   UNCLASSIFIED: {unc}")
    print(f"  pre-registered thresholds: {W_A} needs >=3 bins with >=2 AND unclassified <=2; "
          f"{W_B} needs unclassified >=5 or no bin >=2; {W_C} needs a bin >=8")
    print(f"  -> {verdict}")
    print(f"\n  found by: " + '  '.join(f"{k} {v}" for k, v in found.most_common()))
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
