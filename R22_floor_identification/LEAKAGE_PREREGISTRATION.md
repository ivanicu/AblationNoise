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

---

# Amendment 1 — the outcome, and the second leaked head was undetectable

Appended 2026-07-29. **No threshold above was changed.**

## Both chained controls pass, and the second one passes exactly

```
CONTROL 1  the replay contains L16H3                                        PASS
CONTROL 2  substituting R10's per-head values for the recovered draw list
           gives sd = 0.22088667589755384 against a stored 0.22088667589755384
           abs err  0.000e+00                                               PASS
```

**Bit-identical.** The replay recovered the exact `30` heads, and `R10`'s exhaustive per-head values
**are** `R1`'s per-draw values — the same measurements, reached by two different code paths on two
different days. That validates the replay and the substitution in one step, which is what the
chaining was for.

## `k_leak = 2`, and `World A` is dead

```
the eight                L16H03 L17H00 L17H07 L17H11 L18H09 L19H00 L19H05 L22H07
in the reference draws   L16H03, L19H00
expected under the design                    1.3119
the 30 draws cover                           26 distinct heads of 168
```

**Two of the eight are inside their own reference, and the design predicted `1.31`.** `L16H3` was
never an accident.

> **And `L19H00` was undetectable.** Its effect is `0.0154` — nowhere near the extremes — so it is
> neither the `min` nor the `max`, and those are the only order statistics the artifact stores.
> **`D176`'s detection method has a ceiling of exactly one head**, and the repository could not have
> learned about the second by any inspection of what it published. `World S` is confirmed: the
> contamination was not merely unnoticed, it was **unknowable from the artifact.**

## Registered verdict: `CONTAMINATION-MATERIAL` — and the confound control deflates it

```
floor                0.4417733517951077  ->  leave-all-eight-out 0.413088   (28 draws kept)
shift                6.4933%   against the 5.667495896844854% margin that decides the count
n_inside             7  ->  7            unchanged
matched-rank null    median 2.3010%   p95 13.1339%   observed at percentile 0.7710
```

The shift clears the registered threshold, so the rule fires. **But the confound registered before
the run is what the number has to be read against**, and it says the shift is *inside* its own null:
removing any eight rank-matched heads from `30` draws moves the floor by `2.30%` at the median and up
to `13.13%` at `p95`, and the observed `6.49%` sits at the `77`th percentile.

> **So the shift is the price of removing eight of thirty draws, not a fact about these eight.**
> The registered verdict stands as written; the honest reading of it does not support *"the floor was
> `6.5%` too high because of the tested heads"*. **`n_inside` is `7` either way** and nothing
> published flips.

## What survives, at the size it supports

**The number does not move the conclusion. The design flaw does not need it to.**

- The reference for judging `k` heads is drawn **from the population containing them**, with nothing
  excluding them (`R1_noise_floor/run.py:246`).
- `2` of `8` were in it, against `1.3119` expected — **the modal outcome, not a mishap.**
- **Only one of the two could ever have been detected** from the published artifact, because only
  `min` and `max` are stored.
- `resolution_limit()` already states the leave-one-out rule for the per-head test and it was never
  applied here.

**The repair is not leave-one-out on whichever head happened to be extreme.** It is that a reference
must be drawn from a pool that excludes what it judges, and that a stored `n / mean / sd / min / max`
cannot support any later audit of who was in it.

## Boundary

One model, one vocabulary, one metric, `8` heads, `30` draws. The replay recovers head *identities*;
every effect value is `R10`'s, admitted by control 2 at `abs err 0.000e+00`. The matched-rank null
jitters each rank by `+-5` and draws `2000` times; a different matching rule would give a different
percentile. Nothing here re-runs the model, and nothing here proposes a replacement floor —
`0.413088` is a leave-out computation on a contaminated design, not a corrected measurement.
