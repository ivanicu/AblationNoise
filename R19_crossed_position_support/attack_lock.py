"""P7: a lock never attacked is a lock never tested. FIVE vectors, actually performed, output kept."""
import importlib.util, os, sys, tempfile, subprocess, time
from pathlib import Path
sys.path.insert(0, '/home/ivan/AblationNoise/R19_crossed_position_support')
spec = importlib.util.spec_from_file_location(
    'r19run', '/home/ivan/AblationNoise/R19_crossed_position_support/run.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)          # module-level only; main() is not called

TMP = Path(tempfile.mkdtemp(prefix='locktest_'))
OUT = TMP / 'r19_x.json'
refusals = []
def refuse(verdict, why, **extra):
    refusals.append((verdict, why))
    raise SystemExit('REFUSED: %s' % why)

def try_acquire(out=OUT):
    try:
        return ('ACQUIRED', mod.acquire_lock(out, refuse))
    except SystemExit as e:
        return ('REFUSED', str(e))

print('=== 1. clean acquire, then a SECOND runner with a LIVE owner ===')
st, lk = try_acquire()
print('   first  ->', st, '| lock holds pid', Path(str(OUT) + '.lock').read_text().strip())
st2, msg = try_acquire()
print('   second ->', st2, '|', str(msg)[:96])
assert st2 == 'REFUSED', 'A SECOND RUNNER WAS ALLOWED IN -- the whole point'

print('=== 2. STALE lock: owner pid is dead ===')
Path(str(OUT) + '.lock').write_text('999999\n')       # a pid that cannot exist
st3, lk3 = try_acquire()
print('   ->', st3, '(must be ACQUIRED, or the 11th SIGKILL becomes permanent)')
assert st3 == 'ACQUIRED', 'A STALE LOCK BLOCKED FOREVER'

print('=== 3. GARBAGE content ===')
Path(str(OUT) + '.lock').write_text('not-a-pid\n\x00\xff')
st4, _ = try_acquire()
print('   ->', st4, '(must not crash)')
assert st4 == 'ACQUIRED'

print('=== 4. EMPTY file ===')
Path(str(OUT) + '.lock').write_text('')
st5, _ = try_acquire()
print('   ->', st5, '(must not crash)')
assert st5 == 'ACQUIRED'

print('=== 5. a DIFFERENT --out must NOT be blocked ===')
OTHER = TMP / 'r19_other.json'
st6, _ = try_acquire(OTHER)
print('   ->', st6, '(locks are per-output; a shared lock would serialise unrelated runs)')
assert st6 == 'ACQUIRED'

print('=== 6. the lock survives being read by a different process ===')
Path(str(OUT) + '.lock').write_text('%d\n' % os.getpid())
r = subprocess.run([sys.executable, '-c',
                    'import sys;sys.path.insert(0,"/home/ivan/AblationNoise/R19_crossed_position_support");'
                    'import importlib.util;'
                    's=importlib.util.spec_from_file_location("m","/home/ivan/AblationNoise/R19_crossed_position_support/run.py");'
                    'm=importlib.util.module_from_spec(s);s.loader.exec_module(m);'
                    'def_=None;\n'
                    'def r(v,w,**k):\n raise SystemExit("REFUSED:"+w)\n'
                    'm.acquire_lock(__import__("pathlib").Path("%s"), r)' % OUT],
                   capture_output=True, text=True)
print('   subprocess rc=%d  %s' % (r.returncode, (r.stdout + r.stderr).strip()[:90]))
assert r.returncode != 0, 'A LIVE LOCK DID NOT REFUSE A REAL SECOND PROCESS'

print()
print('ALL SIX VECTORS PASS. refusals recorded: %d' % len(refusals))
for v, w in refusals:
    print('   %s : %s' % (v, w[:80]))
