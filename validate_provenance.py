#!/usr/bin/env python3
"""Which code produced each result file? Three-valued, because two of the answers are not failures.

THE DEFECT THIS EXISTS FOR was recorded in a sibling project and never carried here: a fix was
announced while the running workers kept executing the pre-edit file, and **nothing in the output
could have shown it**. Its durable repair was to stamp `sha256(source)[:8]` into every row, so
"did that fix actually run" becomes a query instead of a memory.

Audited 2026-07-28: **40 result files, zero provenance**, and by git timestamps **12 of them were
produced by code that has since been edited** — R5's three (before `--dtype` was added), R7's four
and R8's five (before `control_fitness` was wired into the runners). Every one of those edits is,
on inspection, additive rather than behaviour-changing. *On inspection* is the evidence standard
this repository refuses everywhere else.

    CONFIRMED   the file carries a stamp and it matches its runner's current source
    STALE       it carries a stamp that does not match -- the runner has changed since
    UNVERIFIED  it carries no stamp at all. Falls back to git timestamps, which are weaker
                evidence and are reported as such, never as a verdict about the numbers

    python3 validate_provenance.py [--json]
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha8(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:8]


def last_commit_ts(rel: str):
    r = subprocess.run(['git', 'log', '-1', '--format=%ct', '--', rel],
                       cwd=str(HERE), capture_output=True, text=True)
    return int(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else None


def stamp_in_history(rel: str, stamp: str) -> bool:
    """Did ANY committed version of this runner hash to `stamp`?

    THE BLIND SPOT THIS CLOSES, and it is the exact scenario the stamp was invented for. A job that
    has already loaded its source keeps executing the PRE-EDIT file. Edit and commit the runner
    while it runs, and the result it finally writes carries the OLD hash while git says the runner
    has not moved since -- so the IMPOSSIBLE branch convicts a file that is simply honest about
    which code produced it. Caught the first time it happened, on R11's run A: I fixed the runner's
    refusal branches during the ~16 minutes that job was executing.

    Resolving the stamp against HISTORY rather than against HEAD turns that false conviction into
    the true statement: STALE, and here is the commit whose source it matches.
    """
    r = subprocess.run(['git', 'rev-list', '--all', '--', rel],
                       cwd=str(HERE), capture_output=True, text=True)
    for rev in r.stdout.split():
        b = subprocess.run(['git', 'show', f'{rev}:{rel}'],
                           cwd=str(HERE), capture_output=True)
        if b.returncode == 0 and hashlib.sha256(b.stdout).hexdigest()[:8] == stamp:
            return True
    return False


def runner_for(result_path: Path):
    """The runner that owns a result file: the .py in its round whose name matches its prefix."""
    round_dir = result_path.parent
    while round_dir != HERE and round_dir.name != 'results':
        round_dir = round_dir.parent
    round_dir = round_dir.parent
    stem = result_path.stem
    cands = sorted(round_dir.glob('*.py'))
    # diag results are produced by diag_*.py; everything else by run.py
    for c in cands:
        if c.name.startswith('diag_') and 'diag' in stem:
            return c
    for c in cands:
        if c.name == 'run.py':
            return c
    return cands[0] if cands else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    rows = []
    for f in sorted(glob.glob(str(HERE / 'R*/results/**/*.json'), recursive=True)):
        p = Path(f)
        d = json.load(open(p))
        stamp = d.get('code_version') if isinstance(d, dict) else None
        # THE PRODUCER IS READ FROM THE FILE, NOT INFERRED FROM ITS DIRECTORY. Inferring it is
        # how this check convicted three innocent files: hook_identity.py writes into
        # R1_noise_floor/results/, so the directory heuristic compared its stamp against R1's
        # runner and found a mismatch it then called impossible. Location is a label; the
        # producer is the object. Fifth instance today of trusting the first over the second.
        named = d.get('producer') if isinstance(d, dict) else None
        runner = None
        if named:
            # An exact repo-relative path first; a bare basename only as a fallback, and a
            # basename that matches MORE THAN ONE file is a GUESS, however confidently the field
            # was written. Taking cands[0] and reporting guessed=False is how R11's result got
            # convicted against R6's runner: eleven rounds all name their script `run.py`.
            exact = HERE / named
            if exact.exists():
                runner, ambiguous = exact, False
            else:
                cands = sorted(Path(x) for x in
                               glob.glob(str(HERE / '**' / named), recursive=True))
                runner = cands[0] if cands else None
                ambiguous = len(cands) > 1
        else:
            ambiguous = False
        guessed = runner is None or ambiguous
        if runner is None:
            runner = runner_for(p)
        rel_r = str(runner.relative_to(HERE)) if runner else None
        cur = sha8(runner) if runner else None
        if stamp and guessed:
            v = 'UNVERIFIED'
        elif stamp and cur and stamp == cur:
            v = 'CONFIRMED'
        elif stamp:
            v = 'STALE'
        else:
            v = 'UNVERIFIED'
        ts_r = last_commit_ts(rel_r) if rel_r else None
        ts_f = last_commit_ts(str(p.relative_to(HERE)))
        # THREE-VALUED, AND THE FIRST VERSION WAS NOT -- caught the same hour it was written.
        # `bool(ts_r and ts_f and ts_r > ts_f)` returns False both when the runner is NOT newer
        # and when either timestamp is MISSING (an uncommitted file). Those are different facts,
        # and collapsing them let the IMPOSSIBLE branch fire on a result that simply had not been
        # committed yet. Absent evidence read as positive evidence: the third instance today.
        # AND A COMMITTED TIMESTAMP CANNOT SEE AN UNCOMMITTED EDIT. Fourth instance today of
        # absent evidence read as positive: the runner had been modified in the working tree, git
        # log still reported its previous commit, ts_r == ts_f, and IMPOSSIBLE fired on a result
        # that was simply newer than the last commit of a file I had just edited.
        dirty = subprocess.run(['git', 'diff', '--quiet', '--', rel_r],
                               cwd=str(HERE)).returncode != 0 if rel_r else False
        older = (None if (ts_r is None or ts_f is None or dirty)
                 else (ts_r > ts_f))
        # Only asked when it can change a verdict: resolving a stamp against every historical
        # blob of the runner is O(history), and running it on CONFIRMED rows would be waste.
        known = (stamp_in_history(rel_r, stamp)
                 if (v == 'STALE' and rel_r and stamp) else None)
        rows.append({'result': str(p.relative_to(HERE)), 'runner': rel_r, 'verdict': v,
                     'stamp_matches_a_historical_version': known,
                     'stamp': stamp, 'current': cur, 'runner_committed_after_result': older,
                     'runner_dirty': dirty, 'producer_guessed_from_path': guessed})

    n = len(rows)
    c = {k: sum(r['verdict'] == k for r in rows) for k in ('CONFIRMED', 'STALE', 'UNVERIFIED')}
    older = [r for r in rows if r['verdict'] == 'UNVERIFIED'
             and r['runner_committed_after_result'] is True]
    unknown_ts = [r for r in rows if r['runner_committed_after_result'] is None]
    # A stamp that matches nothing AND a result newer than every edit of its runner means the
    # stamp cannot have come from that runner. That is the only case worth failing the build on.
    # IMPOSSIBLE requires KNOWING the runner has not moved. `is False` -- not `not ...` -- so an
    # uncommitted file, whose timestamps are unknown, cannot be convicted.
    # A GUESSED PRODUCER CANNOT CONVICT. If the file did not name its own producer, the
    # comparison is against a script inferred from a directory, and a mismatch says nothing.
    # A STAMP THAT MATCHES SOME COMMITTED VERSION OF THE RUNNER IS NOT IMPOSSIBLE, IT IS STALE.
    # Without this the check convicts exactly the case the stamp exists to reveal: a long-running
    # job executing source that was edited underneath it.
    impossible = [r for r in rows if r['verdict'] == 'STALE'
                  and r['runner_committed_after_result'] is False
                  and not r['producer_guessed_from_path']
                  and r['stamp_matches_a_historical_version'] is not True]

    out = {'n': n, 'counts': c, 'n_unverified_and_older_by_git': len(older),
           'n_timestamps_unknown': len(unknown_ts),
           'impossible': [r['result'] for r in impossible], 'rows': rows}
    if args.json:
        print(json.dumps(out, indent=2))
        return 1 if impossible else 0

    print(f"  {n} result files:  {c['CONFIRMED']} CONFIRMED  {c['STALE']} STALE  "
          f"{c['UNVERIFIED']} UNVERIFIED (no stamp)")
    if c['UNVERIFIED']:
        print(f"  of the unstamped, git timestamps show {len(older)} whose runner was committed "
              f"AFTER them:")
        for r in older:
            print(f"    {r['result']}")
        print(f"  that is weaker evidence than a stamp and it is not a verdict about the numbers "
              f"-- it says the code moved, not that the result is wrong.")
    if unknown_ts:
        print(f"  {len(unknown_ts)} file(s) have no git timestamp on one side (uncommitted): the "
              f"timestamp fallback is UNKNOWN there, not 'not older'.")
    for r in rows:
        if r['verdict'] == 'STALE' and r['stamp_matches_a_historical_version'] is True:
            print(f"  STALE {r['result']}: its stamp {r['stamp']} matches an EARLIER committed "
                  f"version of {r['runner']} -- the runner was edited while the job was running, "
                  f"which is the case the stamp exists to make visible, not a fault")
    for r in impossible:
        print(f"  IMPOSSIBLE {r['result']}: carries stamp {r['stamp']} but its runner has not "
              f"been edited since -- the stamp cannot have come from that runner")
    return 1 if impossible else 0


if __name__ == '__main__':
    raise SystemExit(main())
