<!-- unbacked-ok: 1.296e-07 1.038e-07 -- the P7 attack harness's own output. attacks/plant_missing_component.py loads a MODEL, so it cannot join the dependency-free reference set (detectors/prose_numbers.py:generator_numbers states that constraint); same exemption class as hook_identity's residuals in METHODS.md. The script is checked in and the exact command is in its docstring, so the numbers are reproducible by anyone with the weights -- they are unbacked because the checker is deliberately CPU-only, not because nothing produced them. -->
# Archived, not deleted — two smoke runs whose runner version was never committed

`SMOKE_smoke.json` was produced by the **un-optimised** `components()`, which computed `336` small
matmuls per item per condition. `SMOKE2_smoke2.json` was produced by the vectorised replacement
(`dirv @ W_O` once per item, reused across all conditions).

**Their only job was to prove the optimisation changed no number, and it is discharged:**

```
max |unoptimised - optimised| over own/att/mlp/emb/norm/total_measured_here   1.296e-07
the additivity identity still holds on the optimised run                      1.038e-07
```

The un-optimised `run.py` was never committed — the vectorisation replaced it in the working tree
before the first commit of this round — so `validate_provenance.py` correctly returns `IMPOSSIBLE`
for `SMOKE_smoke.json`: its stamp `c3c929b9` matches no version of the runner in git history. **That
verdict is right, and the files are moved here rather than removed** so the comparison above remains
checkable by anyone who reconstructs the earlier function from this file's docstring.
