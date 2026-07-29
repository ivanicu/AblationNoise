#!/usr/bin/env python3
"""P7 attack on the D169 fix: a gate that can only FAIL is not a gate.

Putting `ok_id` back into analyze.py's gate makes this round UNVERIFIED -- correct, and registered.
But a check that returns UNVERIFIED whatever the data is worth exactly as much as one that returns
PASS whatever the data. Both branches must be reachable, and the only honest way to know is to feed
the gate a world where control 1 passes and watch it return a verdict.

Vector 1  the real result                          -> must print UNVERIFIED
Vector 2  a copy whose total_r10 is replaced by     -> must print a VERDICT WORD, not UNVERIFIED
          total_measured_here, so control 1 passes     (this is the branch the fix could have killed)
Vector 3  vector 2 with the last-layer control       -> must print UNVERIFIED again, proving the
          broken as well                                other gates still bite
"""
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROUND = HERE.parent
REPO = ROUND.parent
PY = sys.executable
RES = ROUND / 'results' / 'r21_indirect_qwen2.5-1.5b.json'
BAK = ROUND / 'results' / '.r21_attack_backup.json'


def run():
    r = subprocess.run([PY, str(ROUND / 'analyze.py')], cwd=str(REPO),
                       capture_output=True, text=True)
    return r.stdout + r.stderr, r.returncode


def main():
    shutil.copy(RES, BAK)
    try:
        out1, rc1 = run()
        v1 = 'UNVERIFIED' in out1
        print(f'  [1] real result                    rc {rc1}  UNVERIFIED printed: {v1}  '
              f'-> {"PASS" if v1 else "FAIL"}')

        d = json.load(open(BAK))
        for k, c in d['cells'].items():
            c['total_r10'] = c['total_measured_here']          # control 1 now passes exactly
        json.dump(d, open(RES, 'w'))
        out2, rc2 = run()
        got_verdict = any(w in out2 for w in ('MIXED', 'ATTENTION-DOMINATED', 'MLP-DOMINATED',
                                              'RENORM-DOMINATED', 'EMB-DOMINATED'))
        v2 = got_verdict and 'REGISTERED VERDICT: UNVERIFIED' not in out2
        print(f'  [2] control 1 made to PASS         rc {rc2}  verdict word printed: {got_verdict}  '
              f'-> {"PASS" if v2 else "FAIL -- the gate can only fail"}')

        for k, c in d['cells'].items():
            if k.startswith('L27'):
                c['att'] = 1.0                                  # break the last-layer control
        json.dump(d, open(RES, 'w'))
        out3, rc3 = run()
        v3 = 'UNVERIFIED' in out3
        print(f'  [3] and last-layer control broken  rc {rc3}  UNVERIFIED printed: {v3}  '
              f'-> {"PASS" if v3 else "FAIL -- the other gates do not bite"}')

        ok = v1 and v2 and v3
        print(f'\n  BOTH BRANCHES REACHABLE: {"CONFIRMED" if ok else "UNVERIFIED"}')
        return 0 if ok else 3
    finally:
        shutil.move(BAK, RES)
        subprocess.run([PY, str(ROUND / 'analyze.py')], cwd=str(REPO), capture_output=True)


if __name__ == '__main__':
    sys.exit(main())
