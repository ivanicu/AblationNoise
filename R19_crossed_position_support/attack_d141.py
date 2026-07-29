"""P7 on the D141 fix: a guard that has not been attacked has not been tested. The old guards never
fired, which is exactly why they survived -- so the fix must be shown to fire."""
import subprocess, sys, os, tempfile, shutil
BASE = '/home/ivan/AblationNoise'
PY = '/home/ivan/research/causal-publication-protocol/env/bin/python3'
RES = BASE + '/R19_crossed_position_support/results/r19_crossed_qwen2.5-1.5b.json'

print('=== 1. BASELINE: the analysis runs and reads the hypotheses ===')
r = subprocess.run([PY, BASE + '/R19_crossed_position_support/analyze.py', RES],
                   capture_output=True, text=True, cwd=BASE)
print('   rc=%d   H-support line present: %s' % (r.returncode, 'H-support' in r.stdout))
assert r.returncode == 0 and 'H-support' in r.stdout

print('=== 2. ATTACK: make `import headline` fail, so `eight` is empty ===')
tmp = tempfile.mkdtemp(prefix='d141_')
shutil.copytree(BASE, tmp + '/repo', symlinks=True,
                ignore=shutil.ignore_patterns('.git', '__pycache__', 'env'))
os.replace(tmp + '/repo/headline.py', tmp + '/repo/headline.py.hidden')
r2 = subprocess.run([PY, tmp + '/repo/R19_crossed_position_support/analyze.py',
                     tmp + '/repo/R19_crossed_position_support/results/r19_crossed_qwen2.5-1.5b.json'],
                    capture_output=True, text=True, cwd=tmp + '/repo')
refused = 'REFUSED_NO_PUBLISHED_SET' in r2.stdout
print('   rc=%d   REFUSED_NO_PUBLISHED_SET printed: %s' % (r2.returncode, refused))
print('   H-support verdict still printed as a PASS/FAIL: %s'
      % ('H-support' in r2.stdout.split('REFUSED_NO_PUBLISHED_SET')[-1] if refused else 'n/a'))
assert refused and r2.returncode == 3, \
    'THE GUARD DID NOT FIRE -- a missing dependency still produced a verdict'

print('=== 3. the OLD behaviour, reproduced on the same crippled tree, for contrast ===')
old = open(tmp + '/repo/R19_crossed_position_support/analyze.py').read()
old = old.replace("""        if not eight:
            print('     -> REFUSED_NO_PUBLISHED_SET""", """        if False:
            print('     -> REFUSED_NO_PUBLISHED_SET""", 1)
old = old.replace('and agree == 8\n', 'and (agree == 8 or not eight)\n', 1)
open(tmp + '/repo/R19_crossed_position_support/analyze.py', 'w').write(old)
r3 = subprocess.run([PY, tmp + '/repo/R19_crossed_position_support/analyze.py',
                     tmp + '/repo/R19_crossed_position_support/results/r19_crossed_qwen2.5-1.5b.json'],
                    capture_output=True, text=True, cwd=tmp + '/repo')
print('   rc=%d   old code emits an H-support verdict with NO published set: %s'
      % (r3.returncode, 'H-support' in r3.stdout))
old_ruled = ('H-support' in r3.stdout) and r3.returncode == 0
shutil.rmtree(tmp, ignore_errors=True)
print()
print('VECTOR 2 (the fix fires):            PASS -- rc 3, REFUSED_NO_PUBLISHED_SET printed')
print('VECTOR 3 (the old code ruled anyway): %s'
      % ('CONFIRMED' if old_ruled else
         'UNVERIFIED -- my reconstruction of the old behaviour returned rc %d and printed no '
         'H-support verdict, so it did not reproduce the old code and the CONTRAST IS NOT '
         'DEMONSTRATED. The first version of this script printed "BOTH DIRECTIONS SHOWN" here '
         'regardless -- a conclusion string saying what its author wanted to hear, which is the '
         'last entry on the overshoot list, printed by the attack harness itself.'
         % r3.returncode))
