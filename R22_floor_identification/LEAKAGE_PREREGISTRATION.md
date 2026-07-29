# Pre-registration — the reference draws are RECOVERABLE, and the leakage is structural rather than a single accident

Written 2026-07-29, **before the seed was replayed**, committed alone so git ordering rather than my
word establishes that the thresholds preceded the numbers.

## What the object says

`R1_noise_floor/run.py:246,254`:

```python
band_pool = [(L, h) for L in range(lo, hi + 1) for h in range(NH)]
for i in range(N_DRAWS):
    conds[f'band_k{k}_d{i:02d}'] = rng.sample(band_pool, k)
```

**The reference pool is the whole band, including all eight heads the floor is used to judge.**
Nothing excludes them. `D176` found `L16H3` inside its own reference by noticing that the stored
`min` matched its effect to `1.589e-07` — but `min` is the *only* order statistic stored, so **the
other seven are invisible by construction.** That was one detection, not one occurrence.

Under this design, `30` draws with replacement from `168` heads put an expected
`8 x (1 - (167/168)^30) = 1.31` of the eight inside their own reference. **`L16H3` is not an
accident; it is the modal outcome.**

## And the draws are recoverable

`rng = random.Random(DRAW_SEED)` with `DRAW_SEED = 20260727`, a deterministic pool order, and a fixed
sweep. **Replaying the seed recovers exactly which heads were drawn** — the identities were never
lost, only the effect values.

## The two worlds

| | |
|---|---|
| **World A — one accident** | `L16H3` got in by chance; the other seven did not. Leave-one-out fixes it and the reference is otherwise sound. |
| **World S — structural** | the reference is drawn *from the population being tested*, so a floor built this way is contaminated whenever any tested head is drawn, and the repository has **no artifact that could ever have told it which**. Then the repair is not leave-one-out on a head that happened to be the minimum — it is that this reference construction cannot judge these heads at all. |

## Positive controls, chained, and both exact

1. **The replay must place `L16H3` among the `30` `k=1` band draws.** The stored `min` matches its
   effect to `1.589e-07`, so if the replayed list does not contain it, the replay is wrong and
   nothing below is readable.
2. **The substitution must reproduce the stored `sd`.** `R10`'s exhaustive per-head values are the
   same model, the same band, the same original room vocabulary and the same `n_items = 120`.
   Substituting them for the recovered draw list must reproduce
   `sd = 0.22088667589755384`. **If it does, the replay and the substitution are validated at
   once**; if it does not, the substitution is invalid and the leave-out floor cannot be computed —
   `UNVERIFIED`, not an estimate.

## Registered thresholds

Population: the `8` heads `E132b` measured, `qwen2.5-1.5b`, original vocabulary, `n = 120`.

| verdict | rule |
|---|---|
| **CONTAMINATION-MATERIAL** | the leave-all-eight-out floor differs from `0.4417733517951077` by `>= 5.667495896844854 %` — the margin that decides the count — **or** `n_inside` changes |
| **CONTAMINATION-IMMATERIAL** | both below that and unchanged |
| **UNVERIFIED** | either positive control fails |

Reported regardless: **`k_leak`**, how many of the eight the replay actually places in the reference.

## The strongest confound, written before the run

**Removing the eight removes `L16H3`, the largest `|effect|` in the band, so the floor MUST shrink.**
That is selection, not contamination — the eight were chosen because they were *expected to be
causal*, and any set chosen that way will contain unusual values.

**Control, in the same iteration:** `2000` random removals of `8` band heads **matched on the
`|centred effect|` rank distribution of the real eight**, giving the null distribution of the floor
shift. The observed shift is quoted as a percentile of it. **A shift inside that null is the price of
removing eight heads, not evidence about these eight.**

**Second confound: the substitution is a bundle.** `R10`'s values come from its own run. Control 2 is
what makes the substitution admissible at all, and if it passes to `1e-6` the two runs agree on this
population; if it passes only loosely, the leave-out floor is an estimate and is labelled one.

## What each outcome costs me

**`CONTAMINATION-MATERIAL`** means `0.4417733517951077` was never the right floor and every
`frac_of_floor` in `r1_prior_effects()` is against a contaminated threshold — and, worse, that the
contamination was **unknowable from the artifact** rather than merely unnoticed.

**`CONTAMINATION-IMMATERIAL`** would be the comfortable outcome and is therefore the one to
distrust: it would still leave `World S` standing as a design fact, with the damage happening to be
small on this particular draw.

## Boundary

One model, one vocabulary, one metric, `8` heads. The replay recovers head *identities*, not effect
values; every effect value used below is `R10`'s, admitted only by control 2. Nothing here re-runs
the model, and nothing here says which floor should replace the published one.
